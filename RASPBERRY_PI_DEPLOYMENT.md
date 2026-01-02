# Raspberry Pi 5 Deployment Guide - Vehicle-Mounted Black Ice Detection

## Overview

This guide details how to deploy the black ice detection system on a Raspberry Pi 5 for vehicle mounting with LED and buzzer alerts.

---

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Pi Camera      │────▶│  Raspberry Pi 5  │────▶│  LED Indicators │
│  (CSI/USB)      │     │  Detection Core  │     │  + Buzzer       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Optional:       │
                        │  - GPS Module    │
                        │  - Temperature   │
                        │  - SD Card Log   │
                        └──────────────────┘
```

---

## Hardware Requirements

### Essential Components

| Component | Specification | Estimated Cost | Notes |
|-----------|--------------|----------------|-------|
| **Raspberry Pi 5** | 4GB or 8GB RAM | $60-80 | 8GB recommended for better performance |
| **Camera** | Pi Camera Module 3 or USB webcam | $25-50 | Wide angle lens preferred |
| **Power Supply** | 5V 5A USB-C PD | $12-15 | Vehicle 12V to USB-C adapter |
| **LED Indicators** | RGB LED (common cathode) | $2-5 | Or 3 separate LEDs (green/yellow/red) |
| **Buzzer** | Active buzzer 5V | $2-3 | Piezo buzzer for alerts |
| **MicroSD Card** | 64GB+ Class 10/U3 | $10-15 | For OS and logging |
| **Case** | Weatherproof enclosure | $15-25 | Must fit Pi + camera |
| **Mounting** | Dashboard mount/suction cup | $10-20 | Stable camera positioning |

**Total: ~$136-213**

### Optional Components

| Component | Purpose | Cost |
|-----------|---------|------|
| GPS Module (USB) | Location tagging | $20-40 |
| Temperature Sensor (DS18B20) | Contextual data | $5-10 |
| Real-Time Clock (RTC) | Accurate timestamps | $5-10 |
| Cooling Fan | Prevent thermal throttling | $5-10 |
| External SSD | Faster storage | $30-50 |

---

## Wiring Diagram

### LED + Buzzer Connection to GPIO

```
Raspberry Pi 5 GPIO Pinout:
┌─────────────────────────┐
│  3.3V  [1]  [2]  5V     │
│  GPIO2 [3]  [4]  5V     │
│  GPIO3 [5]  [6]  GND    │
│  GPIO4 [7]  [8]  GPIO14 │
│  GND   [9]  [10] GPIO15 │
│  GPIO17[11] [12] GPIO18 │ ← LED Red
│  GPIO27[13] [14] GND    │
│  GPIO22[15] [16] GPIO23 │ ← LED Yellow
│  3.3V [17] [18] GPIO24 │ ← LED Green
│  ...                    │
│  GPIO12[32] [33] GPIO13 │ ← Buzzer
│  GND  [34] ...          │
└─────────────────────────┘
```

### Wiring Instructions

**LED Setup (Common Cathode RGB or 3 LEDs):**
```
LED Red (GPIO 18):
  GPIO18 → 220Ω Resistor → LED Anode (+)
  LED Cathode (-) → GND

LED Yellow (GPIO 23):
  GPIO23 → 220Ω Resistor → LED Anode (+)
  LED Cathode (-) → GND

LED Green (GPIO 24):
  GPIO24 → 220Ω Resistor → LED Anode (+)
  LED Cathode (-) → GND
```

**Buzzer Setup:**
```
Active Buzzer (GPIO 13):
  GPIO13 → Buzzer Positive (+)
  Buzzer Negative (-) → GND
```

### Circuit Diagram
```
        Pi GPIO                     Components

GPIO18 ──[220Ω]──┬──>|── GND     Red LED (High Severity)

GPIO23 ──[220Ω]──┬──>|── GND     Yellow LED (Medium Severity)

GPIO24 ──[220Ω]──┬──>|── GND     Green LED (Low Severity / No Ice)

GPIO13 ──────────┬──[Buzzer]── GND     Active Buzzer
```

---

## Software Setup

### Phase 1: Raspberry Pi OS Installation

1. **Flash Raspberry Pi OS (64-bit)**
```bash
# Download Raspberry Pi Imager
# https://www.raspberrypi.com/software/

# Flash to microSD:
# - OS: Raspberry Pi OS (64-bit) Lite or Desktop
# - Configure: hostname, SSH, WiFi
```

2. **Initial Boot & Update**
```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Update system
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y git python3-pip python3-venv
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y python3-picamera2  # For Pi Camera
```

### Phase 2: Hardware Setup

3. **Enable Camera**
```bash
# For Pi Camera Module
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable

# Reboot
sudo reboot
```

4. **Test Camera**
```bash
# For Pi Camera Module
rpicam-hello

# For USB webcam
v4l2-ctl --list-devices
```

5. **Enable GPIO**
```bash
# Install GPIO library
pip3 install RPi.GPIO lgpio gpiod

# Test GPIO (optional)
python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"
```

### Phase 3: Project Installation

6. **Clone Repository**
```bash
cd ~
git clone https://github.com/mirap09/black-ice-detection.git
cd black-ice-detection
```

7. **Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

8. **Install Dependencies (Optimized for Pi)**
```bash
# Install PyTorch (ARM64 optimized)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
pip3 install opencv-python-headless  # Headless version for Pi
pip3 install ultralytics
pip3 install numpy pandas pyyaml tqdm requests
pip3 install RPi.GPIO  # GPIO control

# Skip heavy dependencies for edge deployment
# (no matplotlib, seaborn, streamlit on edge)
```

9. **Download Pre-trained Model**
```bash
# Transfer your trained model from development machine
scp models/checkpoints/black_ice/weights/best.pt pi@raspberrypi.local:~/black-ice-detection/models/

# Or train with YOLOv8-nano for Pi
# python src/training/train.py --model yolov8n.pt --device cpu --epochs 50
```

### Phase 4: Hardware Alert System

10. **Create Hardware Alert Module**

Create `src/alerts/hardware.py`:
```python
"""
Hardware alert system for Raspberry Pi GPIO.
Controls LED indicators and buzzer based on detection severity.
"""

import time
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO not available - running in simulation mode")
    GPIO = None


class HardwareAlerts:
    """Control LEDs and buzzer via GPIO."""

    def __init__(self, led_pins=None, buzzer_pin=None):
        """
        Initialize GPIO pins for alerts.

        Args:
            led_pins: Dict with 'green', 'yellow', 'red' GPIO pins
            buzzer_pin: GPIO pin for buzzer
        """
        self.led_pins = led_pins or {
            'green': 24,   # GPIO 24 - No ice / Safe
            'yellow': 23,  # GPIO 23 - Medium severity
            'red': 18      # GPIO 18 - High severity
        }
        self.buzzer_pin = buzzer_pin or 13  # GPIO 13

        if GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Setup LED pins
            for pin in self.led_pins.values():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)

            # Setup buzzer pin
            GPIO.setup(self.buzzer_pin, GPIO.OUT)
            GPIO.output(self.buzzer_pin, GPIO.LOW)

            print("✓ GPIO initialized")

    def set_severity(self, severity):
        """
        Set LED based on severity level.

        Args:
            severity: 'none', 'low', 'medium', 'high'
        """
        if not GPIO:
            print(f"[SIM] Severity: {severity}")
            return

        # Turn off all LEDs
        for pin in self.led_pins.values():
            GPIO.output(pin, GPIO.LOW)

        # Turn on appropriate LED
        if severity == 'none' or severity == 'low':
            GPIO.output(self.led_pins['green'], GPIO.HIGH)
        elif severity == 'medium':
            GPIO.output(self.led_pins['yellow'], GPIO.HIGH)
        elif severity == 'high':
            GPIO.output(self.led_pins['red'], GPIO.HIGH)

    def trigger_buzzer(self, severity, duration=0.5):
        """
        Trigger buzzer based on severity.

        Args:
            severity: 'medium' or 'high'
            duration: Beep duration in seconds
        """
        if not GPIO or severity not in ['medium', 'high']:
            return

        # Different patterns for different severities
        if severity == 'medium':
            # Single beep
            GPIO.output(self.buzzer_pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.buzzer_pin, GPIO.LOW)

        elif severity == 'high':
            # Triple beep
            for _ in range(3):
                GPIO.output(self.buzzer_pin, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(self.buzzer_pin, GPIO.LOW)
                time.sleep(0.1)

    def flash_led(self, color, times=3, interval=0.2):
        """Flash a specific LED color."""
        if not GPIO or color not in self.led_pins:
            return

        pin = self.led_pins[color]
        for _ in range(times):
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(interval)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(interval)

    def cleanup(self):
        """Clean up GPIO on exit."""
        if GPIO:
            GPIO.cleanup()
            print("✓ GPIO cleaned up")
```

11. **Create Headless Detection Script**

Create `src/inference/pi_detector.py`:
```python
"""
Headless detection script for Raspberry Pi deployment.
Runs detection without GUI, controls hardware alerts.
"""

import sys
import time
from pathlib import Path
import cv2

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.inference.detector import BlackIceDetector
from src.alerts.classifier import AlertClassifier
from src.alerts.hardware import HardwareAlerts
from src.utils.camera import Camera
from src.utils.logging import DetectionLogger


def main():
    # Configuration
    MODEL_PATH = "models/best.pt"  # Or yolov8n.pt
    CAMERA_SOURCE = 0  # USB camera or 0 for Pi Camera
    CONF_THRESHOLD = 0.5
    LOG_PATH = "logs/detections.db"

    print("=" * 60)
    print("Black Ice Detection - Raspberry Pi Mode")
    print("=" * 60)

    # Initialize components
    print("\n1. Loading detector...")
    detector = BlackIceDetector(
        model_path=MODEL_PATH,
        conf_threshold=CONF_THRESHOLD,
        device="cpu"
    )

    print("2. Initializing alert classifier...")
    alert_classifier = AlertClassifier()

    print("3. Initializing hardware alerts...")
    hardware = HardwareAlerts()

    print("4. Opening camera...")
    camera = Camera(source=CAMERA_SOURCE)
    if not camera.open():
        print("✗ Failed to open camera")
        return 1

    print("5. Initializing logger...")
    logger = DetectionLogger(LOG_PATH)
    session_id = logger.start_session({'device': 'raspberry_pi_5'})

    print("\n✓ System ready! Starting detection...")
    print("Press Ctrl+C to stop\n")

    # Start with green LED (no ice detected)
    hardware.set_severity('none')

    frame_count = 0
    detection_count = 0
    last_buzzer_time = 0
    BUZZER_COOLDOWN = 5  # seconds

    try:
        while True:
            # Read frame
            ret, frame = camera.read()
            if not ret:
                print("✗ Failed to read frame")
                break

            frame_count += 1

            # Detect (every frame)
            detections, inference_time = detector.detect_with_timing(frame)

            if detections:
                detection_count += len(detections)

                # Classify severity
                severity = alert_classifier.get_highest_severity(detections)

                # Log detection
                for det in detections:
                    logger.log_detection(
                        confidence=det['confidence'],
                        bbox=det['bbox'],
                        severity=severity,
                        frame=None  # Don't save frames on Pi (save space)
                    )

                # Update LED
                hardware.set_severity(severity)

                # Trigger buzzer (with cooldown)
                current_time = time.time()
                if (severity in ['medium', 'high'] and
                    current_time - last_buzzer_time > BUZZER_COOLDOWN):
                    hardware.trigger_buzzer(severity)
                    last_buzzer_time = current_time

                # Console output
                max_conf = max(d['confidence'] for d in detections)
                print(f"[{frame_count:06d}] ⚠️  ICE DETECTED | "
                      f"Severity: {severity.upper()} | "
                      f"Confidence: {max_conf:.2%} | "
                      f"Count: {len(detections)} | "
                      f"Time: {inference_time:.1f}ms")

            else:
                # No ice detected - green LED
                hardware.set_severity('none')

                # Periodic status (every 100 frames)
                if frame_count % 100 == 0:
                    fps = 1000 / inference_time if inference_time > 0 else 0
                    print(f"[{frame_count:06d}] ✓ Clear | "
                          f"FPS: {fps:.1f} | "
                          f"Total detections: {detection_count}")

            # Small delay to prevent overload
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n\n⏹  Stopping detection...")

    finally:
        # Cleanup
        camera.release()
        logger.end_session(session_id)
        hardware.cleanup()

        print(f"\n✓ Session complete")
        print(f"  Frames processed: {frame_count}")
        print(f"  Detections logged: {detection_count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

12. **Test Hardware**
```bash
# Test LEDs and buzzer
python3 << 'EOF'
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Test each LED
for pin, color in [(24, "Green"), (23, "Yellow"), (18, "Red")]:
    GPIO.setup(pin, GPIO.OUT)
    print(f"Testing {color} LED...")
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(pin, GPIO.LOW)

# Test buzzer
GPIO.setup(13, GPIO.OUT)
print("Testing buzzer...")
GPIO.output(13, GPIO.HIGH)
time.sleep(0.5)
GPIO.output(13, GPIO.LOW)

GPIO.cleanup()
print("✓ Hardware test complete")
EOF
```

### Phase 5: Auto-Start Configuration

13. **Create Systemd Service**
```bash
sudo nano /etc/systemd/system/black-ice-detection.service
```

Add:
```ini
[Unit]
Description=Black Ice Detection System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/black-ice-detection
Environment="PATH=/home/pi/black-ice-detection/venv/bin"
ExecStart=/home/pi/black-ice-detection/venv/bin/python3 src/inference/pi_detector.py
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

14. **Enable Auto-Start**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable black-ice-detection.service

# Start service
sudo systemctl start black-ice-detection.service

# Check status
sudo systemctl status black-ice-detection.service

# View logs
journalctl -u black-ice-detection.service -f
```

---

## Performance Optimization for Pi 5

### Model Optimization

1. **Use YOLOv8-nano**
```bash
# Smallest, fastest model
# ~6MB, suitable for edge devices
```

2. **ONNX Runtime (Faster Inference)**
```bash
# Install ONNX Runtime
pip3 install onnxruntime

# Export model to ONNX
python src/training/export.py --model models/best.pt --format onnx

# Use ONNX in detector (modify detector.py to use onnxruntime)
```

3. **INT8 Quantization** (Advanced)
```python
# Reduce model size and increase speed
# 4x smaller, 2-4x faster
# Requires calibration dataset
```

### System Optimization

4. **Reduce Image Resolution**
```python
# In pi_detector.py, resize frames
frame = cv2.resize(frame, (416, 416))  # Instead of 640x640
```

5. **Frame Skipping**
```python
# Process every Nth frame
if frame_count % 2 == 0:  # Process every 2nd frame
    detections = detector.detect(frame)
```

6. **Disable Desktop Environment**
```bash
# Boot to CLI only (saves RAM)
sudo raspi-config
# System Options → Boot / Auto Login → Console

# Or temporarily
sudo systemctl set-default multi-user.target
```

7. **Overclock (Optional)**
```bash
sudo nano /boot/firmware/config.txt

# Add:
# over_voltage=6
# arm_freq=2400

# Reboot
sudo reboot

# Monitor temperature
vcgencmd measure_temp
```

---

## Vehicle Mounting Guide

### Physical Mounting

**Camera Position:**
- Mount on dashboard or windshield
- Angle: 15-30° downward to capture road ahead
- Distance: 2-5 meters ahead view
- Height: Eye level or slightly above

**Pi Enclosure:**
- Use weatherproof case
- Ensure ventilation for cooling
- Secure with Velcro or zip ties
- Keep away from airbag deployment zones

**LED/Buzzer Placement:**
- LEDs: Visible in peripheral vision (dashboard top)
- Buzzer: Audible but not jarring

### Power Management

**12V to USB-C Adapter:**
```
Vehicle 12V → Buck Converter → 5V 5A USB-C → Pi 5
```

**Power Options:**
1. **Cigarette Lighter Adapter** - Easy, removable
2. **Hardwired** - Professional, always on
3. **Power Bank** - Temporary testing

**Auto-Start on Power:**
- Pi boots when power applied
- Systemd service starts automatically
- No manual intervention needed

---

## Testing & Calibration

### Bench Testing

1. **Test in controlled environment**
2. **Use pre-recorded videos of icy roads**
3. **Verify LED/buzzer responses**
4. **Check inference speed (target: >5 FPS)**

### Field Testing

1. **Test in actual vehicle**
2. **Validate mounting stability**
3. **Check camera view angle**
4. **Test in various lighting conditions**
5. **Verify alerts are noticeable while driving**

### Calibration

**Confidence Threshold:**
```python
# Adjust based on false positive rate
# Too many false alarms: Increase to 0.6-0.7
# Missing detections: Decrease to 0.3-0.4
CONF_THRESHOLD = 0.5  # Default
```

**Alert Timing:**
```python
# Adjust buzzer cooldown
BUZZER_COOLDOWN = 3  # More frequent alerts
BUZZER_COOLDOWN = 10  # Less frequent alerts
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Camera not detected | Check cable, enable camera in raspi-config |
| Slow inference (< 2 FPS) | Use yolov8n, reduce resolution, enable overclocking |
| Pi overheating | Add heatsink/fan, reduce overclock |
| LEDs not working | Check wiring, test GPIO with simple script |
| Buzzer too loud | Add potentiometer for volume control |
| False positives | Increase confidence threshold |
| Service won't start | Check logs: `journalctl -xe` |

### Performance Expectations

| Model | Resolution | Pi 5 FPS | Latency |
|-------|-----------|----------|---------|
| YOLOv8n | 416x416 | 8-12 FPS | ~80-120ms |
| YOLOv8n | 640x640 | 5-8 FPS | ~120-200ms |
| YOLOv8s | 416x416 | 4-6 FPS | ~150-250ms |
| YOLOv8s | 640x640 | 2-4 FPS | ~250-500ms |

---

## Maintenance

### Regular Checks

- **Weekly**: Clean camera lens
- **Monthly**: Check SD card space (`df -h`)
- **Quarterly**: Update system packages
- **Annually**: Replace SD card (prevent wear)

### Log Management

```bash
# View recent detections
sqlite3 logs/detections.db "SELECT * FROM detections ORDER BY timestamp DESC LIMIT 10;"

# Clear old logs (keep last 30 days)
python3 << 'EOF'
from src.utils.logging import DetectionLogger
logger = DetectionLogger("logs/detections.db")
deleted = logger.clear_old_detections(days=30)
print(f"Deleted {deleted} old records")
EOF
```

---

## Cost Summary

### Minimum Setup: ~$136
- Pi 5 (4GB): $60
- Pi Camera Module: $25
- Power supply: $15
- LEDs + Buzzer: $5
- MicroSD 64GB: $10
- Case + mounting: $21

### Recommended Setup: ~$213
- Pi 5 (8GB): $80
- Pi Camera Module 3 Wide: $40
- Power supply (vehicle): $15
- LEDs + Buzzer + components: $10
- MicroSD 128GB: $18
- Weatherproof case: $25
- GPS module: $25

---

## Next Steps

1. ✅ Order hardware components
2. ✅ Set up Raspberry Pi 5
3. ✅ Wire LEDs and buzzer
4. ✅ Install software
5. ✅ Test on bench
6. ✅ Mount in vehicle
7. ✅ Field test
8. ✅ Calibrate thresholds
9. 📋 Deploy and monitor

---

## Safety Disclaimer

⚠️ **IMPORTANT**: This system is a **driver assistance tool only**. It should NOT be used as the sole means of detecting hazardous road conditions. Always drive carefully and attentively, especially in winter conditions.

- System may have false positives/negatives
- Not a replacement for safe driving practices
- Driver is always responsible for vehicle control
- Test thoroughly before relying on system

---

## Additional Resources

- [Raspberry Pi 5 Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi-5.html)
- [Pi Camera Module 3 Guide](https://www.raspberrypi.com/documentation/accessories/camera.html)
- [RPi.GPIO Documentation](https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/)
- [Ultralytics Edge Deployment](https://docs.ultralytics.com/guides/raspberry-pi/)

---

**Ready to deploy? Follow the phases sequentially and you'll have a working system! 🚗❄️**
