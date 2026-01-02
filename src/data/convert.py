"""
Convert COCO format annotations to YOLO format.

COCO format (JSON):
{
    "images": [{"id": 1, "file_name": "img.jpg", "width": 640, "height": 480}],
    "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [x, y, w, h]}],
    "categories": [{"id": 1, "name": "black_ice"}]
}

YOLO format (TXT, one file per image):
<class_id> <x_center> <y_center> <width> <height>
All values normalized to [0, 1]
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from tqdm import tqdm


def coco_bbox_to_yolo(coco_bbox: List[float], img_width: int, img_height: int) -> List[float]:
    """
    Convert COCO bbox format to YOLO format.

    COCO: [x_min, y_min, width, height] (absolute pixels)
    YOLO: [x_center, y_center, width, height] (normalized 0-1)

    Args:
        coco_bbox: COCO format bbox [x, y, w, h]
        img_width: Image width in pixels
        img_height: Image height in pixels

    Returns:
        YOLO format bbox [x_center, y_center, w, h] (normalized)
    """
    x_min, y_min, bbox_w, bbox_h = coco_bbox

    # Calculate center
    x_center = x_min + bbox_w / 2
    y_center = y_min + bbox_h / 2

    # Normalize to [0, 1]
    x_center_norm = x_center / img_width
    y_center_norm = y_center / img_height
    width_norm = bbox_w / img_width
    height_norm = bbox_h / img_height

    # Clip to [0, 1] to handle potential errors
    x_center_norm = np.clip(x_center_norm, 0, 1)
    y_center_norm = np.clip(y_center_norm, 0, 1)
    width_norm = np.clip(width_norm, 0, 1)
    height_norm = np.clip(height_norm, 0, 1)

    return [x_center_norm, y_center_norm, width_norm, height_norm]


def load_coco_annotations(json_path: Path) -> Tuple[Dict, List, List]:
    """
    Load COCO format annotations from JSON file.

    Args:
        json_path: Path to COCO JSON file

    Returns:
        Tuple of (images_dict, annotations_list, categories_list)
    """
    with open(json_path, 'r') as f:
        coco_data = json.load(f)

    images = {img['id']: img for img in coco_data.get('images', [])}
    annotations = coco_data.get('annotations', [])
    categories = coco_data.get('categories', [])

    return images, annotations, categories


def convert_dataset(
    source_dir: Path,
    dest_dir: Path,
    dataset_name: str,
    class_mapping: Dict[int, int]
) -> Tuple[int, int, int]:
    """
    Convert a single dataset from COCO to YOLO format.

    Args:
        source_dir: Source directory containing images and annotations
        dest_dir: Destination directory for YOLO format
        dataset_name: Name of the dataset (for logging)
        class_mapping: Mapping from COCO category_id to YOLO class_id

    Returns:
        Tuple of (num_images, num_annotations, num_errors)
    """
    # Find COCO JSON file
    json_files = list(source_dir.glob("*.json"))
    if not json_files:
        print(f"⚠ Warning: No JSON annotation file found in {source_dir}")
        return 0, 0, 0

    json_path = json_files[0]
    print(f"  Loading annotations from: {json_path.name}")

    # Load COCO annotations
    images, annotations, categories = load_coco_annotations(json_path)

    print(f"  Found {len(images)} images, {len(annotations)} annotations, {len(categories)} categories")

    # Create destination directories
    images_dir = dest_dir / "images"
    labels_dir = dest_dir / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    # Group annotations by image
    annotations_by_image = {}
    for ann in annotations:
        img_id = ann['image_id']
        if img_id not in annotations_by_image:
            annotations_by_image[img_id] = []
        annotations_by_image[img_id].append(ann)

    # Convert each image
    num_converted = 0
    num_annotations_converted = 0
    num_errors = 0

    for img_id, img_info in tqdm(images.items(), desc=f"  Converting {dataset_name}"):
        try:
            # Find source image
            img_filename = img_info['file_name']
            source_img_path = source_dir / img_filename

            if not source_img_path.exists():
                # Try alternative paths
                source_img_path = source_dir / "images" / img_filename
                if not source_img_path.exists():
                    print(f"    ⚠ Image not found: {img_filename}")
                    num_errors += 1
                    continue

            # Copy image to destination
            dest_img_path = images_dir / img_filename
            shutil.copy2(source_img_path, dest_img_path)

            # Create YOLO label file
            label_filename = Path(img_filename).stem + ".txt"
            dest_label_path = labels_dir / label_filename

            # Convert annotations for this image
            img_width = img_info['width']
            img_height = img_info['height']

            yolo_annotations = []
            if img_id in annotations_by_image:
                for ann in annotations_by_image[img_id]:
                    # Get YOLO class id
                    coco_class_id = ann['category_id']
                    yolo_class_id = class_mapping.get(coco_class_id, 0)

                    # Convert bbox
                    coco_bbox = ann['bbox']
                    yolo_bbox = coco_bbox_to_yolo(coco_bbox, img_width, img_height)

                    # Format: <class_id> <x_center> <y_center> <width> <height>
                    yolo_line = f"{yolo_class_id} {' '.join(map(str, yolo_bbox))}\n"
                    yolo_annotations.append(yolo_line)
                    num_annotations_converted += 1

            # Write YOLO label file (even if empty)
            with open(dest_label_path, 'w') as f:
                f.writelines(yolo_annotations)

            num_converted += 1

        except Exception as e:
            print(f"    ✗ Error processing {img_info.get('file_name', 'unknown')}: {e}")
            num_errors += 1

    return num_converted, num_annotations_converted, num_errors


def create_data_yaml(dest_dir: Path, class_names: List[str]):
    """
    Create data.yaml configuration file for YOLO training.

    Args:
        dest_dir: Destination directory
        class_names: List of class names
    """
    yaml_content = f"""# Black Ice Dataset Configuration
# Generated by convert.py

# Paths (relative to this file)
path: {dest_dir.absolute()}
train: images/train
val: images/val
test: images/test

# Classes
nc: {len(class_names)}  # number of classes
names: {class_names}  # class names
"""

    yaml_path = dest_dir / "data.yaml"
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)

    print(f"\n✓ Created {yaml_path}")


def main():
    """Main conversion function."""
    parser = argparse.ArgumentParser(
        description="Convert COCO format to YOLO format"
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default="data/raw",
        help="Source directory with COCO format data"
    )
    parser.add_argument(
        "--dest-dir",
        type=str,
        default="data/processed",
        help="Destination directory for YOLO format data"
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["white", "black", "OD"],
        help="Dataset subdirectories to convert"
    )

    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    source_dir = project_root / args.source_dir
    dest_dir = project_root / args.dest_dir

    # Class mapping (single class: black ice)
    # COCO category_id -> YOLO class_id
    class_mapping = {1: 0}  # Assuming COCO category_id 1 = black_ice
    class_names = ["black_ice"]

    print("=" * 60)
    print("COCO to YOLO Converter")
    print("=" * 60)
    print(f"Source: {source_dir}")
    print(f"Destination: {dest_dir}")
    print(f"Datasets: {', '.join(args.datasets)}")
    print(f"Classes: {class_names}")
    print()

    # Convert each dataset
    total_images = 0
    total_annotations = 0
    total_errors = 0

    for dataset_name in args.datasets:
        print(f"\n📦 Processing {dataset_name} dataset")
        print("-" * 60)

        dataset_source = source_dir / dataset_name
        if not dataset_source.exists():
            print(f"  ⚠ Warning: {dataset_source} does not exist, skipping")
            continue

        num_images, num_annotations, num_errors = convert_dataset(
            dataset_source,
            dest_dir,
            dataset_name,
            class_mapping
        )

        print(f"  ✓ Converted {num_images} images with {num_annotations} annotations")
        if num_errors > 0:
            print(f"  ⚠ {num_errors} errors encountered")

        total_images += num_images
        total_annotations += num_annotations
        total_errors += num_errors

    # Create data.yaml
    create_data_yaml(dest_dir, class_names)

    # Summary
    print("\n" + "=" * 60)
    print("Conversion Summary")
    print("=" * 60)
    print(f"Total images: {total_images}")
    print(f"Total annotations: {total_annotations}")
    print(f"Average annotations per image: {total_annotations/total_images:.2f}" if total_images > 0 else "N/A")
    if total_errors > 0:
        print(f"⚠ Errors: {total_errors}")

    if total_images > 0:
        print("\n✓ Conversion complete!")
        print("\nNext step:")
        print("  python src/data/split.py  # Create train/val/test splits")
    else:
        print("\n✗ No images were converted. Please check your source directory.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
