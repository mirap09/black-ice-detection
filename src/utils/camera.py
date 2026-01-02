"""
Camera interface for capturing video frames.

Supports:
- USB/webcam cameras
- IP cameras (RTSP streams)
- Video files
"""

import cv2
import time
from pathlib import Path
from typing import Optional, Tuple
import numpy as np


class Camera:
    """Camera interface for video capture."""

    def __init__(
        self,
        source: int | str = 0,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fps: Optional[int] = None
    ):
        """
        Initialize camera.

        Args:
            source: Camera source (0 for default webcam, or video path/RTSP URL)
            width: Desired frame width (None for default)
            height: Desired frame height (None for default)
            fps: Desired FPS (None for default)
        """
        self.source = source
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_opened = False

        # Desired settings
        self.width = width
        self.height = height
        self.fps = fps

        # Actual settings (will be set after opening)
        self.actual_width = None
        self.actual_height = None
        self.actual_fps = None

    def open(self) -> bool:
        """
        Open camera/video source.

        Returns:
            True if successful, False otherwise
        """
        if self.is_opened:
            return True

        self.cap = cv2.VideoCapture(self.source)

        if not self.cap.isOpened():
            return False

        # Set desired properties
        if self.width:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        if self.height:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if self.fps:
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        # Get actual properties
        self.actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

        self.is_opened = True
        return True

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from camera.

        Returns:
            Tuple of (success, frame)
        """
        if not self.is_opened:
            if not self.open():
                return False, None

        ret, frame = self.cap.read()
        return ret, frame

    def release(self):
        """Release camera resources."""
        if self.cap:
            self.cap.release()
            self.is_opened = False

    def is_video_file(self) -> bool:
        """Check if source is a video file."""
        if isinstance(self.source, str):
            return Path(self.source).exists()
        return False

    def get_total_frames(self) -> Optional[int]:
        """
        Get total number of frames (for video files).

        Returns:
            Total frames, or None if not applicable
        """
        if not self.is_opened or not self.is_video_file():
            return None

        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def get_current_frame(self) -> Optional[int]:
        """
        Get current frame number (for video files).

        Returns:
            Current frame number, or None if not applicable
        """
        if not self.is_opened:
            return None

        return int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))

    def get_properties(self) -> dict:
        """
        Get camera properties.

        Returns:
            Dictionary of camera properties
        """
        if not self.is_opened:
            return {}

        return {
            'source': self.source,
            'width': self.actual_width,
            'height': self.actual_height,
            'fps': self.actual_fps,
            'is_video_file': self.is_video_file(),
            'total_frames': self.get_total_frames(),
        }

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()

    def __repr__(self) -> str:
        status = "opened" if self.is_opened else "closed"
        return f"Camera(source={self.source}, {status})"


class FrameRateLimiter:
    """Utility to limit frame processing rate."""

    def __init__(self, target_fps: float):
        """
        Initialize frame rate limiter.

        Args:
            target_fps: Target frames per second
        """
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        self.last_time = time.time()

    def wait(self):
        """Wait to maintain target FPS."""
        elapsed = time.time() - self.last_time
        sleep_time = self.frame_time - elapsed

        if sleep_time > 0:
            time.sleep(sleep_time)

        self.last_time = time.time()

    def reset(self):
        """Reset timer."""
        self.last_time = time.time()


def list_cameras(max_test: int = 5) -> list:
    """
    List available cameras.

    Args:
        max_test: Maximum camera indices to test

    Returns:
        List of available camera indices
    """
    available = []

    for i in range(max_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()

    return available


def test_camera(source: int | str = 0, duration: float = 5.0):
    """
    Test camera capture.

    Args:
        source: Camera source
        duration: Test duration in seconds
    """
    print(f"Testing camera: {source}")

    with Camera(source) as cam:
        if not cam.is_opened:
            print("Failed to open camera")
            return

        print("Camera properties:")
        for key, value in cam.get_properties().items():
            print(f"  {key}: {value}")

        print(f"\nCapturing frames for {duration} seconds...")
        print("Press 'q' to quit early")

        start_time = time.time()
        frame_count = 0

        while time.time() - start_time < duration:
            ret, frame = cam.read()

            if not ret:
                print("Failed to read frame")
                break

            frame_count += 1

            # Display frame
            cv2.imshow('Camera Test', frame)

            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        elapsed = time.time() - start_time
        actual_fps = frame_count / elapsed

        print(f"\nCaptured {frame_count} frames in {elapsed:.2f}s")
        print(f"Actual FPS: {actual_fps:.2f}")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Test default camera
    test_camera(0, duration=5.0)
