"""
Export trained model to deployment formats.
"""

import sys
import argparse
from pathlib import Path
from ultralytics import YOLO


def export_model(
    model_path: str | Path,
    format: str = "onnx",
    img_size: int = 640,
    dynamic: bool = False,
    simplify: bool = True,
    opset: int = 12,
    half: bool = False
):
    """
    Export model to specified format.

    Args:
        model_path: Path to trained model weights
        format: Export format (onnx, torchscript, coreml, tflite, etc.)
        img_size: Image size for export
        dynamic: Enable dynamic input shapes
        simplify: Simplify ONNX model
        opset: ONNX opset version
        half: Export in FP16 (half precision)
    """
    print("=" * 60)
    print("Model Export")
    print("=" * 60)
    print(f"Model: {model_path}")
    print(f"Format: {format}")
    print(f"Image size: {img_size}")
    print(f"Dynamic shapes: {dynamic}")
    if format == "onnx":
        print(f"Simplify: {simplify}")
        print(f"Opset: {opset}")
    print(f"Half precision: {half}")
    print()

    # Load model
    print("Loading model...")
    model = YOLO(model_path)

    # Export
    print(f"Exporting to {format.upper()}...")
    export_path = model.export(
        format=format,
        imgsz=img_size,
        dynamic=dynamic,
        simplify=simplify if format == "onnx" else None,
        opset=opset if format == "onnx" else None,
        half=half
    )

    print("\n" + "=" * 60)
    print("Export Complete!")
    print("=" * 60)
    print(f"Exported model: {export_path}")

    # Move to exported directory
    export_path = Path(export_path)
    dest_dir = Path(model_path).parent.parent.parent / "exported"
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / export_path.name
    if export_path != dest_path:
        import shutil
        shutil.copy2(export_path, dest_path)
        print(f"Copied to: {dest_path}")

    # Test exported model
    if format == "onnx":
        print("\nTesting exported model...")
        try:
            import onnxruntime as ort
            session = ort.InferenceSession(str(dest_path))
            print("✓ ONNX model loaded successfully")

            # Print input/output info
            print("\nModel inputs:")
            for inp in session.get_inputs():
                print(f"  {inp.name}: {inp.shape} ({inp.type})")

            print("\nModel outputs:")
            for out in session.get_outputs():
                print(f"  {out.name}: {out.shape} ({out.type})")

        except Exception as e:
            print(f"⚠ Could not test ONNX model: {e}")

    return export_path


def main():
    """Main export function."""
    parser = argparse.ArgumentParser(
        description="Export trained model to deployment format"
    )

    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to model weights"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="onnx",
        choices=["onnx", "torchscript", "coreml", "tflite", "engine", "saved_model"],
        help="Export format"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Image size"
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="Enable dynamic input shapes"
    )
    parser.add_argument(
        "--simplify",
        action="store_true",
        default=True,
        help="Simplify ONNX model"
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=12,
        help="ONNX opset version"
    )
    parser.add_argument(
        "--half",
        action="store_true",
        help="Export in FP16 half precision"
    )

    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    model_path = project_root / args.model if not Path(args.model).is_absolute() else Path(args.model)

    # Check if model exists
    if not model_path.exists():
        print(f"✗ Model not found: {model_path}")
        return 1

    # Export
    try:
        export_model(
            model_path=model_path,
            format=args.format,
            img_size=args.imgsz,
            dynamic=args.dynamic,
            simplify=args.simplify,
            opset=args.opset,
            half=args.half
        )
    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
