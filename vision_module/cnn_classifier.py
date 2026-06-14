"""
CNN Cable Classifier

Usage:
  python cnn_classifier.py train --data-dir classification_data --epochs 20
  python cnn_classifier.py predict --image path/to/image.jpg

Dataset layout:
  vision_module/classification_data/train/<class_name>/*.jpg
  vision_module/classification_data/val/<class_name>/*.jpg

If you want to classify YOLO-extracted cable crops, prepare them in the above folder structure first.
"""

import argparse
from pathlib import Path

from PIL import Image
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


SCRIPT_DIR = Path(__file__).resolve().parent
CLASSIFICATION_DATA_DIR = SCRIPT_DIR / "classification_data"
WEIGHTS_DIR = SCRIPT_DIR / "classifier_weights"
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)


def get_transforms(train: bool = True):
    if train:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])


def build_model(num_classes: int):
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def _remove_empty_class_dirs(parent_dir: Path):
    """Remove class folders that contain no valid image files."""
    if not parent_dir.exists():
        return

    valid_extensions = {'.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif', '.tiff', '.webp'}
    for child in list(parent_dir.iterdir()):
        if not child.is_dir():
            continue
        has_image = any(file.suffix.lower() in valid_extensions for file in child.glob('*'))
        if not has_image:
            child.rmdir()
            print(f"[INFO] Removed empty class folder: {child}")


def train_classifier(data_dir: Path, epochs: int, batch_size: int, lr: float, output_path: Path):
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"

    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError(
            f"Expected classification data layout:\n"
            f"  {data_dir}/train/<class_name>/*.jpg\n"
            f"  {data_dir}/val/<class_name>/*.jpg"
        )

    _remove_empty_class_dirs(train_dir)
    _remove_empty_class_dirs(val_dir)

    train_dataset = datasets.ImageFolder(train_dir, transform=get_transforms(train=True))
    val_dataset = datasets.ImageFolder(val_dir, transform=get_transforms(train=False))

    if len(train_dataset.classes) < 2:
        raise ValueError("Need at least 2 classes for classification.")

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(len(train_dataset.classes)).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.5)

    best_val_acc = 0.0
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        running_corrects = 0

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            running_corrects += (outputs.argmax(dim=1) == labels).sum().item()

        epoch_loss = running_loss / len(train_dataset)
        epoch_acc = running_corrects / len(train_dataset)

        val_acc = evaluate(model, val_loader, device)
        scheduler.step()

        print(f"Epoch {epoch}/{epochs} | train_loss={epoch_loss:.4f} train_acc={epoch_acc:.4f} val_acc={val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                "model_state_dict": model.state_dict(),
                "class_to_idx": train_dataset.class_to_idx,
            }, output_path)
            print(f"Saved best model: {output_path}")

    print(f"Training complete. Best val accuracy: {best_val_acc:.4f}")
    return train_dataset.classes


def evaluate(model: nn.Module, data_loader: DataLoader, device: torch.device) -> float:
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in data_loader:
            images = images.to(device)
            labels = labels.to(device)
            outputs = model(images)
            correct += (outputs.argmax(dim=1) == labels).sum().item()
            total += images.size(0)

    return correct / total if total else 0.0


def load_model(weights_path: Path, num_classes: int, device: torch.device):
    checkpoint = torch.load(weights_path, map_location=device, weights_only=False)
    model = build_model(num_classes).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, checkpoint.get("class_to_idx", {})


def predict(image_path: Path, weights_path: Path, device: torch.device):
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    checkpoint = torch.load(weights_path, map_location=device, weights_only=False)
    class_to_idx = checkpoint.get("class_to_idx", {})
    idx_to_class = {v: k for k, v in class_to_idx.items()}

    model = build_model(len(idx_to_class)).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    transform = get_transforms(train=False)
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image)
        pred_idx = int(outputs.argmax(dim=1).item())

    return idx_to_class.get(pred_idx, str(pred_idx)), outputs.softmax(dim=1).max().item()


def main():
    parser = argparse.ArgumentParser(description="CNN-based Cable Classifier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train", help="Train the cable classifier")
    train_parser.add_argument("--data-dir", type=str, default=str(CLASSIFICATION_DATA_DIR), help="Root folder for classification data")
    train_parser.add_argument("--epochs", type=int, default=20)
    train_parser.add_argument("--batch-size", type=int, default=16)
    train_parser.add_argument("--lr", type=float, default=1e-4)
    train_parser.add_argument("--output", type=str, default=str(WEIGHTS_DIR / "cable_classifier.pth"))

    predict_parser = subparsers.add_parser("predict", help="Predict cable class from a single image")
    predict_parser.add_argument("--image", type=str, required=True)
    predict_parser.add_argument("--weights", type=str, default=str(WEIGHTS_DIR / "cable_classifier.pth"))

    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if args.command == "train":
        output_path = Path(args.output)
        classes = train_classifier(Path(args.data_dir), args.epochs, args.batch_size, args.lr, output_path)
        print("Classes:", classes)
    elif args.command == "predict":
        pred_class, confidence = predict(Path(args.image), Path(args.weights), device)
        print(f"Prediction: {pred_class} ({confidence:.3f})")


if __name__ == "__main__":
    main()
