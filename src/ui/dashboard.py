"""
Streamlit Dashboard for Black Ice Detection System.

Real-time detection interface with camera feed, alerts, and statistics.
"""

import sys
import time
from pathlib import Path
import cv2
import numpy as np
import streamlit as st
from PIL import Image
import yaml
import tkinter as tk
from tkinter import filedialog

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.inference.detector import BlackIceDetector
from src.utils.camera import Camera
from src.utils.logging import DetectionLogger
from src.utils.config import Config


def select_file(file_types, title="Select file"):
    """Open native file browser dialog."""
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    file_path = filedialog.askopenfilename(
        title=title,
        filetypes=file_types
    )
    root.destroy()
    return file_path


# Page configuration
st.set_page_config(
    page_title="Black Ice Detection System",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stAlert {
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .severity-low {
        background-color: #fff3cd;
        color: #856404;
    }
    .severity-medium {
        background-color: #ffeaa7;
        color: #d63031;
    }
    .severity-high {
        background-color: #ff7675;
        color: #2d3436;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_detector(model_path: str, conf_threshold: float, device: str):
    """Load detector (cached)."""
    return BlackIceDetector(
        model_path=model_path,
        conf_threshold=conf_threshold,
        device=device
    )


@st.cache_resource
def load_alert_config(config_path: str):
    """Load alert configuration."""
    return Config(config_path)


def get_severity(confidence: float, bbox_area: float, alert_config: Config) -> str:
    """Determine severity level based on confidence and area."""
    # High severity
    if confidence >= alert_config.get("severity.high.confidence_min", 0.85):
        return "high"

    # Medium severity
    if confidence >= alert_config.get("severity.medium.confidence_min", 0.6):
        if bbox_area <= alert_config.get("severity.medium.bbox_area_max", 0.3):
            return "medium"
        else:
            return "high"

    # Low severity
    return "low"


def draw_detections(frame: np.ndarray, detections: list, alert_config: Config) -> np.ndarray:
    """Draw bounding boxes and labels on frame."""
    annotated = frame.copy()
    h, w = frame.shape[:2]

    for det in detections:
        # Get bbox coordinates
        x_center, y_center, width, height = det['bbox']
        x1 = int((x_center - width/2) * w)
        y1 = int((y_center - height/2) * h)
        x2 = int((x_center + width/2) * w)
        y2 = int((y_center + height/2) * h)

        # Determine severity
        bbox_area = width * height
        severity = get_severity(det['confidence'], bbox_area, alert_config)

        # Get color based on severity
        color_map = {
            'low': alert_config.get("severity.low.color", [255, 255, 0]),
            'medium': alert_config.get("severity.medium.color", [0, 165, 255]),
            'high': alert_config.get("severity.high.color", [0, 0, 255])
        }
        color = tuple(color_map.get(severity, [255, 255, 0]))

        # Draw bbox
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Draw label
        label = f"{det['class_name']} {det['confidence']:.2f} ({severity})"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

        # Background for text
        cv2.rectangle(
            annotated,
            (x1, y1 - label_size[1] - 10),
            (x1 + label_size[0], y1),
            color,
            -1
        )

        # Text
        cv2.putText(
            annotated,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )

    return annotated


def main():
    """Main dashboard function."""

    # Title
    st.title("❄️ Black Ice Detection System")
    st.markdown("Real-time black ice detection for vehicle safety")

    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")

    # Model selection
    st.sidebar.subheader("🧠 Model Selection")

    # Find available models
    available_models = []
    models_dir = Path("models")

    if models_dir.exists():
        # Look for .pt files in common locations
        for pattern in ["**/*.pt", "*.pt"]:
            available_models.extend([str(p) for p in models_dir.glob(pattern)])

    # Add default path if not found
    default_model = "models/checkpoints/black_ice/weights/best.pt"
    if default_model not in available_models and not available_models:
        available_models = [default_model]

    # Initialize session state for model path
    if 'model_path' not in st.session_state:
        st.session_state.model_path = default_model

    if available_models:
        # Dropdown for quick selection
        model_choice = st.sidebar.selectbox(
            "Select Model",
            options=["Custom Path"] + available_models,
            index=1 if len(available_models) > 0 else 0,
            help="Choose from available models or enter custom path"
        )

        if model_choice == "Custom Path":
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                model_path_input = st.text_input(
                    "Custom Model Path",
                    value=st.session_state.model_path,
                    placeholder="Enter path to .pt model file",
                    help="Path to trained YOLO model",
                    label_visibility="collapsed"
                )
            with col2:
                if st.button("📁", key="browse_model", help="Browse for model file"):
                    selected = select_file(
                        [("PyTorch Model", "*.pt"), ("All Files", "*.*")],
                        title="Select Model File"
                    )
                    if selected:
                        st.session_state.model_path = selected
                        st.rerun()
            model_path = model_path_input if model_path_input else st.session_state.model_path
        else:
            model_path = model_choice
            st.sidebar.text(f"📁 {model_path}")
    else:
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            model_path_input = st.text_input(
                "Model Path",
                value=st.session_state.model_path,
                placeholder="Enter path to .pt model file",
                help="Path to trained YOLO model",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("📁", key="browse_model", help="Browse for model file"):
                selected = select_file(
                    [("PyTorch Model", "*.pt"), ("All Files", "*.*")],
                    title="Select Model File"
                )
                if selected:
                    st.session_state.model_path = selected
                    st.rerun()
        model_path = model_path_input if model_path_input else st.session_state.model_path

    # File upload option for model
    st.sidebar.markdown("**Or upload a model:**")
    uploaded_model = st.sidebar.file_uploader(
        "Upload Model",
        type=["pt"],
        help="Upload a trained YOLOv8 .pt model file",
        label_visibility="collapsed"
    )

    if uploaded_model is not None:
        # Save uploaded model temporarily
        temp_model_path = Path("temp_model.pt")
        with open(temp_model_path, "wb") as f:
            f.write(uploaded_model.read())
        model_path = str(temp_model_path)
        st.sidebar.success(f"✅ Uploaded: {uploaded_model.name}")

    # Device selection
    device = st.sidebar.selectbox(
        "Device",
        options=["cpu", "cuda", "mps"],
        index=2 if sys.platform == "darwin" else 0,
        help="Inference device (use 'mps' for Mac, 'cuda' for NVIDIA)"
    )

    # Confidence threshold
    conf_threshold = st.sidebar.slider(
        "Confidence Threshold",
        min_value=0.1,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Minimum confidence for detection"
    )

    # Camera source
    camera_source = st.sidebar.selectbox(
        "Camera Source",
        options=["Webcam (0)", "Video File", "IP Camera"],
        help="Select video input source"
    )

    # Get camera source value
    # Initialize session state for video path
    if 'video_path' not in st.session_state:
        st.session_state.video_path = ""

    source = None
    if camera_source == "Webcam (0)":
        source = 0
    elif camera_source == "Video File":
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            video_file = st.text_input(
                "Video File Path",
                value=st.session_state.video_path,
                placeholder="Enter path to video file",
                help="Full path to the video file",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("📁", key="browse_video", help="Browse for video file"):
                selected = select_file(
                    [("Video Files", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*")],
                    title="Select Video File"
                )
                if selected:
                    st.session_state.video_path = selected
                    st.rerun()

        # Show file upload option as alternative
        st.sidebar.markdown("**Or upload a video:**")
        uploaded_file = st.sidebar.file_uploader(
            "Upload Video",
            type=["mp4", "avi", "mov", "mkv"],
            help="Upload a video file to analyze",
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            # Save uploaded file temporarily
            temp_path = Path("temp_upload.mp4")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())
            source = str(temp_path)
            st.sidebar.success(f"✅ Uploaded: {uploaded_file.name}")
        elif video_file and video_file.strip():
            source = video_file.strip()
        else:
            st.sidebar.warning("⚠️ Please enter a video file path or upload a file")
    else:  # IP Camera
        ip_url = st.sidebar.text_input(
            "RTSP URL",
            value="",
            placeholder="rtsp://username:password@ip:port/stream",
            help="RTSP stream URL"
        )
        if ip_url and ip_url.startswith("rtsp://"):
            source = ip_url
        else:
            st.sidebar.warning("⚠️ Please enter a valid RTSP URL")

    # Alert settings
    st.sidebar.header("🔔 Alert Settings")
    enable_alerts = st.sidebar.checkbox("Enable Alerts", value=True)
    show_confidence = st.sidebar.checkbox("Show Confidence", value=True)
    save_detections = st.sidebar.checkbox("Save Detection Frames", value=False, help="Save frames with detections to 'detections/' folder")

    # Video playback settings (only for video files)
    if camera_source == "Video File":
        st.sidebar.header("▶️ Playback Settings")
        playback_speed = st.sidebar.slider(
            "Playback Speed",
            min_value=0.1,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Adjust video playback speed (1.0 = normal)"
        )

    # Load detector
    try:
        if not Path(model_path).exists():
            st.error(f"❌ Model not found: {model_path}")
            st.info("Please train a model first: `python src/training/train.py`")
            return

        with st.spinner("Loading model..."):
            detector = load_detector(model_path, conf_threshold, device)

        # Show model info
        st.sidebar.success("✅ Model loaded successfully!")
        with st.sidebar.expander("📊 Model Info"):
            model_size = Path(model_path).stat().st_size / (1024 * 1024)  # MB
            st.text(f"Size: {model_size:.1f} MB")
            st.text(f"Device: {device.upper()}")
            st.text(f"Threshold: {conf_threshold}")

        # Load alert config
        alert_config_path = "configs/alerts.yaml"
        if Path(alert_config_path).exists():
            alert_config = load_alert_config(alert_config_path)
        else:
            alert_config = Config.__new__(Config)
            alert_config._config = {}

    except Exception as e:
        st.error(f"❌ Error loading model: {e}")
        st.info("Make sure the model file is a valid YOLOv8 .pt file")
        return

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📹 Live Feed")
        frame_placeholder = st.empty()

    with col2:
        st.subheader("📊 Statistics")
        stats_placeholder = st.empty()

        st.subheader("⚠️ Current Alert")
        alert_placeholder = st.empty()

        st.subheader("🕐 Recent Detections")
        st.markdown("*Shows frame number, time, confidence, and coverage area*")
        recent_placeholder = st.empty()

        st.subheader("💾 Detection Summary")
        summary_placeholder = st.empty()

    # Control buttons
    col_start, col_stop = st.columns(2)

    with col_start:
        start_btn = st.button("▶️ Start Detection", type="primary", use_container_width=True)

    with col_stop:
        stop_btn = st.button("⏹️ Stop Detection", use_container_width=True)

    # Session state
    if 'running' not in st.session_state:
        st.session_state.running = False

    if 'detection_count' not in st.session_state:
        st.session_state.detection_count = 0
        st.session_state.total_frames = 0
        st.session_state.avg_confidence = 0.0
        st.session_state.recent_detections = []

    if start_btn:
        st.session_state.running = True

    if stop_btn:
        st.session_state.running = False

    # Detection loop
    if st.session_state.running:
        # Validate source
        if source is None:
            st.error("⚠️ Please configure a valid camera source before starting detection")
            st.session_state.running = False
            return

        try:
            # For video files, check if file exists
            if isinstance(source, str) and not source.startswith("rtsp://"):
                if not Path(source).exists():
                    st.error(f"❌ Video file not found: {source}")
                    st.session_state.running = False
                    return

            camera = Camera(source)

            if not camera.open():
                st.error(f"❌ Failed to open camera source: {source}")
                st.session_state.running = False
                return

            st.success(f"✅ Detection started! Source: {source}")

            while st.session_state.running:
                # Read frame
                ret, frame = camera.read()

                if not ret:
                    st.warning("End of video or camera disconnected")
                    break

                st.session_state.total_frames += 1

                # Detect
                detections, inference_time = detector.detect_with_timing(frame)

                # Update statistics
                if detections:
                    st.session_state.detection_count += len(detections)
                    confidences = [d['confidence'] for d in detections]
                    st.session_state.avg_confidence = np.mean(confidences)

                    # Add to recent detections
                    for det in detections:
                        bbox_area = det['bbox'][2] * det['bbox'][3]
                        severity = get_severity(det['confidence'], bbox_area, alert_config)
                        st.session_state.recent_detections.insert(0, {
                            'time': time.strftime('%H:%M:%S'),
                            'frame': st.session_state.total_frames,
                            'confidence': det['confidence'],
                            'severity': severity,
                            'bbox_area': f"{bbox_area*100:.1f}%"
                        })

                    # Keep only last 10
                    st.session_state.recent_detections = st.session_state.recent_detections[:10]

                # Draw detections
                annotated_frame = draw_detections(frame, detections, alert_config)

                # Save detection frames if enabled
                if detections and save_detections:
                    save_dir = Path("detections")
                    save_dir.mkdir(exist_ok=True)
                    save_path = save_dir / f"frame_{st.session_state.total_frames:05d}.jpg"
                    cv2.imwrite(str(save_path), annotated_frame)

                # Convert BGR to RGB
                annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)

                # Display frame
                frame_placeholder.image(annotated_frame, channels="RGB", use_container_width=True)

                # Update statistics
                with stats_placeholder.container():
                    st.metric("Total Frames", st.session_state.total_frames)
                    st.metric("Detections", st.session_state.detection_count)
                    st.metric("Avg Confidence", f"{st.session_state.avg_confidence:.2%}")
                    st.metric("Inference Time", f"{inference_time:.1f}ms")
                    fps = 1000 / inference_time if inference_time > 0 else 0
                    st.metric("FPS", f"{fps:.1f}")

                # Update alert
                with alert_placeholder.container():
                    if detections and enable_alerts:
                        max_conf_det = max(detections, key=lambda x: x['confidence'])
                        bbox_area = max_conf_det['bbox'][2] * max_conf_det['bbox'][3]
                        severity = get_severity(max_conf_det['confidence'], bbox_area, alert_config)

                        severity_config = alert_config.get(f"severity.{severity}", {})
                        message = severity_config.get('message', 'Black ice detected')

                        if severity == "high":
                            st.error(f"🚨 {message}")
                        elif severity == "medium":
                            st.warning(f"⚠️ {message}")
                        else:
                            st.info(f"ℹ️ {message}")
                    else:
                        st.success("✅ No black ice detected")

                # Update recent detections
                with recent_placeholder.container():
                    if st.session_state.recent_detections:
                        for det in st.session_state.recent_detections[:10]:
                            severity_emoji = {
                                'low': '🟡',
                                'medium': '🟠',
                                'high': '🔴'
                            }
                            st.text(
                                f"{severity_emoji.get(det['severity'], '⚪')} "
                                f"Frame {det['frame']:05d} | "
                                f"{det['time']} | "
                                f"Conf: {det['confidence']:.1%} | "
                                f"Area: {det['bbox_area']}"
                            )
                    else:
                        st.text("No recent detections")

                # Update detection summary
                with summary_placeholder.container():
                    if st.session_state.detection_count > 0:
                        detection_rate = (st.session_state.detection_count / st.session_state.total_frames) * 100
                        st.metric("Detection Rate", f"{detection_rate:.1f}%")
                        st.metric("Total Detections", st.session_state.detection_count)

                        # Count by severity
                        severity_counts = {'low': 0, 'medium': 0, 'high': 0}
                        for det in st.session_state.recent_detections:
                            severity_counts[det['severity']] += 1

                        st.text(f"🟡 Low: {severity_counts['low']}")
                        st.text(f"🟠 Medium: {severity_counts['medium']}")
                        st.text(f"🔴 High: {severity_counts['high']}")
                    else:
                        st.text("No detections yet")

                # Adjust playback speed for video files
                if camera_source == "Video File" and playback_speed < 1.0:
                    # Add delay to slow down playback
                    delay = (1.0 / playback_speed - 1.0) * 0.03
                    time.sleep(delay)
                else:
                    # Small delay to prevent overwhelming the UI
                    time.sleep(0.01)

            camera.release()
            st.info("Detection stopped")

        except Exception as e:
            st.error(f"Error during detection: {e}")
            st.session_state.running = False

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "Black Ice Detection System uses YOLOv8 to detect black ice on road surfaces. "
        "Trained on 2,851 images from indoor and outdoor conditions."
    )
    st.sidebar.markdown("**Status:** " + ("🟢 Running" if st.session_state.running else "🔴 Stopped"))


if __name__ == "__main__":
    main()
