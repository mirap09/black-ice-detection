# Black Ice Detection System

Real-time black ice detection for vehicle-mounted cameras using YOLOv8.

## Overview

This system detects black ice on road surfaces using deep learning trained on the [Zenodo Black Ice Dataset](https://zenodo.org/records/10428765). It provides real-time alerts through audio and visual warnings.

## Features

- Real-time black ice detection using YOLOv8
- Support for USB cameras, IP cameras, and video files
- Audio and visual alert system with severity levels
- Live dashboard with detection statistics
- Detection logging for review and analysis
- Optimized for edge deployment (Raspberry Pi, Jetson Nano)

## Installation

### Prerequisites

- Python 3.11 or higher
- GPU with CUDA support (optional, for faster inference)
- Webcam or IP camera

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd black-ice-detection
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Download Dataset

```bash
python src/data/download.py
```

### 2. Prepare Data

```bash
python src/data/convert_roboflow.py
```

### 3. Train Model

```bash
python src/training/train.py --config configs/model.yaml
```

### 4. Run Detection

```bash
streamlit run src/ui/dashboard.py
```

## Project Structure

```
black-ice-detection/
├── data/               # Dataset files
├── models/             # Trained models
├── src/               # Source code
├── notebooks/         # Jupyter notebooks
├── configs/           # Configuration files
└── tests/             # Unit tests
```

## Dataset

The system uses the Zenodo Black Ice Dataset (Roboflow format):
- 2,851 annotated images (already split into train/valid/test)
- COCO format annotations with YOLO conversion
- Indoor (white/black) and outdoor conditions
- Total size: ~435MB

Dataset breakdown:
- White: 413 images (indoor, white background)
- Black: 814 images (indoor, dark background)
- Outdoor (OD): 1,624 images (real-world conditions)

## Model Performance

| Metric | Value |
|--------|-------|
| mAP@0.5 | TBD |
| Precision | TBD |
| Recall | TBD |
| FPS (GPU) | TBD |
| FPS (CPU) | TBD |

## Documentation

📚 **Complete Documentation Suite:**

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Essential commands and troubleshooting
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Step-by-step tutorial
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview
- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - 50+ enhancement ideas
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - 12-week roadmap
- **[PLAN.md](PLAN.md)** - Original detailed plan

## Features

✅ **Implemented:**
- Real-time black ice detection using YOLOv8
- Streamlit dashboard with live camera feed
- Alert severity classification (low/medium/high)
- Detection logging and statistics
- Multi-device support (CPU/MPS/CUDA)
- Configurable thresholds and settings

🚧 **Coming Soon:**
- Audio alert system
- Temporal smoothing
- Vehicle integration (GPS, speed)
- Cloud platform
- Mobile apps

## License

MIT License

## Citation

If you use this system, please cite the original dataset:
```
Zenodo Black Ice Dataset
https://zenodo.org/records/10428765
```

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
