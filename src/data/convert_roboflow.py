"""
Convert Roboflow COCO format to YOLO format.

The Zenodo dataset comes in Roboflow format with:
- train/_annotations.coco.json
- valid/_annotations.coco.json (OD dataset only)
- test/_annotations.coco.json (OD dataset only)
"""

import sys
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from tqdm import tqdm


def coco_bbox_to_yolo(coco_bbox: List[float], img_width: int, img_height: int) -> List[float]:
    """Convert COCO bbox to YOLO format."""
    x_min, y_min, bbox_w, bbox_h = coco_bbox

    x_center = x_min + bbox_w / 2
    y_center = y_min + bbox_h / 2

    x_center_norm = np.clip(x_center / img_width, 0, 1)
    y_center_norm = np.clip(y_center / img_height, 0, 1)
    width_norm = np.clip(bbox_w / img_width, 0, 1)
    height_norm = np.clip(bbox_h / img_height, 0, 1)

    return [x_center_norm, y_center_norm, width_norm, height_norm]


def convert_split(
    source_split_dir: Path,
    dest_dir: Path,
    split_name: str,
    class_mapping: Dict[int, int],
    dataset_name: str
) -> Tuple[int, int, int]:
    """
    Convert a single split (train/valid/test) from COCO to YOLO.

    Args:
        source_split_dir: Source directory (e.g., white/train)
        dest_dir: Destination root directory
        split_name: Split name (train/val/test)
        class_mapping: COCO category_id to YOLO class_id mapping
        dataset_name: Dataset name for logging

    Returns:
        Tuple of (num_images, num_annotations, num_errors)
    """
    # Find COCO annotation file
    json_path = source_split_dir / "_annotations.coco.json"

    if not json_path.exists():
        print(f"  ⚠ No annotations found in {source_split_dir}")
        return 0, 0, 0

    # Load annotations
    with open(json_path, 'r') as f:
        coco_data = json.load(f)

    images = {img['id']: img for img in coco_data.get('images', [])}
    annotations = coco_data.get('annotations', [])
    categories = coco_data.get('categories', [])

    print(f"  {split_name}: {len(images)} images, {len(annotations)} annotations")

    # Group annotations by image
    annotations_by_image = {}
    for ann in annotations:
        img_id = ann['image_id']
        if img_id not in annotations_by_image:
            annotations_by_image[img_id] = []
        annotations_by_image[img_id].append(ann)

    # Create destination directories
    dest_images_dir = dest_dir / "images" / split_name / dataset_name
    dest_labels_dir = dest_dir / "labels" / split_name / dataset_name
    dest_images_dir.mkdir(parents=True, exist_ok=True)
    dest_labels_dir.mkdir(parents=True, exist_ok=True)

    # Convert each image
    num_converted = 0
    num_annotations_converted = 0
    num_errors = 0

    for img_id, img_info in tqdm(images.items(), desc=f"    {dataset_name}/{split_name}", leave=False):
        try:
            img_filename = img_info['file_name']
            source_img_path = source_split_dir / img_filename

            if not source_img_path.exists():
                num_errors += 1
                continue

            # Copy image
            dest_img_path = dest_images_dir / img_filename
            shutil.copy2(source_img_path, dest_img_path)

            # Create YOLO label
            label_filename = Path(img_filename).stem + ".txt"
            dest_label_path = dest_labels_dir / label_filename

            img_width = img_info['width']
            img_height = img_info['height']

            yolo_annotations = []
            if img_id in annotations_by_image:
                for ann in annotations_by_image[img_id]:
                    coco_class_id = ann['category_id']
                    yolo_class_id = class_mapping.get(coco_class_id, 0)

                    coco_bbox = ann['bbox']
                    yolo_bbox = coco_bbox_to_yolo(coco_bbox, img_width, img_height)

                    yolo_line = f"{yolo_class_id} {' '.join(map(str, yolo_bbox))}\n"
                    yolo_annotations.append(yolo_line)
                    num_annotations_converted += 1

            with open(dest_label_path, 'w') as f:
                f.writelines(yolo_annotations)

            num_converted += 1

        except Exception as e:
            print(f"    ✗ Error: {e}")
            num_errors += 1

    return num_converted, num_annotations_converted, num_errors


def main():
    parser = argparse.ArgumentParser(description="Convert Roboflow COCO to YOLO")
    parser.add_argument("--source-dir", type=str, default="data/raw")
    parser.add_argument("--dest-dir", type=str, default="data/processed")
    parser.add_argument("--datasets", nargs="+", default=["white", "black", "OD"])

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent
    source_dir = project_root / args.source_dir
    dest_dir = project_root / args.dest_dir

    # Class mapping
    class_mapping = {1: 0}  # black_ice
    class_names = ["black_ice"]

    print("=" * 60)
    print("Roboflow COCO to YOLO Converter")
    print("=" * 60)
    print(f"Source: {source_dir}")
    print(f"Destination: {dest_dir}")
    print(f"Datasets: {', '.join(args.datasets)}")
    print()

    split_stats = {'train': {}, 'val': {}, 'test': {}}

    for dataset_name in args.datasets:
        print(f"\n📦 Processing {dataset_name} dataset")
        print("-" * 60)

        dataset_dir = source_dir / dataset_name
        if not dataset_dir.exists():
            print(f"  ⚠ {dataset_dir} not found, skipping")
            continue

        # Process splits
        splits = {
            'train': 'train',
            'val': 'valid',  # Roboflow uses 'valid'
            'test': 'test'
        }

        for yolo_split, roboflow_split in splits.items():
            split_dir = dataset_dir / roboflow_split

            if not split_dir.exists():
                continue

            num_img, num_ann, num_err = convert_split(
                split_dir, dest_dir, yolo_split, class_mapping, dataset_name
            )

            if yolo_split not in split_stats:
                split_stats[yolo_split] = {'images': 0, 'annotations': 0, 'errors': 0}

            split_stats[yolo_split]['images'] = split_stats[yolo_split].get('images', 0) + num_img
            split_stats[yolo_split]['annotations'] = split_stats[yolo_split].get('annotations', 0) + num_ann
            split_stats[yolo_split]['errors'] = split_stats[yolo_split].get('errors', 0) + num_err

    # Create data.yaml
    yaml_content = f"""# Black Ice Dataset Configuration
# Generated from Roboflow format

path: {dest_dir.absolute()}
train: images/train
val: images/val
test: images/test

nc: {len(class_names)}
names: {class_names}
"""

    yaml_path = dest_dir / "data.yaml"
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)

    # Summary
    print("\n" + "=" * 60)
    print("Conversion Summary")
    print("=" * 60)

    for split in ['train', 'val', 'test']:
        if split in split_stats and split_stats[split].get('images', 0) > 0:
            stats = split_stats[split]
            print(f"{split.capitalize():5s}: {stats['images']:4d} images, {stats['annotations']:4d} annotations")
            if stats['errors'] > 0:
                print(f"       {stats['errors']} errors")

    total_images = sum(s.get('images', 0) for s in split_stats.values())
    total_annotations = sum(s.get('annotations', 0) for s in split_stats.values())

    print(f"\nTotal: {total_images} images, {total_annotations} annotations")

    if total_images > 0:
        print(f"Avg annotations/image: {total_annotations/total_images:.2f}")
        print(f"\n✓ Created {yaml_path}")
        print("\n✓ Conversion complete!")
        print("\nDataset is ready for training:")
        print("  python src/training/train.py --data data/processed/data.yaml")
    else:
        print("\n✗ No images converted")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
