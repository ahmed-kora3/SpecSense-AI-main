\# ⚡ AI-Powered Cable Inspection \& Specification System



\## 📌 Project Overview

This project is an automated Computer Vision system designed to inspect electrical cables using Artificial Intelligence. It utilizes \*\*YOLOv8\*\* for object detection and a custom \*\*Python logic engine\*\* to extract real-world physical specifications.



The system not only detects cables but also performs \*\*quantitative analysis\*\* to estimate:

1\.  \*\*Real Diameter (mm)\*\*.

2\.  \*\*Voltage Class\*\*.

3\.  \*\*Insulation \& Sheath Materials\*\*.

4\.  \*\*Operational Condition (Pass/Fail)\*\*.



---



\## 🛠️ Tech Stack

\* \*\*Core AI Engine:\*\* YOLOv8 (Ultralytics)

\* \*\*Language:\*\* Python 3.10+

\* \*\*Image Processing:\*\* OpenCV (cv2)

\* \*\*Framework:\*\* PyTorch



---



\## ⚙️ How It Works (The Logic)



\### 1. Detection Phase

The system uses a custom-trained YOLOv8n model (`best.pt`) to identify cable cross-sections in raw images.



\### 2. Measurement Phase

Once a cable is detected, the system calculates the bounding box width in pixels.

\* \*\*Calibration Factor:\*\* `18.5 pixels = 1 mm` (Estimated for this dataset).

\* \*\*Formula:\*\* Diameter (mm) = Width (pixels) / Calibration Factor



\### 3. Classification Logic (Rule-Based)

Based on the calculated diameter, the system automatically assigns technical specifications using standard cable engineering tables:



| Diameter Range (mm) | Voltage Class | Conductor | Insulation | Sheath |

| :--- | :--- | :--- | :--- | :--- |

| \*\*< 15 mm\*\* | Low Voltage (300/500 V) | Class 1 (Solid) | PVC | PVC (White/Grey) |

| \*\*15 mm - 40 mm\*\* | Low Voltage (0.6/1 kV) | Class 2 (Stranded) | XLPE | PVC (Black) |

| \*\*> 40 mm\*\* | Medium Voltage (11-33 kV) | Class 2 (Compacted) | XLPE + Semi-Con | HDPE / PVC |



---



\## 🚀 Installation \& Usage



\### 1. Prerequisites

Ensure you have Python installed. Then install the required libraries:

```bash


### Quick Start (Windows)

1. **Run the System**: Double-click `run_system.bat`.
   - This script will automatically install dependencies and run the inspection tool.

### Manual Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the inspection:
   ```bash
   python get_specs.py
   ```


