"""
Dataset downloader for Zenodo Black Ice Dataset.

Downloads the three dataset ZIP files:
- white.zip (68.3 MB) - Indoor white background
- black.zip (199.2 MB) - Indoor black background
- OD.zip (167.4 MB) - Outdoor conditions

Total: ~435 MB
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple
import requests
from tqdm import tqdm


# Zenodo record URL
ZENODO_RECORD_ID = "10428765"
BASE_URL = f"https://zenodo.org/records/{ZENODO_RECORD_ID}/files"

# Dataset files to download
DATASET_FILES = [
    ("white.zip", 68.3, "Indoor white background dataset"),
    ("black.zip", 199.2, "Indoor black background dataset"),
    ("OD.zip", 167.4, "Outdoor conditions dataset"),
]


def download_file(url: str, destination: Path, description: str = "") -> bool:
    """
    Download a file from URL with progress bar.

    Args:
        url: URL to download from
        destination: Path to save the file
        description: Description for progress bar

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if file already exists
        if destination.exists():
            print(f"✓ {destination.name} already exists, skipping download")
            return True

        # Make request
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Get file size
        total_size = int(response.headers.get('content-length', 0))

        # Download with progress bar
        with open(destination, 'wb') as f:
            with tqdm(
                desc=description or destination.name,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print(f"✓ Downloaded {destination.name}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ Error downloading {destination.name}: {e}")
        if destination.exists():
            destination.unlink()  # Remove partial file
        return False


def extract_zip(zip_path: Path, extract_dir: Path) -> bool:
    """
    Extract a ZIP file.

    Args:
        zip_path: Path to ZIP file
        extract_dir: Directory to extract to

    Returns:
        True if successful, False otherwise
    """
    import zipfile

    try:
        # Check if already extracted
        expected_dir = extract_dir / zip_path.stem
        if expected_dir.exists() and any(expected_dir.iterdir()):
            print(f"✓ {zip_path.name} already extracted, skipping")
            return True

        print(f"Extracting {zip_path.name}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        print(f"✓ Extracted {zip_path.name}")
        return True

    except Exception as e:
        print(f"✗ Error extracting {zip_path.name}: {e}")
        return False


def verify_download(data_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verify that all dataset files were downloaded and extracted.

    Args:
        data_dir: Root data directory

    Returns:
        Tuple of (success, list of missing items)
    """
    missing = []

    # Check for extracted directories
    expected_dirs = ["white", "black", "OD"]
    for dir_name in expected_dirs:
        dir_path = data_dir / "raw" / dir_name
        if not dir_path.exists():
            missing.append(f"Directory: {dir_name}")
        elif not any(dir_path.iterdir()):
            missing.append(f"Directory (empty): {dir_name}")

    return len(missing) == 0, missing


def main():
    """Main download function."""
    parser = argparse.ArgumentParser(
        description="Download Zenodo Black Ice Dataset"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Data directory (default: data)"
    )
    parser.add_argument(
        "--no-extract",
        action="store_true",
        help="Download only, don't extract"
    )
    parser.add_argument(
        "--keep-zip",
        action="store_true",
        help="Keep ZIP files after extraction"
    )

    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / args.data_dir
    raw_dir = data_dir / "raw"

    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Zenodo Black Ice Dataset Downloader")
    print("=" * 60)
    print(f"Record ID: {ZENODO_RECORD_ID}")
    print(f"Destination: {raw_dir}")
    print(f"Total size: ~435 MB")
    print()

    # Download files
    success_count = 0
    for filename, size_mb, description in DATASET_FILES:
        print(f"\n📦 {filename} ({size_mb} MB) - {description}")
        print("-" * 60)

        url = f"{BASE_URL}/{filename}"
        destination = raw_dir / filename

        if download_file(url, destination, description):
            success_count += 1

            # Extract if requested
            if not args.no_extract:
                if extract_zip(destination, raw_dir):
                    # Remove ZIP if requested
                    if not args.keep_zip:
                        print(f"Removing {filename}...")
                        destination.unlink()

    # Summary
    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)
    print(f"Downloaded: {success_count}/{len(DATASET_FILES)} files")

    if success_count == len(DATASET_FILES):
        # Verify extraction
        if not args.no_extract:
            success, missing = verify_download(data_dir)
            if success:
                print("✓ All datasets downloaded and extracted successfully!")
                print("\nDataset structure:")
                print(f"  {raw_dir}/")
                print("  ├── white/     (413 images)")
                print("  ├── black/     (814 images)")
                print("  └── OD/        (1,624 images)")
                print("\nNext steps:")
                print("  1. python src/data/convert.py  # Convert COCO to YOLO format")
                print("  2. python src/data/split.py    # Create train/val/test splits")
            else:
                print("⚠ Warning: Some datasets may not have extracted properly:")
                for item in missing:
                    print(f"  - {item}")
        else:
            print("✓ All files downloaded successfully!")
            print(f"Run with --no-extract=false to extract the ZIP files")
    else:
        print("⚠ Some downloads failed. Please check your connection and try again.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
