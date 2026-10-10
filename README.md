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

## 🎨 Frontend Architecture & Integration Details

### 1. Frontend Technologies & Component Structure
The frontend UI is built as a single-page application (SPA) in `artifacts/frontend/`:

- **React 19 + TypeScript:** Strongly-typed component architecture ensuring type safety across API interactions.
- **Vite 7:** High-speed development server with Instant Hot Module Replacement (HMR) and optimized build bundling.
- **[Wouter](artifacts/frontend/src/App.tsx):** Minimalist client-side router managing application routes (`/dashboard`, `/vision`, `/ocr`, `/assistant`).
- **[TanStack Query (React Query v5)](artifacts/frontend/src/pages/VisionPage.tsx):** Asynchronous state management handling server data fetching (`useQuery`) and mutation workflows (`useMutation`).
- **Custom Glassmorphism CSS System (`src/index.css`):** Bespoke dark-mode UI design system featuring micro-animations, glassmorphism cards, and responsive layouts.

### 2. Application Pages & Functions (`src/pages/`)
- **[DashboardPage.tsx](artifacts/frontend/src/pages/DashboardPage.tsx):** Real-time analytics dashboard rendering inspection metrics, OCR statistics, and recent project logs fetched from `/api/stats` and `/api/history/*`.
- **[VisionPage.tsx](artifacts/frontend/src/pages/VisionPage.tsx):** Drag-and-drop image upload interface sending `multipart/form-data` to `/api/vision/inspect`. Renders YOLOv8 segmentation overlays inline via Base64 along with quality control pass/fail badges.
- **[OcrPage.tsx](artifacts/frontend/src/pages/OcrPage.tsx):** Document analyzer uploading PDF/images to `/api/ocr/analyze`. Renders extracted technical specifications, typo correction logs, engineering validation warnings, and keyword badges.
- **[AssistantPage.tsx](artifacts/frontend/src/pages/AssistantPage.tsx):** Three-in-one engineering suite:
  1. *Gemini AI Natural Language Parser:* Converts plain text (Arabic/English) into structured electrical parameters.
  2. *Feeder Cable Sizing Calculator:* Computes current load ($I$), voltage drop ($V_{drop}$), and recommended cable gauge ($mm^2$).
  3. *Internal Wiring Designer:* Generates complete circuit layout, breaker sizing, and cable requirements for residential & commercial units.

---

### 🔗 Frontend-Backend Integration Pipeline

Integration between the React SPA and the FastAPI backend is designed for seamless operation in both development and production environments:

```
[ React SPA (Vite) ] ── (Port 5173 Dev / Port 8000 Prod) ──► [ FastAPI Server ]
         │                                                           │
         ├── POST /api/vision/inspect ───────► YOLOv8 Segmentation   │
         ├── POST /api/ocr/analyze ──────────► EasyOCR + SpaCy       │
         ├── POST /api/assistant/parse-project ► Gemini AI API       │
         └── GET  /api/stats ────────────────► PostgreSQL / Memory    │
```

#### 1️⃣ Development Environment (Vite Proxy + CORS)
- **Frontend Server:** Runs on `http://localhost:5173`.
- **Backend API:** Runs on `http://127.0.0.1:8000`.
- **Vite Proxy Configuration (`vite.config.ts`):** Requests starting with `/api` are automatically proxied to the backend target:
  ```typescript
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  }
  ```
- **FastAPI CORS Middleware (`server.py`):** Configured with `CORSMiddleware` to explicitly allow requests originating from `http://localhost:5173`.

#### 2️⃣ Production Environment (Single-Server Hosting)
- Executing `pnpm build` compiles the React application into optimized static assets in `artifacts/frontend/dist`.
- **FastAPI Static File Mounting (`server.py`):** The backend dynamically mounts the compiled frontend directory at root `/`:
  ```python
  frontend_dist = os.path.join(os.path.dirname(__file__), "artifacts", "frontend", "dist")
  if os.path.exists(frontend_dist):
      app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
  ```
- *Result:* In production, FastAPI serves both the React SPA and the REST API endpoints synchronously from a single port (`8000`).

#### 3️⃣ Data Exchange Protocol
- **File Uploads:** Uploaded documents and images are transmitted via `multipart/form-data` using `FormData`.
- **Inline Image Rendering:** YOLO output images are encoded as **Base64 strings** inside the JSON response and directly rendered by React via `<img src="data:image/jpeg;base64,..." />`, eliminating temporary server image files.
- **Structured JSON Payloads:** All request/response bodies are validated against Pydantic models (`HealthStatus`, `ParseProjectRequest`, `CalculateFeederRequest`, `DesignWiringRequest`).

---

## ✨ Key Features Summary

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
