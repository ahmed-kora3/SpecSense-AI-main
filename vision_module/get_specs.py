from ultralytics import YOLO
import cv2
import os
import glob
import numpy as np

# --- System Configuration ---
current_dir = os.path.dirname(os.path.abspath(__file__))

# 🔥 استخدم موديل Segmentation
MODEL_PATH = os.path.join(current_dir, "yolov8m-seg.pt")
model = YOLO(MODEL_PATH)

# Output folder
output_folder = os.path.join(current_dir, "Inspection_Results")
os.makedirs(output_folder, exist_ok=True)

# Images path
images_folder = os.path.join(current_dir, "Cable_Dataset", "images", "train")
image_files = glob.glob(os.path.join(images_folder, "*"))
image_files = [f for f in image_files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

# Calibration (ممكن تعدلها بعدين)
pixels_per_mm = 18.5

if not image_files:
    print("[ERROR] No images found.")
    exit()

# --- ENGINEERING LOGIC ---
def get_cable_datasheet(diameter):
    specs = {}

    if diameter < 15:
        specs["Voltage"] = "Low Voltage (300/500 V)"
        specs["Conductor"] = "Class 1 (Solid Copper)"
        specs["Insulation"] = "PVC"
        specs["Sheath"] = "PVC (Grey/White)"
        specs["Type"] = "Control Cable"

    elif 15 <= diameter < 40:
        specs["Voltage"] = "Low Voltage (0.6/1 kV)"
        specs["Conductor"] = "Stranded Copper"
        specs["Insulation"] = "XLPE"
        specs["Sheath"] = "PVC (Black)"
        specs["Type"] = "Power Cable"

    else:
        specs["Voltage"] = "Medium Voltage (11-33 kV)"
        specs["Conductor"] = "Compacted Copper/Al"
        specs["Insulation"] = "XLPE + Semi-conductive"
        specs["Sheath"] = "HDPE / PVC"
        specs["Type"] = "Heavy Duty Cable"

    return specs

print("\n" + "="*70)
print("🚀 SEGMENTATION-BASED INSPECTION REPORT")
print("="*70 + "\n")

for image_path in image_files:

    results = model(image_path, conf=0.25, verbose=False)
    result = results[0]

    if result.masks is None:
        print(f"[WARNING] No cable detected in {os.path.basename(image_path)}")
        continue

    # --- Extract Mask ---
    mask = result.masks.data[0].cpu().numpy()

    ys, xs = np.where(mask > 0)

    if len(xs) == 0:
        continue

    # 🔥 حساب القطر بطريقة أدق (متوسط عبر عدة صفوف)
    widths = []
    for y in range(ys.min(), ys.max(), 5):
        row = xs[ys == y]
        if len(row) > 0:
            widths.append(row.max() - row.min())

    width_pixels = sum(widths) / len(widths)
    diameter_mm = width_pixels / pixels_per_mm

    # --- Status ---
    if diameter_mm < 5:
        status = "⚠️ FAILED (Cut/Damage)"
    elif diameter_mm > 100:
        status = "⚠️ FAILED (Out of Range)"
    else:
        status = "✅ PASSED"

    # --- Specs ---
    tech_data = get_cable_datasheet(diameter_mm)

    # --- PRINT REPORT ---
    print(f"📄 IMAGE: {os.path.basename(image_path)}")
    print("-"*50)
    print(f"Pixel Width: {width_pixels:.2f}")
    print(f"Diameter: {diameter_mm:.2f} mm")
    print(f"Status: {status}")
    print("-"*50)
    print("Specs:")
    for k, v in tech_data.items():
        print(f" - {k}: {v}")
    print("="*70 + "\n")

    # --- DRAW RESULTS ---
    img = cv2.imread(image_path)

    # Overlay mask (لون أخضر)
    overlay = img.copy()
    overlay[mask > 0] = (0, 255, 0)
    img = cv2.addWeighted(img, 0.7, overlay, 0.3, 0)

    # كتابة النص
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, f"Dia: {diameter_mm:.1f} mm", (20, 40), font, 1, (255,255,255), 2)
    cv2.putText(img, f"{status}", (20, 80), font, 1, (0,255,0), 2)

    output_path = os.path.join(output_folder, f"SEG_{os.path.basename(image_path)}")
    cv2.imwrite(output_path, img)

print("✅ Segmentation Inspection Complete")
print(f"📁 Results saved in: {output_folder}")