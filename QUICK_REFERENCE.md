# Black Ice Detection - Quick Reference

## 🚀 One-Command Summary

```bash
# Complete workflow
pip install -r requirements.txt && \
python src/data/convert_roboflow.py && \
python src/training/train.py --device mps && \
streamlit run src/ui/dashboard.py
```

---

## 📝 Essential Commands

### Setup
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### Data
```bash
python src/data/download.py                    # Download dataset
python src/data/convert_roboflow.py            # Convert to YOLO
```

### Training
```bash
python src/training/train.py --device mps      # Mac
python src/training/train.py --device cuda     # NVIDIA
python src/training/train.py --device cpu      # CPU
```

### Evaluation
```bash
python src/training/evaluate.py --model models/checkpoints/black_ice/weights/best.pt --device mps
```

### Dashboard
```bash
streamlit run src/ui/dashboard.py
```

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| `GETTING_STARTED.md` | Tutorial for beginners |
| `IMPROVEMENTS.md` | 50+ enhancement ideas |
| `IMPLEMENTATION_PLAN.md` | 12-week detailed roadmap |
| `PROJECT_SUMMARY.md` | Complete project overview |
| `PLAN.md` | Original detailed plan |

---

## 🎯 Quick Wins (Start Here!)

1. **Run Dashboard** - See the system in action
2. **Add Audio Alerts** - 4 hours, high impact
3. **Temporal Smoothing** - 6 hours, reduces flicker
4. **Write Tests** - 8 hours, ensures reliability

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "externally-managed-environment" | Use venv: `python3 -m venv venv` |
| GPU shows "0G" | Use `--device mps` (Mac) or `--device cuda` (NVIDIA) |
| Dashboard won't start | Check model path exists |
| Low accuracy | Train longer or use larger model |

---

## 📊 Model Sizes

| Model | Command | Best For |
|-------|---------|----------|
| Nano | `--model yolov8n.pt` | Edge devices |
| Small | `--model yolov8s.pt` | **Recommended** |
| Medium | `--model yolov8m.pt` | Desktop GPU |

---

## ⚡ Performance Tips

- **Mac:** Use `--device mps`
- **NVIDIA:** Use `--device cuda` + TensorRT
- **CPU:** Reduce `--batch 8` and `--imgsz 416`
- **Speed:** Use yolov8n.pt
- **Accuracy:** Use yolov8m.pt or yolov8l.pt

---

## 🎨 Dashboard Tips

1. **Start with webcam** - Test camera source 0
2. **Adjust confidence** - Start at 0.5, lower if too few detections
3. **Check FPS** - Should be >10 FPS on decent hardware
4. **Save detections** - Enable logging in config

---

## 📈 Next Steps

1. ✅ Train baseline model
2. ✅ Run dashboard
3. 📝 Read IMPROVEMENTS.md
4. 🛠️ Pick a feature to implement
5. 🚀 Deploy to vehicle

---

**Need help? Check GETTING_STARTED.md for detailed instructions!**
