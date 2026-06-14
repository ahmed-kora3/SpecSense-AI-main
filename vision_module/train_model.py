from ultralytics import YOLO
import torch
from pathlib import Path
import os

# --- Configuration ---
DATA_YAML_PATH = 'data.yaml'
MODEL_SIZE = os.environ.get("YOLO_BASE_MODEL", "yolov8n-seg.pt")
EPOCHS = 150
BATCH_SIZE = 8 
IMG_SIZE = 640

# --- Training Script ---
def _looks_like_segmentation_labels(labels_dir: Path) -> bool:
    """
    YOLO-seg TXT lines look like:
      cls x1 y1 x2 y2 x3 y3 ...
    (more than 5 tokens). Detection-only looks like:
      cls xc yc w h
    """
    if not labels_dir.exists():
        return False

    for txt_file in labels_dir.rglob("*.txt"):
        # Skip accidental non-label files if any exist in labels/.
        if txt_file.name.lower().endswith((".cache.txt",)):
            continue

        try:
            first_line = txt_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        if not first_line:
            continue

        tokens = first_line[0].strip().split()
        if len(tokens) > 5:
            return True

    return False

def train_yolov8():
    """Initializes and trains the YOLOv8 segmentation model."""
    
    # Check for GPU availability
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"--- Starting Training on Device: {device.upper()} ---")

    try:
        labels_dir = Path("Cable_Dataset") / "labels"
        if not _looks_like_segmentation_labels(labels_dir):
            print(
                "⚠️ Segmentation labels not detected.\n"
                "- Export from Roboflow as YOLOv8 Segmentation (polygons)\n"
                "- Extract so you have: Cable_Dataset/images/(train|val|test) and Cable_Dataset/labels/(train|val|test)\n"
                "- A label line should look like: 0 x1 y1 x2 y2 x3 y3 ... (many numbers)\n"
            )

        # Load a pretrained YOLOv8 Segmentation model
        model = YOLO(MODEL_SIZE)
        print(f"Loaded base model: {MODEL_SIZE}")

        # Start Training
        results = model.train(
            data=DATA_YAML_PATH,     # Your dataset configuration file
            epochs=EPOCHS,           # Number of training cycles
            imgsz=IMG_SIZE,          # Input image size
            batch=BATCH_SIZE,        # Adjust based on your GPU VRAM
            device=device,           # Specify the device (cuda or cpu)
            name='cable_analysis_v1' # Run name
        )

        # Get the path of the best saved model
        save_dir = Path(results.save_dir)
        best_model_path = save_dir / 'weights' / 'best.pt'
        print(f"\nTraining Complete. Best model saved to: {best_model_path}")
        return best_model_path

    except Exception as e:
        print(f"An error occurred during training: {e}")
        return None

if __name__ == "__main__":
    trained_model_path = train_yolov8()
