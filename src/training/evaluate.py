"""
Evaluation script for trained models.
"""

import sys
import argparse
from pathlib import Path
import torch
from ultralytics import YOLO
import json


def evaluate_model(
    model_path: str | Path,
    data_yaml: str | Path,
    split: str = "test",
    device: str = "cuda",
    conf_threshold: float = 0.25,
    iou_threshold: float = 0.45,
    save_results: bool = True
):
    """
    Evaluate trained model on test set.

    Args:
        model_path: Path to trained model weights
        data_yaml: Path to data.yaml
        split: Dataset split to evaluate on (train/val/test)
        device: Device to use (cuda/cpu/mps)
        conf_threshold: Confidence threshold
        iou_threshold: IoU threshold for NMS
        save_results: Whether to save results to file
    """
    print("=" * 60)
    print("Model Evaluation")
    print("=" * 60)

    # Check device
    if device == "cuda" and not torch.cuda.is_available():
        print("⚠ CUDA not available, using CPU")
        device = "cpu"

    print(f"Model: {model_path}")
    print(f"Dataset: {data_yaml}")
    print(f"Split: {split}")
    print(f"Device: {device}")
    print()

    # Load model
    model = YOLO(model_path)

    # Validate
    print("Running validation...")
    results = model.val(
        data=str(data_yaml),
        split=split,
        device=device,
        conf=conf_threshold,
        iou=iou_threshold,
        verbose=True
    )

    # Display results
    print("\n" + "=" * 60)
    print("Evaluation Results")
    print("=" * 60)

    metrics = {
        'map50': results.box.map50,
        'map50_95': results.box.map,
        'precision': results.box.mp,
        'recall': results.box.mr,
        'f1_score': 2 * (results.box.mp * results.box.mr) / (results.box.mp + results.box.mr + 1e-6)
    }

    print("\nMetrics:")
    print(f"  mAP@0.5:     {metrics['map50']:.4f}")
    print(f"  mAP@0.5:0.95: {metrics['map50_95']:.4f}")
    print(f"  Precision:   {metrics['precision']:.4f}")
    print(f"  Recall:      {metrics['recall']:.4f}")
    print(f"  F1 Score:    {metrics['f1_score']:.4f}")

    # Save results
    if save_results:
        results_path = Path(model_path).parent / "evaluation_results.json"
        with open(results_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"\n✓ Results saved to: {results_path}")

    return results, metrics


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(
        description="Evaluate trained YOLOv8 model"
    )

    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to model weights"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data/processed/data.yaml",
        help="Path to data.yaml"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        choices=["train", "val", "test"],
        help="Dataset split to evaluate"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        help="Device (cuda/cpu/mps)"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold"
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.45,
        help="IoU threshold"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file"
    )

    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    model_path = project_root / args.model if not Path(args.model).is_absolute() else Path(args.model)
    data_yaml = project_root / args.data if not Path(args.data).is_absolute() else Path(args.data)

    # Check if model exists
    if not model_path.exists():
        print(f"✗ Model not found: {model_path}")
        return 1

    # Evaluate
    try:
        evaluate_model(
            model_path=model_path,
            data_yaml=data_yaml,
            split=args.split,
            device=args.device,
            conf_threshold=args.conf,
            iou_threshold=args.iou,
            save_results=not args.no_save
        )
    except Exception as e:
        print(f"\n✗ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
