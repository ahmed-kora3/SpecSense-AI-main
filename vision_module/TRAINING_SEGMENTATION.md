# Training: YOLOv8 Segmentation (Cables)

This repo trains segmentation using Ultralytics YOLOv8.

## 1) Dataset folder layout (required)

Make sure your exported Roboflow ZIP is extracted so you have:

```
vision_module/Cable_Dataset/
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
```

### Quick verification

Open any label file (for example `Cable_Dataset/labels/train/*.txt`):

- **Segmentation label (correct):** `0 x1 y1 x2 y2 x3 y3 ...` (many numbers)
- **Detection label (not segmentation):** `0 xc yc w h` (only 5 values)

If you see detection-only labels, re-export from Roboflow using **YOLOv8 Segmentation** (polygons).

## 2) `data.yaml`

`vision_module/data.yaml` is already set to:

- `path: Cable_Dataset`
- `train/val/test: images/...`

## 3) Install dependencies

From the repo root:

```
pip install -r requirements.txt
```

## 4) Train

Option A) Python script:

```
cd vision_module
python train_model.py
```

Option B) Ultralytics CLI:

```
cd vision_module
yolo task=segment mode=train model=yolov8n-seg.pt data=data.yaml epochs=100 imgsz=640
```

## 5) Output

Ultralytics will create a run folder like:

`vision_module/runs/segment/<run-name>/weights/best.pt`

