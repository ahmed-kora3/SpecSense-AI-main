"""
SpecSense AI - Pure Backend Module
===================================
All core logic exposed as clean Python functions.
No UI dependencies. Import from here in any UI framework.
"""

import os
import cv2 
# pyrefly: ignore [missing-import]
import numpy as np
import tempfile
import traceback

# Vision Module
from vision_module.interface import analyze_cable_image

# OCR Module
from OCR_Reader.src.core_ocr import OCREngine
from OCR_Reader.src.extraction import SpecificationExtractor, SpecCorrector
from OCR_Reader.src.validation import CableValidator

# Keyword Module
from Keyword_Generator.keyword_tool import KeywordExtractor, CableClassifier

# Assistant Module
from Assistant_Module.assistant_engine import run_assistant_pipeline
from Assistant_Module.llm_service import explain_cable_selection, explain_internal_wiring
from Assistant_Module.internal_wiring_engine import InternalWiringEngine
from Assistant_Module.project_parser import parse_project_description


# ============================================================
# VISION
# ============================================================

def run_vision_analysis(image_path: str) -> dict:
    """
    Run YOLOv8 cable cross-section analysis on an image file.

    Args:
        image_path: Absolute path to image file.

    Returns:
        {
            "success": bool,
            "processed_image": np.ndarray | None,   # BGR image with annotations
            "data": list[dict],                      # Cable specs / error list
            "error": str | None
        }
    """
    try:
        processed_img, data = analyze_cable_image(image_path)
        return {
            "success": processed_img is not None,
            "processed_image": processed_img,
            "data": data,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "processed_image": None,
            "data": [],
            "error": str(e)
        }


# ============================================================
# OCR / DATASHEET
# ============================================================

def run_ocr_analysis(file_path: str) -> dict:
    """
    Run full OCR pipeline: read → extract → correct → validate → keywords.

    Args:
        file_path: Absolute path to PDF, image, or DOCX file.

    Returns:
        {
            "success": bool,
            "full_text": str,
            "raw_specs": dict,
            "clean_specs": dict,
            "correction_log": list[str],
            "validation": dict,
            "keywords": dict,
            "category": str,
            "error": str | None,
            "traceback": str | None
        }
    """
    try:
        ocr_engine = OCREngine(languages=['en'])
        results = ocr_engine.read_image(file_path, detail=0)
        full_text = " ".join(results)

        extractor = SpecificationExtractor()
        raw_specs = extractor.extract_specs(full_text)

        corrector = SpecCorrector()
        clean_specs, correction_log = corrector.correct_all(raw_specs)

        validator = CableValidator()
        validation_result = validator.validate_cable(clean_specs)

        keywords = KeywordExtractor().extract_keywords(full_text)
        category = CableClassifier().classify(full_text)

        return {
            "success": True,
            "full_text": full_text,
            "raw_specs": raw_specs,
            "clean_specs": clean_specs,
            "correction_log": correction_log,
            "validation": validation_result,
            "keywords": keywords,
            "category": category,
            "error": None,
            "traceback": None
        }
    except Exception as e:
        return {
            "success": False,
            "full_text": "",
            "raw_specs": {},
            "clean_specs": {},
            "correction_log": [],
            "validation": {},
            "keywords": {},
            "category": "",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# ============================================================
# ASSISTANT - EXTERNAL FEEDER CABLE
# ============================================================

def run_cable_selection(
    total_power_w: float,
    voltage: int,
    distance_m: float,
    system_type: str = "single",
    max_voltage_drop_pct: float = 5.0
) -> dict:
    """
    Calculate cable size for an external feeder.

    Args:
        total_power_w:        Total connected load in Watts.
        voltage:              Supply voltage in Volts.
        distance_m:           Cable run length in meters.
        system_type:          "single" or "three".
        max_voltage_drop_pct: Maximum allowable voltage drop %.

    Returns:
        {
            "calc": dict,          # Raw pipeline results
            "explanation": str,    # AI-generated explanation
            "error": str | None
        }
    """
    try:
        appliances = [{'name': 'General Load', 'power': total_power_w, 'quantity': 1}]
        calc = run_assistant_pipeline(
            appliances, voltage, distance_m,
            system_type=system_type,
            max_voltage_drop_pct=max_voltage_drop_pct
        )
        explanation = explain_cable_selection(calc)
        return {"calc": calc, "explanation": explanation, "error": None}
    except Exception as e:
        return {"calc": {}, "explanation": "", "error": str(e)}


# ============================================================
# ASSISTANT - INTERNAL WIRING
# ============================================================

def run_internal_wiring_design(
    num_rooms: int,
    num_acs: int,
    num_lights: int,
    num_sockets: int,
    has_kitchen: bool,
    light_w: int = 20,
    socket_w: int = 300,
    ac_w: int = 1500,
    kitchen_w: int = 3000,
    lighting_df: float = 0.8,
    socket_df: float = 0.6
) -> dict:
    """
    Design internal circuit layout for a building.

    Returns:
        {
            "wiring_data": dict,   # Circuits, summary, cable totals
            "explanation": str,    # AI-generated explanation
            "error": str | None
        }
    """
    try:
        inputs = {
            'num_rooms': num_rooms,
            'num_acs': num_acs,
            'num_lights': num_lights,
            'num_sockets': num_sockets,
            'has_kitchen': has_kitchen
        }
        heuristics = {
            'light_w': light_w,
            'socket_w': socket_w,
            'ac_w': ac_w,
            'kitchen_w': kitchen_w
        }
        diversity = {
            'lighting_df': lighting_df,
            'socket_df': socket_df,
            'ac_df': 0.9,
            'kitchen_df': 0.8
        }
        wiring_data = InternalWiringEngine.design_internal_wiring(inputs, heuristics, diversity)
        explanation = explain_internal_wiring(wiring_data)
        return {"wiring_data": wiring_data, "explanation": explanation, "error": None}
    except Exception as e:
        return {"wiring_data": {}, "explanation": "", "error": str(e)}


# ============================================================
# ASSISTANT - PROJECT DESCRIPTION PARSER
# ============================================================

def parse_project(description: str) -> dict:
    """
    Parse a natural-language project description (EN or AR) into structured inputs.

    Returns:
        {
            "success": bool,
            "data": dict,        # rooms, ac_units, lighting_points, etc.
            "error": str | None
        }
    """
    try:
        result = parse_project_description(description)
        if "error" in result:
            return {"success": False, "data": {}, "error": result["error"]}
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        return {"success": False, "data": {}, "error": str(e)}


# ============================================================
# FULL PIPELINE
# ============================================================

def run_full_pipeline(
    image_paths: list,
    doc_paths: list,
    total_power_w: float = 5000.0,
    voltage: int = 220,
    distance_m: float = 20.0,
    system_type: str = "single"
) -> dict:
    """
    Run Vision → OCR → Assistant sequentially.

    Returns:
        {
            "vision":    list of vision result dicts,
            "ocr":       list of OCR result dicts,
            "assistant": dict with calc + explanation
        }
    """
    vision_results = [run_vision_analysis(p) for p in image_paths]
    ocr_results    = [run_ocr_analysis(p)    for p in doc_paths]
    assistant_result = run_cable_selection(total_power_w, voltage, distance_m, system_type)

    return {
        "vision": vision_results,
        "ocr": ocr_results,
        "assistant": assistant_result
    }
