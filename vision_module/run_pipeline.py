import argparse
import json
from pathlib import Path

import cv2
import torch

from vision_module.interface import analyze_cable_image
from vision_module.cnn_classifier import predict


def annotate_with_class(img, class_label: str, confidence: float):
    label = f"CNN: {class_label} ({confidence:.2f})"
    (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    padding = 12
    x1, y1 = 20, img.shape[0] - 40
    x2, y2 = x1 + text_w + padding, y1 + text_h + padding
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), -1)
    cv2.putText(
        img,
        label,
        (x1 + 8, y2 - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return img


def run_pipeline(image_path: Path, weights_path: Path, output_dir: Path = None, output_json: Path = None):
    image_path = image_path.resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    processed_img, vision_results = analyze_cable_image(str(image_path))
    if processed_img is None:
        raise RuntimeError("Vision analysis returned no image result.")

    cnn_class, cnn_confidence = predict(image_path, weights_path, device)

    annotated_img = annotate_with_class(processed_img.copy(), cnn_class, cnn_confidence)

    result = {
        "image": str(image_path),
        "cnn_prediction": {
            "class": cnn_class,
            "confidence": round(float(cnn_confidence), 4),
        },
        "vision_results": vision_results,
    }

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_image_path = output_dir / f"ANNOTATED_{image_path.name}"
    else:
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        output_image_path = Path(temp_file.name)
        temp_file.close()

    cv2.imwrite(str(output_image_path), annotated_img)
    result["annotated_image"] = str(output_image_path)

    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    return result


def main():
    parser = argparse.ArgumentParser(description="Run end-to-end YOLO + CNN cable pipeline")
    parser.add_argument("--image", required=True, help="Path to the input image")
    parser.add_argument(
        "--weights",
        default=str(Path(__file__).resolve().parent / "classifier_weights" / "cable_classifier.pth"),
        help="Path to the pretrained CNN weights",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "pipeline_outputs"),
        help="Directory where annotated images will be saved",
    )
    parser.add_argument(
        "--output-json",
        default=str(Path(__file__).resolve().parent / "pipeline_outputs" / "result.json"),
        help="Save pipeline result as JSON",
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    weights_path = Path(args.weights)
    output_dir = Path(args.output_dir) if args.output_dir else None
    output_json = Path(args.output_json) if args.output_json else None

    result = run_pipeline(image_path, weights_path, output_dir=output_dir, output_json=output_json)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
