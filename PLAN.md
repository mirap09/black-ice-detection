# Black Ice Detection System - Implementation Plan

## Project Overview

**Objective:** Build a real-time black ice detection system for vehicle-mounted cameras using deep learning, trained on the Zenodo black ice dataset.

**Dataset Source:** https://zenodo.org/records/10428765
- White Dataset: 413 images (indoor, white background)
- Black Dataset: 814 images (indoor, dark background)
- Outdoor Dataset: 1,624 images (real-world conditions)
- **Total: 2,851 images** with COCO-format annotations

---

## Phase 1: Project Setup & Data Preparation

### 1.1 Environment Setup
- [ ] Create Python virtual environment (3.11+)
- [ ] Install core dependencies:
  - PyTorch 2.x with CUDA support
  - Ultralytics (YOLOv8)
  - OpenCV
  - Albumentations (augmentation)
  - Streamlit (UI)
- [ ] Set up project directory structure
- [ ] Initialize git repository

### 1.2 Dataset Download
- [ ] Create download script for Zenodo dataset
- [ ] Download all three ZIP files:
  - white.zip (68.3 MB)
  - black.zip (199.2 MB)
  - OD.zip (167.4 MB)
- [ ] Extract and organize raw data

### 1.3 Data Exploration
- [ ] Analyze annotation distribution
- [ ] Visualize sample images with bounding boxes
- [ ] Calculate class statistics:
  - Bounding box sizes
  - Aspect ratios
  - Ice coverage percentages
- [ ] Identify potential data quality issues
- [ ] Document dataset characteristics

### 1.4 Data Conversion & Preprocessing
- [ ] Convert COCO annotations to YOLO format
- [ ] Validate converted annotations
- [ ] Create unified dataset structure
- [ ] Generate train/val/test splits (70/20/10)
- [ ] Stratify by source dataset (white/black/outdoor)

### 1.5 Data Augmentation Strategy
- [ ] Implement augmentation pipeline:
  - Geometric: rotation, flipping, scaling
  - Photometric: brightness, contrast, saturation
  - Weather simulation: rain, fog, snow effects
  - Motion blur (simulating vehicle movement)
  - Noise injection
- [ ] Validate augmented samples visually

---

## Phase 2: Model Development

### 2.1 Baseline Model (YOLOv8)
- [ ] Configure YOLOv8-small for single-class detection
- [ ] Set up training configuration:
  - Learning rate schedule
  - Batch size optimization
  - Early stopping criteria
- [ ] Train baseline model
- [ ] Log training metrics (loss, mAP, precision, recall)
- [ ] Evaluate on validation set

### 2.2 Model Experimentation
- [ ] Experiment with YOLOv8 variants:
  - YOLOv8-nano (edge deployment)
  - YOLOv8-medium (higher accuracy)
- [ ] Try alternative architectures if needed:
  - RT-DETR (transformer-based)
  - YOLOv11 (latest architecture)
- [ ] Compare performance metrics

### 2.3 Hyperparameter Tuning
- [ ] Tune key parameters:
  - Image size (640 vs 1280)
  - Confidence threshold
  - IoU threshold for NMS
  - Augmentation intensity
- [ ] Document best configuration

### 2.4 Model Evaluation
- [ ] Generate comprehensive metrics:
  - mAP@0.5, mAP@0.5:0.95
  - Precision-Recall curves
  - Confusion matrix
  - F1 score
- [ ] Analyze failure cases:
  - False positives (wet road misclassified)
  - False negatives (missed ice patches)
- [ ] Test on each dataset subset separately
- [ ] Evaluate inference speed (FPS)

### 2.5 Model Export
- [ ] Export best model to ONNX format
- [ ] Optimize for deployment:
  - TensorRT (NVIDIA GPUs)
  - OpenVINO (Intel)
  - CoreML (Apple)
- [ ] Validate exported model accuracy

---

## Phase 3: Inference Pipeline

### 3.1 Camera Interface Module
- [ ] Implement camera capture class:
  - USB camera support
  - IP camera / RTSP streams
  - Video file input (testing)
- [ ] Add frame buffering for smooth processing
- [ ] Handle camera disconnection gracefully

### 3.2 Detection Module
- [ ] Create detector class wrapping YOLO
- [ ] Implement preprocessing pipeline:
  - Resize to model input size
  - Normalize pixel values
  - Handle different aspect ratios
- [ ] Add post-processing:
  - Non-maximum suppression
  - Confidence filtering
  - Bounding box scaling to original size

### 3.3 Tracking & Temporal Smoothing
- [ ] Implement simple object tracking (optional):
  - Track ice patches across frames
  - Reduce flickering detections
- [ ] Add temporal smoothing:
  - Moving average confidence
  - Persistence threshold (N consecutive frames)

### 3.4 Performance Optimization
- [ ] Profile inference pipeline
- [ ] Implement batched inference (if beneficial)
- [ ] Add GPU memory management
- [ ] Optimize for target hardware

---

## Phase 4: Alert System & User Interface

### 4.1 Alert Classification
- [ ] Define severity levels:
  - **LOW**: Small ice patch, low confidence
  - **MEDIUM**: Moderate coverage, high confidence
  - **HIGH**: Large area or imminent danger
- [ ] Implement alert logic based on:
  - Detection confidence
  - Bounding box size / coverage
  - Proximity (if depth estimation available)

### 4.2 Audio Alerts
- [ ] Create audio alert system:
  - Different tones for severity levels
  - Text-to-speech warnings (optional)
- [ ] Add cooldown to prevent alert fatigue
- [ ] Make alerts configurable

### 4.3 Visual Alerts
- [ ] Implement on-screen warnings:
  - Colored border/overlay based on severity
  - Flashing indicators for high severity
- [ ] Draw bounding boxes on detected ice
- [ ] Show confidence scores

### 4.4 Dashboard UI (Streamlit)
- [ ] Create main dashboard layout:
  - Live camera feed with detections
  - Current alert status
  - Detection statistics
- [ ] Add controls:
  - Start/stop detection
  - Adjust confidence threshold
  - Toggle audio alerts
- [ ] Implement detection log viewer:
  - Timestamp, confidence, severity
  - Captured frame thumbnails
- [ ] Add settings panel:
  - Camera selection
  - Model selection
  - Alert preferences

### 4.5 Logging & Recording
- [ ] Implement detection logging:
  - SQLite database for detection events
  - Save frames with detections
- [ ] Add session recording (optional):
  - Record video with overlay
  - Export detection timeline

---

## Phase 5: Testing & Validation

### 5.1 Unit Testing
- [ ] Test data conversion functions
- [ ] Test detector class
- [ ] Test alert logic
- [ ] Test camera interface

### 5.2 Integration Testing
- [ ] Test full pipeline end-to-end
- [ ] Test with recorded videos
- [ ] Test edge cases:
  - No detections
  - Multiple detections
  - Rapid scene changes

### 5.3 Performance Testing
- [ ] Measure end-to-end latency
- [ ] Profile memory usage
- [ ] Test sustained operation (1+ hour)
- [ ] Benchmark on target hardware:
  - Laptop with GPU
  - Laptop CPU-only
  - Edge device (if applicable)

### 5.4 Accuracy Validation
- [ ] Test on held-out test set
- [ ] Cross-validate across dataset sources
- [ ] Analyze real-world performance gaps

---

## Phase 6: Documentation & Deployment

### 6.1 Documentation
- [ ] Write README with:
  - Project overview
  - Installation instructions
  - Usage guide
  - Model performance summary
- [ ] Document API/module interfaces
- [ ] Create troubleshooting guide

### 6.2 Deployment Packaging
- [ ] Create requirements.txt / pyproject.toml
- [ ] Add Docker support (optional)
- [ ] Create standalone executable (optional):
  - PyInstaller or similar

### 6.3 Future Improvements (Backlog)
- [ ] Multi-camera support
- [ ] Cloud logging / fleet management
- [ ] Model retraining pipeline
- [ ] Integration with vehicle CAN bus
- [ ] GPS-tagged detection mapping

---

## Project Structure

```
black-ice-detection/
├── data/
│   ├── raw/                      # Original downloaded data
│   │   ├── white/
│   │   ├── black/
│   │   └── outdoor/
│   ├── processed/                # YOLO format dataset
│   │   ├── images/
│   │   │   ├── train/
│   │   │   ├── val/
│   │   │   └── test/
│   │   └── labels/
│   │       ├── train/
│   │       ├── val/
│   │       └── test/
│   └── data.yaml                 # Dataset configuration
├── models/
│   ├── checkpoints/              # Training checkpoints
│   └── exported/                 # Production models (ONNX)
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download.py           # Dataset downloader
│   │   ├── convert.py            # COCO to YOLO converter
│   │   ├── augment.py            # Augmentation pipeline
│   │   └── split.py              # Train/val/test splitting
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py              # Training script
│   │   ├── evaluate.py           # Evaluation metrics
│   │   └── export.py             # Model export
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── detector.py           # YOLO detector wrapper
│   │   ├── tracker.py            # Object tracking
│   │   └── pipeline.py           # Full inference pipeline
│   ├── alerts/
│   │   ├── __init__.py
│   │   ├── classifier.py         # Alert severity classification
│   │   ├── audio.py              # Audio alert system
│   │   └── visual.py             # Visual alert overlays
│   ├── ui/
│   │   ├── __init__.py
│   │   └── dashboard.py          # Streamlit dashboard
│   └── utils/
│       ├── __init__.py
│       ├── camera.py             # Camera interface
│       ├── logging.py            # Detection logging
│       └── config.py             # Configuration management
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_model_training.ipynb
│   └── 03_evaluation.ipynb
├── configs/
│   ├── model.yaml                # Model hyperparameters
│   ├── augmentation.yaml         # Augmentation settings
│   └── alerts.yaml               # Alert thresholds
├── tests/
│   ├── test_data.py
│   ├── test_detector.py
│   └── test_alerts.py
├── assets/
│   └── sounds/                   # Alert sound files
├── logs/                         # Detection logs
├── PLAN.md                       # This file
├── README.md
├── requirements.txt
├── pyproject.toml
└── .gitignore
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.11+ | Core development |
| Deep Learning | PyTorch 2.x | Model training backend |
| Object Detection | Ultralytics YOLOv8 | Primary detection model |
| Image Processing | OpenCV | Camera capture, preprocessing |
| Augmentation | Albumentations | Training data augmentation |
| UI Framework | Streamlit | Dashboard interface |
| Database | SQLite | Detection logging |
| Visualization | Matplotlib, Seaborn | Training metrics, analysis |
| Export | ONNX Runtime | Model deployment |

---

## Timeline Estimate

| Phase | Tasks | Dependencies |
|-------|-------|--------------|
| Phase 1 | Setup & Data Preparation | None |
| Phase 2 | Model Development | Phase 1 |
| Phase 3 | Inference Pipeline | Phase 2 |
| Phase 4 | Alert System & UI | Phase 3 |
| Phase 5 | Testing & Validation | Phase 4 |
| Phase 6 | Documentation & Deployment | Phase 5 |

---

## Success Criteria

- [ ] Model achieves mAP@0.5 > 0.70 on test set
- [ ] Inference speed > 20 FPS on laptop with GPU
- [ ] Inference speed > 5 FPS on CPU-only
- [ ] End-to-end latency < 200ms
- [ ] False positive rate < 10%
- [ ] System runs stable for 1+ hour continuous operation

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Small dataset limits generalization | High | Aggressive augmentation, transfer learning |
| Wet road vs ice confusion | High | Careful threshold tuning, temporal smoothing |
| Real-world conditions differ from dataset | Medium | Test with diverse video sources, plan for retraining |
| Edge device performance insufficient | Medium | Use smaller model variants, optimize inference |
| Camera quality varies | Low | Test with multiple camera types, add preprocessing |

---

## Next Steps

1. **Immediate:** Set up project structure and environment
2. **This week:** Download dataset and complete data exploration
3. **Next:** Train baseline YOLOv8 model and evaluate
