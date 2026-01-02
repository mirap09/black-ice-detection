"""
Split dataset into train/val/test sets.

Performs stratified splitting to ensure balanced representation from
each source dataset (white, black, outdoor).
"""

import os
import sys
import argparse
import shutil
import random
from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict
import yaml


def get_image_files(images_dir: Path) -> List[Path]:
    """
    Get all image files from directory.

    Args:
        images_dir: Directory containing images

    Returns:
        List of image file paths
    """
    extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []

    for ext in extensions:
        image_files.extend(images_dir.glob(f"*{ext}"))
        image_files.extend(images_dir.glob(f"*{ext.upper()}"))

    return sorted(image_files)


def stratify_by_source(
    image_files: List[Path],
    source_keywords: List[str]
) -> Dict[str, List[Path]]:
    """
    Group images by source dataset based on filename keywords.

    Args:
        image_files: List of image paths
        source_keywords: Keywords to identify source datasets

    Returns:
        Dictionary mapping source name to list of image paths
    """
    stratified = defaultdict(list)

    for img_path in image_files:
        filename = img_path.stem.lower()

        # Try to identify source based on filename
        source_identified = False
        for keyword in source_keywords:
            if keyword.lower() in filename:
                stratified[keyword].append(img_path)
                source_identified = True
                break

        if not source_identified:
            # If no keyword matches, group as "other"
            stratified["other"].append(img_path)

    return dict(stratified)


def split_dataset(
    images: List[Path],
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int
) -> Tuple[List[Path], List[Path], List[Path]]:
    """
    Split dataset into train/val/test sets.

    Args:
        images: List of image paths
        train_ratio: Training set ratio
        val_ratio: Validation set ratio
        test_ratio: Test set ratio
        seed: Random seed for reproducibility

    Returns:
        Tuple of (train_images, val_images, test_images)
    """
    # Validate ratios
    total_ratio = train_ratio + val_ratio + test_ratio
    assert abs(total_ratio - 1.0) < 1e-6, f"Ratios must sum to 1.0, got {total_ratio}"

    # Shuffle with seed
    random.seed(seed)
    shuffled = images.copy()
    random.shuffle(shuffled)

    # Calculate split indices
    n_total = len(shuffled)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    # Split
    train = shuffled[:n_train]
    val = shuffled[n_train:n_train + n_val]
    test = shuffled[n_train + n_val:]

    return train, val, test


def copy_files(
    image_files: List[Path],
    source_images_dir: Path,
    source_labels_dir: Path,
    dest_images_dir: Path,
    dest_labels_dir: Path
) -> Tuple[int, int]:
    """
    Copy image and label files to destination.

    Args:
        image_files: List of image paths to copy
        source_images_dir: Source images directory
        source_labels_dir: Source labels directory
        dest_images_dir: Destination images directory
        dest_labels_dir: Destination labels directory

    Returns:
        Tuple of (num_images_copied, num_labels_copied)
    """
    dest_images_dir.mkdir(parents=True, exist_ok=True)
    dest_labels_dir.mkdir(parents=True, exist_ok=True)

    num_images = 0
    num_labels = 0

    for img_path in image_files:
        # Copy image
        dest_img = dest_images_dir / img_path.name
        shutil.copy2(img_path, dest_img)
        num_images += 1

        # Copy corresponding label
        label_filename = img_path.stem + ".txt"
        source_label = source_labels_dir / label_filename

        if source_label.exists():
            dest_label = dest_labels_dir / label_filename
            shutil.copy2(source_label, dest_label)
            num_labels += 1

    return num_images, num_labels


def update_data_yaml(
    yaml_path: Path,
    splits_info: Dict[str, int]
):
    """
    Update data.yaml with split information.

    Args:
        yaml_path: Path to data.yaml file
        splits_info: Dictionary with split statistics
    """
    # Read existing yaml
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    # Add split information
    data['splits'] = {
        'train': splits_info['train'],
        'val': splits_info['val'],
        'test': splits_info['test'],
        'total': splits_info['total']
    }

    # Write updated yaml
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    print(f"\n✓ Updated {yaml_path}")


def main():
    """Main splitting function."""
    parser = argparse.ArgumentParser(
        description="Split dataset into train/val/test sets"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Data directory with converted YOLO format data"
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.7,
        help="Training set ratio (default: 0.7)"
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.2,
        help="Validation set ratio (default: 0.2)"
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.1,
        help="Test set ratio (default: 0.1)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--stratify",
        action="store_true",
        help="Perform stratified split by source dataset"
    )
    parser.add_argument(
        "--source-keywords",
        nargs="+",
        default=["white", "black", "od", "outdoor"],
        help="Keywords to identify source datasets for stratification"
    )

    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / args.data_dir
    source_images_dir = data_dir / "images"
    source_labels_dir = data_dir / "labels"

    print("=" * 60)
    print("Dataset Splitter")
    print("=" * 60)
    print(f"Data directory: {data_dir}")
    print(f"Split ratios: Train={args.train_ratio:.1%}, Val={args.val_ratio:.1%}, Test={args.test_ratio:.1%}")
    print(f"Random seed: {args.seed}")
    print(f"Stratified: {args.stratify}")
    print()

    # Check if source directories exist
    if not source_images_dir.exists():
        print(f"✗ Error: {source_images_dir} does not exist")
        print("Please run convert.py first to convert COCO to YOLO format")
        return 1

    # Get all image files
    print("Scanning for images...")
    image_files = get_image_files(source_images_dir)
    print(f"Found {len(image_files)} images")

    if len(image_files) == 0:
        print("✗ No images found")
        return 1

    # Perform splitting
    all_train = []
    all_val = []
    all_test = []

    if args.stratify:
        print("\nPerforming stratified split...")
        stratified = stratify_by_source(image_files, args.source_keywords)

        print("\nDataset distribution:")
        for source, images in stratified.items():
            print(f"  {source}: {len(images)} images")

            # Split each stratum
            train, val, test = split_dataset(
                images,
                args.train_ratio,
                args.val_ratio,
                args.test_ratio,
                args.seed
            )

            all_train.extend(train)
            all_val.extend(val)
            all_test.extend(test)

            print(f"    → Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

    else:
        print("\nPerforming random split...")
        all_train, all_val, all_test = split_dataset(
            image_files,
            args.train_ratio,
            args.val_ratio,
            args.test_ratio,
            args.seed
        )

    # Summary
    print("\n" + "=" * 60)
    print("Split Summary")
    print("=" * 60)
    print(f"Train: {len(all_train)} images ({len(all_train)/len(image_files):.1%})")
    print(f"Val:   {len(all_val)} images ({len(all_val)/len(image_files):.1%})")
    print(f"Test:  {len(all_test)} images ({len(all_test)/len(image_files):.1%})")
    print(f"Total: {len(image_files)} images")

    # Copy files to train/val/test directories
    print("\nCopying files to train/val/test directories...")

    splits = {
        'train': all_train,
        'val': all_val,
        'test': all_test
    }

    splits_info = {'total': len(image_files)}

    for split_name, split_files in splits.items():
        print(f"\n📁 {split_name.capitalize()} set:")
        dest_images = data_dir / "images" / split_name
        dest_labels = data_dir / "labels" / split_name

        num_images, num_labels = copy_files(
            split_files,
            source_images_dir,
            source_labels_dir,
            dest_images,
            dest_labels
        )

        print(f"  ✓ Copied {num_images} images and {num_labels} labels")
        splits_info[split_name] = num_images

        if num_labels < num_images:
            print(f"  ⚠ Warning: {num_images - num_labels} images missing labels")

    # Update data.yaml
    yaml_path = data_dir / "data.yaml"
    if yaml_path.exists():
        update_data_yaml(yaml_path, splits_info)

    print("\n" + "=" * 60)
    print("✓ Dataset split complete!")
    print("=" * 60)
    print("\nDataset structure:")
    print(f"  {data_dir}/")
    print("  ├── images/")
    print(f"  │   ├── train/  ({splits_info['train']} images)")
    print(f"  │   ├── val/    ({splits_info['val']} images)")
    print(f"  │   └── test/   ({splits_info['test']} images)")
    print("  └── labels/")
    print(f"      ├── train/  ({splits_info['train']} labels)")
    print(f"      ├── val/    ({splits_info['val']} labels)")
    print(f"      └── test/   ({splits_info['test']} labels)")

    print("\nNext step:")
    print("  python src/training/train.py  # Start training")

    return 0


if __name__ == "__main__":
    sys.exit(main())
