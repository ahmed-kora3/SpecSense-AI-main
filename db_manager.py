"""
SpecSense AI — Database Manager (PostgreSQL)
=============================================
Handles all database operations: table creation, data insertion, and history queries.
Uses psycopg2 for direct PostgreSQL connection.
"""

import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()


# ──────────────────────────────────────────────
# Connection
# ──────────────────────────────────────────────

def get_db_connection():
    """إنشاء اتصال آمن مع قاعدة بيانات PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "specsense_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except Exception as e:
        print(f"[DATABASE CONNECTION ERROR] Unable to connect: {e}")
        return None


# ──────────────────────────────────────────────
# Table Initialization
# ──────────────────────────────────────────────

def init_db():
    """
    إنشاء جميع الجداول المطلوبة في قاعدة البيانات إذا لم تكن موجودة.
    يتم استدعاؤها مرة واحدة عند تشغيل السيرفر.
    """
    conn = get_db_connection()
    if not conn:
        print("[DATABASE] WARNING: Could not connect to PostgreSQL - running without database.")
        return False

    cur = conn.cursor()
    try:
        # 1. جدول فحص صور الكابلات (Vision Module)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cable_inspections (
                id              SERIAL PRIMARY KEY,
                filename        VARCHAR(255) NOT NULL,
                diameter_mm     DOUBLE PRECISION,
                status          VARCHAR(50),
                voltage_class   VARCHAR(100),
                cable_type      VARCHAR(100),
                details         JSONB DEFAULT '{}',
                created_at      TIMESTAMP DEFAULT NOW()
            );
        """)

        # 2. جدول تحليل الكتالوجات والمستندات (OCR Module)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS datasheet_analyses (
                id                  SERIAL PRIMARY KEY,
                filename            VARCHAR(255) NOT NULL,
                category            VARCHAR(100),
                extracted_specs     JSONB DEFAULT '{}',
                correction_log      JSONB DEFAULT '[]',
                validation_results  JSONB DEFAULT '{}',
                keywords            JSONB DEFAULT '{}',
                created_at          TIMESTAMP DEFAULT NOW()
            );
        """)

        # 3. جدول مشاريع التصميم والحسابات (Assistant Module)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS wiring_projects (
                id                  SERIAL PRIMARY KEY,
                project_type        VARCHAR(50) DEFAULT 'feeder',
                description         TEXT,
                total_power_w       DOUBLE PRECISION,
                system_type         VARCHAR(50),
                voltage             DOUBLE PRECISION,
                distance_m          DOUBLE PRECISION,
                recommended_cable   VARCHAR(50),
                voltage_drop_pct    DOUBLE PRECISION,
                wiring_circuits     JSONB DEFAULT '{}',
                ai_explanation      TEXT,
                created_at          TIMESTAMP DEFAULT NOW()
            );
        """)

        conn.commit()
        print("[DATABASE] OK - All tables created / verified successfully.")
        return True

    except Exception as e:
        conn.rollback()
        print(f"[DATABASE ERROR] Table creation failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()


# ──────────────────────────────────────────────
# INSERT — Vision (Cable Inspections)
# ──────────────────────────────────────────────

def save_cable_inspection(filename, diameter_mm, status, voltage_class, cable_type, details_dict):
    """حفظ نتائج فحص صورة كابل واحد في الـ database"""
    query = """
        INSERT INTO cable_inspections
        (filename, diameter_mm, status, voltage_class, cable_type, details)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
    """
    conn = get_db_connection()
    if not conn:
        return None

    cur = conn.cursor()
    try:
        cur.execute(query, (filename, diameter_mm, status, voltage_class, cable_type, Json(details_dict)))
        idx = cur.fetchone()[0]
        conn.commit()
        print(f"[DATABASE] OK - Vision inspection saved - ID: {idx}")
        return idx
    except Exception as e:
        conn.rollback()
        print(f"[DATABASE ERROR] Vision save failed: {e}")
        return None
    finally:
        cur.close()
        conn.close()


# ──────────────────────────────────────────────
# INSERT — OCR (Datasheet Analyses)
# ──────────────────────────────────────────────

def save_datasheet_analysis(filename, category, extracted_specs, correction_log, validation_results, keywords):
    """حفظ نتائج تحليل كتالوج أو مستند في الـ database"""
    query = """
        INSERT INTO datasheet_analyses
        (filename, category, extracted_specs, correction_log, validation_results, keywords)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
    """
    conn = get_db_connection()
    if not conn:
        return None

    cur = conn.cursor()
    try:
        cur.execute(query, (
            filename, category,
            Json(extracted_specs), Json(correction_log),
            Json(validation_results), Json(keywords)
        ))
        idx = cur.fetchone()[0]
        conn.commit()
        print(f"[DATABASE] OK - Datasheet analysis saved - ID: {idx}")
        return idx
    except Exception as e:
        conn.rollback()
        print(f"[DATABASE ERROR] OCR save failed: {e}")
        return None
    finally:
        cur.close()
        conn.close()


# ──────────────────────────────────────────────
# INSERT — Assistant (Wiring Projects)
# ──────────────────────────────────────────────

def save_wiring_project(project_type, description, power_w, system_type, voltage,
                        distance_m, recommended_cable, v_drop, circuits_dict, ai_exp):
    """حفظ حسابات المساعد الهندسي (feeder أو internal wiring) في الـ database"""
    query = """
        INSERT INTO wiring_projects
        (project_type, description, total_power_w, system_type, voltage,
         distance_m, recommended_cable, voltage_drop_pct, wiring_circuits, ai_explanation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
    """
    conn = get_db_connection()
    if not conn:
        return None

    cur = conn.cursor()
    try:
        cur.execute(query, (
            project_type, description, power_w, system_type, voltage,
            distance_m, recommended_cable, v_drop,
            Json(circuits_dict) if circuits_dict else Json({}),
            ai_exp
        ))
        idx = cur.fetchone()[0]
        conn.commit()
        print(f"[DATABASE] OK - Wiring project saved - ID: {idx}")
        return idx
    except Exception as e:
        conn.rollback()
        print(f"[DATABASE ERROR] Project save failed: {e}")
        return None
    finally:
        cur.close()
        conn.close()


# ──────────────────────────────────────────────
# SELECT — History Queries
# ──────────────────────────────────────────────

def get_recent_inspections(limit=20):
    """جلب آخر فحوصات الصور من الـ database"""
    conn = get_db_connection()
    if not conn:
        return []
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT * FROM cable_inspections ORDER BY created_at DESC LIMIT %s;",
            (limit,)
        )
        return cur.fetchall()
    except Exception as e:
        print(f"[DATABASE ERROR] Fetch inspections failed: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_recent_analyses(limit=20):
    """جلب آخر تحليلات الكتالوجات من الـ database"""
    conn = get_db_connection()
    if not conn:
        return []
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT * FROM datasheet_analyses ORDER BY created_at DESC LIMIT %s;",
            (limit,)
        )
        return cur.fetchall()
    except Exception as e:
        print(f"[DATABASE ERROR] Fetch analyses failed: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_recent_projects(limit=20):
    """جلب آخر مشاريع التصميم والحسابات من الـ database"""
    conn = get_db_connection()
    if not conn:
        return []
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT * FROM wiring_projects ORDER BY created_at DESC LIMIT %s;",
            (limit,)
        )
        return cur.fetchall()
    except Exception as e:
        print(f"[DATABASE ERROR] Fetch projects failed: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_dashboard_stats():
    """جلب إحصائيات سريعة لعرضها في الـ Dashboard"""
    conn = get_db_connection()
    if not conn:
        return {"total_inspections": 0, "total_analyses": 0, "total_projects": 0}
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM cable_inspections;")
        inspections = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM datasheet_analyses;")
        analyses = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM wiring_projects;")
        projects = cur.fetchone()[0]

        return {
            "total_inspections": inspections,
            "total_analyses": analyses,
            "total_projects": projects,
        }
    except Exception as e:
        print(f"[DATABASE ERROR] Stats query failed: {e}")
        return {"total_inspections": 0, "total_analyses": 0, "total_projects": 0}
    finally:
        cur.close()
        conn.close()