"""
SpecSense AI — FastAPI Server
==============================
Exposes all backend.py functions as REST API endpoints.
Matches the openapi.yaml specification exactly.
Run with: uvicorn server:app --reload
"""

import os
import tempfile
import traceback
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

import backend
import db_manager

load_dotenv()


# ──────────────────────────────────────────────
# App Lifecycle
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 SpecSense AI API starting...")
    db_manager.init_db()
    yield
    print("🛑 SpecSense AI API shutting down...")


app = FastAPI(
    title="SpecSense AI API",
    description="Intelligent Cable Inspection & Document Analysis System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Pydantic Models (Request / Response)
# ──────────────────────────────────────────────

class HealthStatus(BaseModel):
    status: str


class ParseProjectRequest(BaseModel):
    description: str


class CalculateFeederRequest(BaseModel):
    total_power_w: float
    system_type: str = "single"  # "single" | "three"
    voltage: float = 220
    distance_m: float = 20


class DesignWiringRequest(BaseModel):
    num_rooms: int
    num_acs: int
    num_lights: int
    num_sockets: int
    has_kitchen: bool
    light_w: float = 20
    socket_w: float = 300
    ac_w: float = 1500
    kitchen_w: float = 3000
    lighting_df: float = 0.8
    socket_df: float = 0.6


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────

async def save_upload(upload: UploadFile) -> str:
    """Save an uploaded file to a temp path and return the path."""
    suffix = f"_{upload.filename}" if upload.filename else ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await upload.read()
        tmp.write(content)
        return tmp.name


def cleanup(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# ──────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────

@app.get("/api/healthz", response_model=HealthStatus, tags=["health"])
def health_check():
    return {"status": "ok"}


# ──────────────────────────────────────────────
# Vision
# ──────────────────────────────────────────────

@app.post("/api/vision/inspect", tags=["vision"])
async def vision_inspect(files: list[UploadFile] = File(...)):
    """
    Analyse cable cross-section images with the YOLOv8-seg model.
    Returns segmentation + diameter + cable specs for each image.
    """
    import cv2
    import base64
    import numpy as np

    results = []
    for upload in files:
        tmp_path = await save_upload(upload)
        try:
            result = backend.run_vision_analysis(tmp_path)

            cables = []
            annotated_image_b64 = None

            if result["success"] and result["processed_image"] is not None:
                # Encode annotated image as base64 PNG for the frontend
                img_rgb = cv2.cvtColor(result["processed_image"], cv2.COLOR_BGR2RGB)
                _, buffer = cv2.imencode(".jpg", img_rgb, [cv2.IMWRITE_JPEG_QUALITY, 90])
                annotated_image_b64 = base64.b64encode(buffer).decode("utf-8")

                for cable in result["data"]:
                    if "Error" not in cable:
                        cables.append({
                            "diameter_mm": cable.get("Diameter (mm)", 0),
                            "status": cable.get("Status", "Unknown"),
                            "voltage_class": cable.get("Voltage Class", "N/A"),
                            "cable_type": cable.get("Cable Type", "N/A"),
                            "details": {k: str(v) for k, v in cable.items()},
                        })

            # حفظ كل كابل في قاعدة البيانات
            for c in cables:
                try:
                    db_manager.save_cable_inspection(
                        filename=upload.filename,
                        diameter_mm=c.get("diameter_mm"),
                        status=c.get("status"),
                        voltage_class=c.get("voltage_class"),
                        cable_type=c.get("cable_type"),
                        details_dict=c.get("details", {}),
                    )
                except Exception:
                    pass  # لا نوقف الـ API إذا فشل الحفظ

            results.append({
                "filename": upload.filename,
                "cables": cables,
                "annotated_image": annotated_image_b64,
                "error": result.get("error"),
            })
        except Exception as e:
            results.append({
                "filename": upload.filename,
                "cables": [],
                "annotated_image": None,
                "error": str(e),
            })
        finally:
            cleanup(tmp_path)

    return {"results": results}


# ──────────────────────────────────────────────
# OCR
# ──────────────────────────────────────────────

@app.post("/api/ocr/analyze", tags=["ocr"])
async def ocr_analyze(files: list[UploadFile] = File(...)):
    """
    Run full OCR pipeline on datasheets: read → extract → correct → validate → keywords.
    """
    results = []
    for upload in files:
        tmp_path = await save_upload(upload)
        try:
            result = backend.run_ocr_analysis(tmp_path)
            # حفظ نتيجة التحليل في قاعدة البيانات
            try:
                db_manager.save_datasheet_analysis(
                    filename=upload.filename,
                    category=result.get("category", ""),
                    extracted_specs=result.get("clean_specs", {}),
                    correction_log=result.get("correction_log", []),
                    validation_results=result.get("validation", {}),
                    keywords=result.get("keywords", {}),
                )
            except Exception:
                pass  # لا نوقف الـ API إذا فشل الحفظ

            results.append({
                "filename": upload.filename,
                "extracted_specs": result.get("clean_specs", {}),
                "correction_log": result.get("correction_log", []),
                "validation": result.get("validation", {}),
                "category": result.get("category", ""),
                "keywords": result.get("keywords", {}),
                "error": result.get("error"),
            })
        except Exception as e:
            results.append({
                "filename": upload.filename,
                "extracted_specs": {},
                "correction_log": [],
                "validation": {},
                "category": "",
                "keywords": {},
                "error": str(e),
            })
        finally:
            cleanup(tmp_path)

    return {"results": results}


# ──────────────────────────────────────────────
# Assistant — Project Description Parser
# ──────────────────────────────────────────────

@app.post("/api/assistant/parse-project", tags=["assistant"])
def parse_project_endpoint(req: ParseProjectRequest):
    """
    Parse a natural-language project description (EN or AR) into structured inputs using Gemini.
    """
    result = backend.parse_project(req.description)
    if not result.get("success", False):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to parse description"))
    return result.get("data", {})


# ──────────────────────────────────────────────
# Assistant — External Feeder Cable
# ──────────────────────────────────────────────

@app.post("/api/assistant/calculate-feeder", tags=["assistant"])
def calculate_feeder(req: CalculateFeederRequest):
    """
    Calculate cable size for an external feeder based on load & distance.
    """
    result = backend.run_cable_selection(
        total_power_w=req.total_power_w,
        voltage=int(req.voltage),
        distance_m=req.distance_m,
        system_type=req.system_type,
        max_voltage_drop_pct=5.0,
    )
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    calc = result["calc"]
    response_data = {
        "total_power_w": calc.get("total_power_w"),
        "current_a": calc.get("current_a"),
        "safe_current_a": calc.get("safe_current_a"),
        "recommended_cable_mm2": calc.get("cable", {}).get("recommended_mm2"),
        "initial_cable_mm2": calc.get("initial_cable", {}).get("recommended_mm2"),
        "voltage_drop_v": calc.get("voltage_drop_v"),
        "voltage_drop_pct": calc.get("voltage_drop_pct"),
        "voltage_drop_status": calc.get("voltage_drop_status"),
        "validation_warnings": calc.get("validation_warnings", []),
        "ai_explanation": result.get("explanation", ""),
        "error": result.get("error"),
    }

    # حفظ حسابات الكابل المغذي في قاعدة البيانات
    try:
        db_manager.save_wiring_project(
            project_type="feeder",
            description=f"Feeder: {req.total_power_w}W / {req.system_type} / {req.voltage}V",
            power_w=req.total_power_w,
            system_type=req.system_type,
            voltage=req.voltage,
            distance_m=req.distance_m,
            recommended_cable=str(response_data.get("recommended_cable_mm2", "")),
            v_drop=calc.get("voltage_drop_pct"),
            circuits_dict=None,
            ai_exp=result.get("explanation", ""),
        )
    except Exception:
        pass  # لا نوقف الـ API إذا فشل الحفظ

    return response_data


# ──────────────────────────────────────────────
# Assistant — Internal Wiring Design
# ──────────────────────────────────────────────

@app.post("/api/assistant/design-wiring", tags=["assistant"])
def design_wiring(req: DesignWiringRequest):
    """
    Design internal apartment circuit layout.
    """
    result = backend.run_internal_wiring_design(
        num_rooms=req.num_rooms,
        num_acs=req.num_acs,
        num_lights=req.num_lights,
        num_sockets=req.num_sockets,
        has_kitchen=req.has_kitchen,
        light_w=int(req.light_w),
        socket_w=int(req.socket_w),
        ac_w=int(req.ac_w),
        kitchen_w=int(req.kitchen_w),
        lighting_df=req.lighting_df,
        socket_df=req.socket_df,
    )
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    wiring = result["wiring_data"]
    response_data = {
        "circuits": wiring.get("circuits", []),
        "summary": wiring.get("summary", {}),
        "ai_explanation": result.get("explanation", ""),
    }

    # حفظ تصميم التمديدات الداخلية في قاعدة البيانات
    try:
        db_manager.save_wiring_project(
            project_type="internal_wiring",
            description=f"Internal Wiring: {req.num_rooms} rooms, {req.num_acs} ACs",
            power_w=wiring.get("summary", {}).get("total_power_w"),
            system_type="single",
            voltage=220,
            distance_m=None,
            recommended_cable=None,
            v_drop=None,
            circuits_dict=wiring,
            ai_exp=result.get("explanation", ""),
        )
    except Exception:
        pass  # لا نوقف الـ API إذا فشل الحفظ

    return response_data


# ──────────────────────────────────────────────
# History & Stats API
# ──────────────────────────────────────────────

@app.get("/api/stats", tags=["history"])
def get_stats():
    """إحصائيات سريعة لعرضها في الـ Dashboard."""
    return db_manager.get_dashboard_stats()


@app.get("/api/history/inspections", tags=["history"])
def history_inspections(limit: int = 20):
    """آخر فحوصات صور الكابلات."""
    rows = db_manager.get_recent_inspections(limit)
    # تحويل datetime لـ string للتوافق مع JSON
    for r in rows:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
    return {"results": rows}


@app.get("/api/history/analyses", tags=["history"])
def history_analyses(limit: int = 20):
    """آخر تحليلات الكتالوجات."""
    rows = db_manager.get_recent_analyses(limit)
    for r in rows:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
    return {"results": rows}


@app.get("/api/history/projects", tags=["history"])
def history_projects(limit: int = 20):
    """آخر مشاريع التصميم والحسابات."""
    rows = db_manager.get_recent_projects(limit)
    for r in rows:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
    return {"results": rows}


# ──────────────────────────────────────────────
# Serve React build (production)
# ──────────────────────────────────────────────

frontend_dist = os.path.join(os.path.dirname(__file__), "artifacts", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
