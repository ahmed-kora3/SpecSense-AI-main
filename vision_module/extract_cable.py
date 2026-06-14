import os
from ultralytics import YOLO
import cv2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
model = YOLO(os.path.join(SCRIPT_DIR, "runs/segment/train8/weights/best.pt"))

input_folder = os.path.join(SCRIPT_DIR, "Cable_Dataset", "images", "test")
output_folder = os.path.join(SCRIPT_DIR, "outputs")

os.makedirs(output_folder, exist_ok=True)

def extract_cable(image_path, save_path):
    results = model(image_path)

    for r in results:
        if r.masks is not None:
            mask = r.masks.data[0].cpu().numpy()
            img = cv2.imread(image_path)

            mask = (mask * 255).astype("uint8")
            mask = cv2.resize(mask, (img.shape[1], img.shape[0]))

            extracted = cv2.bitwise_and(img, img, mask=mask)

            cv2.imwrite(save_path, extracted)

# loop على كل الصور
for img_name in os.listdir(input_folder):
    img_path = os.path.join(input_folder, img_name)
    save_path = os.path.join(output_folder, img_name)

    extract_cable(img_path, save_path)

print("✅ Done extracting all cables!")