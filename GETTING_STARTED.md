# Getting Started with Black Ice Detection

This guide will help you get started with the black ice detection system.

## Quick Start

### 1. Installation

```bash
# Clone the repository (or cd into existing directory)
cd black-ice-detection

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Note: If you get "externally-managed-environment" error,
# make sure you're in the virtual environment (you should see "(venv)" in your prompt)
```

### 2. Download Dataset

Download the Zenodo black ice dataset (~435 MB):

```bash
python src/data/download.py
```

This will download and extract:
- White dataset: 413 images (indoor, white background)
- Black dataset: 814 images (indoor, black background)
- Outdoor dataset: 1,624 images (real-world conditions)

**Total: 2,851 annotated images**

### 3. Prepare Data

The Zenodo dataset comes in Roboflow format with pre-split train/valid/test sets.
Convert COCO format annotations to YOLO format:

```bash
python src/data/convert_roboflow.py
```

This will:
- Convert all three datasets (white, black, OD)
- Process existing train/valid/test splits
- Create the data.yaml configuration file
- Organize images and labels for YOLO training

**Note:** The dataset is already split, so you don't need to run `split.py`!

### 4. Train Model

Train YOLOv8 model:

```bash
# For Mac (Apple Silicon) - Use MPS for GPU acceleration
python src/training/train.py --device mps

# For Linux/Windows with NVIDIA GPU
python src/training/train.py --device cuda

# CPU-only training (slower)
python src/training/train.py --device cpu

# With custom config
python src/training/train.py --config configs/model.yaml --device mps

# Different model sizes
python src/training/train.py --model yolov8n.pt --device mps  # Nano (fastest)
python src/training/train.py --model yolov8s.pt --device mps  # Small (balanced)
python src/training/train.py --model yolov8m.pt --device mps  # Medium (accurate)
```

Training will save checkpoints to `models/checkpoints/black_ice/`.

### 5. Evaluate Model

```bash
# For Mac (Apple Silicon)
python src/training/evaluate.py \
  --model models/checkpoints/black_ice/weights/best.pt \
  --device mps

# For NVIDIA GPU
python src/training/evaluate.py \
  --model models/checkpoints/black_ice/weights/best.pt \
  --device cuda

# For CPU
python src/training/evaluate.py \
  --model models/checkpoints/black_ice/weights/best.pt \
  --device cpu
```

### 6. Export Model

Export to ONNX for deployment:

```bash
python src/training/export.py \
  --model models/checkpoints/black_ice/weights/best.pt \
  --format onnx
```

### 7. Run Real-Time Detection Dashboard

Launch the Streamlit dashboard for real-time detection:

```bash
streamlit run src/ui/dashboard.py
```

The dashboard provides:
- **Live camera feed** with detection overlays
- **Real-time statistics** (FPS, detections, confidence)
- **Alert system** with severity levels (low/medium/high)
- **Detection history** and logging
- **Configurable settings** (model, device, thresholds)

**Dashboard Controls:**
- Select camera source (webcam, video file, IP camera)
- Adjust confidence threshold
- Choose device (CPU/MPS/CUDA)
- Enable/disable alerts
- Start/stop detection

**Note:** Make sure your trained model exists before running the dashboard.

## Model Variants

| Model | Size | Speed | Use Case |
|-------|------|-------|----------|
| yolov8n | ~6MB | Fastest | Edge devices (Raspberry Pi) |
| yolov8s | ~22MB | Fast | Laptops, balanced performance |
| yolov8m | ~52MB | Moderate | Desktop with GPU |
| yolov8l | ~87MB | Slow | High accuracy needed |
| yolov8x | ~136MB | Slowest | Maximum accuracy |

## Configuration

### Model Configuration

Edit `configs/model.yaml` to adjust:
- Training hyperparameters (epochs, batch size, learning rate)
- Augmentation settings
- Inference thresholds

### Alert Configuration

Edit `configs/alerts.yaml` to adjust:
- Severity thresholds (low/medium/high)
- Audio alert settings
- Visual alert appearance
- Temporal smoothing parameters

## Testing Single Images

Test the detector on a single image:

```bash
python src/inference/detector.py \
  models/checkpoints/black_ice/weights/best.pt \
  path/to/test/image.jpg
```

## Common Issues

### Externally Managed Environment Error

If you see this error when running `pip install`:
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # You should see (venv) in your prompt

# Verify you're using the venv pip
which pip  # Should show: /path/to/black-ice-detection/venv/bin/pip

# If still having issues, recreate the venv
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dataset Structure Issues

The Zenodo dataset uses Roboflow format:
- Use `convert_roboflow.py` instead of `convert.py`
- Splits are already in train/valid/test folders
- Each dataset has `_annotations.coco.json` in subdirectories

### GPU Not Being Used (Shows "0G")

If training shows "0G" for GPU memory:

**For Mac (Apple Silicon M1/M2/M3):**
```bash
# Use MPS instead of CUDA
python src/training/train.py --device mps
```

**For NVIDIA GPU:**
```bash
# Make sure CUDA is available
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# If CUDA is available, use:
python src/training/train.py --device cuda
```

### CUDA/MPS Out of Memory

Reduce batch size in training:
```bash
python src/training/train.py --batch 8 --device mps
```

### Slow Training

- Use smaller model (yolov8n)
- Enable image caching: `--cache`
- Reduce image size: `--imgsz 416`

### Low Accuracy

- Train for more epochs: `--epochs 150`
- Use larger model (yolov8m)
- Increase augmentation (edit `configs/augmentation.yaml`)

## Next Steps

1. **Data Exploration**: Check `notebooks/01_data_exploration.ipynb` to analyze the dataset
2. **Custom Training**: Modify `configs/model.yaml` for your specific needs
3. **Real-time Detection**: Implement the dashboard for live camera feed
4. **Deployment**: Export to ONNX/TensorRT for edge devices

## Project Structure

```
black-ice-detection/
├── data/                       # Dataset files
│   ├── raw/                   # Downloaded Roboflow data
│   │   ├── white/train/       # 413 images + annotations
│   │   ├── black/train/       # 814 images + annotations
│   │   └── OD/                # 1,624 images (train/valid/test)
│   └── processed/             # YOLO format
│       ├── images/            # Organized by split and dataset
│       ├── labels/            # Corresponding YOLO labels
│       └── data.yaml          # YOLO config
├── models/                    # Trained models
│   ├── checkpoints/          # Training runs
│   └── exported/             # ONNX/other formats
├── src/                      # Source code
│   ├── data/
│   │   ├── download.py       # Dataset downloader
│   │   ├── convert_roboflow.py  # Roboflow→YOLO converter
│   │   └── split.py          # (Not needed - already split)
│   ├── training/
│   │   ├── train.py          # Training script
│   │   ├── evaluate.py       # Evaluation
│   │   └── export.py         # Export to ONNX
│   ├── inference/
│   │   └── detector.py       # Detection module
│   └── utils/               # Utilities
└── configs/                 # Configuration files
```

## Resources

- **Dataset**: https://zenodo.org/records/10428765
- **Ultralytics YOLOv8**: https://docs.ultralytics.com/
- **Full Plan**: See [PLAN.md](PLAN.md)

## Support

For issues or questions, refer to the [PLAN.md](PLAN.md) for detailed implementation guidance.
