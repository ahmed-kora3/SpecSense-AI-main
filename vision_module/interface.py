import cv2
import numpy as np  # Required for robust image loading
import os
from ultralytics import YOLO

# ==========================================
# ⚙️ CONFIGURATION & SETTINGS
# ==========================================
# Calibration Factor: Number of pixels representing 1 millimeter.
# Calibrated based on reference object (Adjust if camera height changes).
PIXELS_PER_MM = 18.5 

# AI Confidence Threshold: Minimum score (0-1) to accept a detection.
# Set EXTREMELY low (0.01) because the current model is very weak/undertrained.
CONF_THRESHOLD = 0.01

# ==========================================
# 🧠 MODEL LOADER
# ==========================================
# Prefer the segmentation-trained model when available.
current_dir = os.path.dirname(os.path.abspath(__file__))
seg_model_path = os.path.join(current_dir, "runs", "segment", "train8", "weights", "best.pt")
legacy_seg_model = os.path.join(current_dir, "yolov8m-seg.pt")
if os.path.exists(seg_model_path):
    model_path = seg_model_path
elif os.path.exists(legacy_seg_model):
    model_path = legacy_seg_model
else:
    model_path = os.path.join(current_dir, "best.pt")

def analyze_cable_image(image_path):
    """
    Analyzes a cable cross-section image using YOLOv8 AI model.
    Measures diameter and classifies quality.

    Args:
        image_path (str): Full path to the input image.

    Returns:
        tuple: (processed_image_array, results_list_of_dicts)
    """
    
    # 1. Load the AI Model
    try:
        model = YOLO(model_path)
    except Exception as e:
        return None, [{"Error": f"Model failed to load. Check '{model_path}'. Error: {e}"}]

    # 2. Read Image (ROBUST METHOD)
    # Standard cv2.imread fails with non-English paths/spaces on Windows.
    # We use numpy to read raw bytes, then decode them.
    try:
        # Read file as byte stream
        img_stream = np.fromfile(image_path, dtype=np.uint8)
        # Decode image
        img = cv2.imdecode(img_stream, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Image decoding failed (Result is None).")
            
    except Exception as e:
        return None, [{"Error": f"Failed to read image. File might be corrupt or path invalid. Details: {e}"}]

    # 3. Run AI Inference
    # verbose=False suppresses terminal noise
    results = model(img, conf=CONF_THRESHOLD, verbose=False)
    
    output_data = []
    result = results[0]

    final_detection = None

    # 4. Prefer segmentation masks when available
    if result.masks is not None and len(result.masks.data) > 0:
        best_area = 0
        best_mask = None
        best_diameter = 0.0
        best_width = 0.0

        for mask_tensor in result.masks.data:
            mask = mask_tensor.cpu().numpy().astype("uint8")
            if mask.shape != img.shape[:2]:
                mask = cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)

            ys, xs = np.where(mask > 0)
            if len(xs) == 0:
                continue

            widths = []
            for y in range(ys.min(), ys.max() + 1, 5):
                row = xs[ys == y]
                if len(row) > 0:
                    widths.append(row.max() - row.min())

            if not widths:
                continue

            width_px = sum(widths) / len(widths)
            diameter_mm = width_px / PIXELS_PER_MM
            area = int(mask.sum())

            if area > best_area:
                best_area = area
                best_mask = mask
                best_diameter = diameter_mm
                best_width = width_px

        if best_mask is not None:
            final_detection = {
                "mask": best_mask,
                "width_px": best_width,
                "diameter_mm": best_diameter,
                "area": best_area,
            }

    # 5. Fallback to detection boxes if segmentation data is unavailable
    if final_detection is None and result.boxes:
        all_detections = []
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            width_px = x2 - x1
            area = width_px * (y2 - y1)
            diameter_mm = width_px / PIXELS_PER_MM
            all_detections.append({
                "box": (x1, y1, x2, y2),
                "width_px": width_px,
                "diameter_mm": diameter_mm,
                "area": area,
            })

        if all_detections:
            all_detections.sort(key=lambda x: x['area'], reverse=True)
            final_detection = all_detections[0]

    if final_detection is None:
        return img, output_data

    # --- Estimate specs based on diameter ---
    diameter_mm = final_detection['diameter_mm']
    width_px = final_detection['width_px']

    if diameter_mm >= 40:
        specs = {
            "Voltage Class": "Medium Voltage (11 kV - 33 kV)",
            "Conductor": "Class 2 (Compacted Copper/Al)",
            "Insulation": "XLPE + Semi-conductive Layer",
            "Sheath Mat.": "HDPE / PVC (Red/Black)",
            "Cable Type": "Heavy Duty Power Feeder"
        }
    elif 15 <= diameter_mm < 40:
        specs = {
            "Voltage Class": "Low Voltage (0.6/1 kV)",
            "Conductor": "Class 2 (Stranded Copper)",
            "Insulation": "XLPE (Cross-linked PE)",
            "Sheath Mat.": "PVC (Black/UV Resistant)",
            "Cable Type": "Power Cable (Armoured)"
        }
    else:
        specs = {
            "Voltage Class": "Low Voltage (300/500 V)",
            "Conductor": "Class 1 (Solid Copper)",
            "Insulation": "PVC (Polyvinyl Chloride)",
            "Sheath Mat.": "PVC (Grey/White)",
            "Cable Type": "Control/Light Duty"
        }

    if diameter_mm > 5.0:
        status = "PASS"
        color = (0, 255, 0)
    else:
        status = "FAIL (Too Small)"
        color = (0, 0, 255)

    if 'mask' in final_detection:
        mask = final_detection['mask'].astype('uint8')
        if mask.shape != img.shape[:2]:
            mask = cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            cv2.drawContours(img, contours, -1, color, 2)

        overlay = img.copy()
        overlay[mask > 0] = (0, 255, 0)
        img = cv2.addWeighted(img, 0.85, overlay, 0.15, 0)
    else:
        x1, y1, x2, y2 = final_detection['box']
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)

    label_text = f"Dia: {diameter_mm:.1f} mm"
    (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    cv2.rectangle(img, (20, img.shape[0] - 45), (20 + text_w + 24, img.shape[0] - 10), (0, 0, 0), -1)
    cv2.putText(img, label_text, (25, img.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    output_data.append({
        "Diameter (mm)": round(diameter_mm, 2),
        "Width (px)": round(width_px, 2),
        "Voltage Class": specs["Voltage Class"],
        "Conductor": specs["Conductor"],
        "Insulation": specs["Insulation"],
        "Sheath Mat.": specs["Sheath Mat."],
        "Cable Type": specs["Cable Type"],
        "Status": status
    })

    return img, output_data