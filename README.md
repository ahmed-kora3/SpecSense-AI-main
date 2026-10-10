# SpecSense AI ⚡
> Intelligent Cable Inspection, Technical Datasheet Parsing & Electrical Engineering Assistant System

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-7.3-646CFF.svg)](https://vitejs.dev/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Segmentation-00FFFF.svg)](https://ultralytics.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1.svg)](https://www.postgresql.org/)

---

## 📌 Overview

**SpecSense AI** is a state-of-the-art AI-powered platform designed for the cable manufacturing and electrical engineering industries. It combines **Computer Vision**, **Optical Character Recognition (OCR)**, **Natural Language Processing (NLP)**, and **Generative AI (Google Gemini)** into a unified, high-performance web application.

Key capabilities include:
- 👁️ **Computer Vision Cable Inspection:** YOLOv8 segmentation model for precise cross-section analysis, diameter measurement, and quality assessment.
- 📄 **OCR & Technical Datasheet Analysis:** Automated spec extraction, error correction, standard compliance verification, and smart keyword tagging.
- ⚡ **AI Electrical Engineering Assistant:** Intelligent feeder cable sizing, internal wiring layout design, and natural language project description parsing via Gemini AI.
- 📊 **Analytics Dashboard & History:** PostgreSQL-backed session history and analytics tracking for inspections and design projects.

---

## 🏗️ Architecture & Modules

```
SpecSense-AI/
├── Assistant_Module/        # Electrical calculations & Gemini AI project parser
├── Keyword_Generator/       # Technical keyword extraction & cable classification
├── OCR_Reader/              # OCR processing, spec extraction, & engineering validation
├── vision_module/           # YOLOv8 segmentation model & image processing pipeline
├── artifacts/
│   └── frontend/            # React 19 + TypeScript + Vite + TailwindCSS UI
├── backend.py               # Pure python backend integration pipeline
├── db_manager.py            # PostgreSQL database connection & queries manager
├── server.py                # FastAPI REST API server
└── docker-compose.yml       # PostgreSQL database container configuration
```

---

## ✨ Key Features

### 1. 👁️ Computer Vision Inspection (`vision_module/`)
- Uses custom-trained **YOLOv8-Segmentation** models (`yolov8m-seg.pt`).
- Automatic cable diameter calculation ($mm$).
- Detection of cable structure (Conductor, Insulation, Armouring, Sheath).
- Instant visual annotations and compliance status (Pass / Warning / Fail).

### 2. 📄 OCR & Datasheet Analysis (`OCR_Reader/` & `Keyword_Generator/`)
- Powered by **EasyOCR** & **SpaCy**.
- Supports PDF datasheets, scan images, and Word documents (`.docx`).
- Automated Spec Correction engine (`SpecCorrector`) for OCR typo fixes.
- Engineering Validator checks extracted values against standards.
- Keyword Generation for inventory categorization and search indexing.

### 3. ⚡ Electrical Assistant & AI Design (`Assistant_Module/`)
- **Feeder Cable Sizing:** Computes current load ($I$), voltage drop ($V_{drop}$), and recommended cross-section area ($mm^2$).
- **Internal Wiring Designer:** Automatically layout circuit breakers, cable sizes, and total load demand for apartments and commercial spaces.
- **Gemini AI Natural Language Parser:** Translates plain text project descriptions (Arabic or English) into structured electrical parameters.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** & **PNPM** (`npm i -g pnpm`)
- **Docker** (Optional, for PostgreSQL database)

---

### 1. Environment Configuration

1. Clone the repository:
   ```bash
   git clone https://github.com/ahmed-kora3/SpecSense-AI-main.git
   cd SpecSense-AI-main
   ```

2. Create `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Set your **Gemini API Key** in `.env`:
   ```env
   GEMINI_API_KEY="your_api_key_here"
   DB_HOST=localhost
   DB_NAME=specsense_db
   DB_USER=postgres
   DB_PASSWORD=specsense_password
   DB_PORT=5432
   ```

---

### 2. Database Setup (Optional)

Start PostgreSQL using Docker Compose:
```bash
docker compose up -d
```
> *Note: If PostgreSQL is not running, the application will function normally using graceful fallback mode.*

---

### 3. Running the Backend Server

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Launch FastAPI backend:
   ```bash
   python -m uvicorn server:app --reload --host 127.0.0.1 --port 8000
   ```
   The REST API will be active at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

---

### 4. Running the Frontend UI

1. Install frontend dependencies and start Vite dev server:
   ```bash
   pnpm install
   pnpm --filter @workspace/frontend dev
   ```

2. Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📡 API Endpoints Summary

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/healthz` | `GET` | Health check endpoint |
| `/api/vision/inspect` | `POST` | Upload cable images for YOLO cross-section inspection |
| `/api/ocr/analyze` | `POST` | Upload datasheets (PDF/Image) for full OCR & spec extraction |
| `/api/assistant/parse-project` | `POST` | Parse natural language project text via Gemini AI |
| `/api/assistant/calculate-feeder` | `POST` | Calculate feeder cable size & voltage drop |
| `/api/assistant/design-wiring` | `POST` | Generate internal apartment wiring design |
| `/api/stats` | `GET` | Retrieve dashboard history statistics |

---

## 🛠️ Key Technologies

- **Backend:** FastAPI, Uvicorn, PyTorch, YOLOv8 (Ultralytics), EasyOCR, SpaCy, Google Gemini AI API
- **Frontend:** React 19, TypeScript, Vite, TailwindCSS v4, Framer Motion, TanStack Query, Lucide Icons
- **Database:** PostgreSQL 15, Docker

---

## 📄 License

This project is licensed under the MIT License.
