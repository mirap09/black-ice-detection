"""
Black ice detector using trained YOLO model.
"""

import time
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import cv2
from ultralytics import YOLO
import torch


class BlackIceDetector:
    """Black ice detector using YOLOv8."""

    def __init__(
        self,
        model_path: str | Path,
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: str = "cuda"
    ):
        """
        Initialize black ice detector.

        Args:
            model_path: Path to trained YOLO model
            conf_threshold: Confidence threshold for detections
            iou_threshold: IoU threshold for NMS
            device: Device to run inference on (cuda/cpu/mps)
        """
        self.model_path = Path(model_path)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

        # Check device availability
        if device == "cuda" and not torch.cuda.is_available():
            print("⚠ CUDA not available, using CPU")
            device = "cpu"
        elif device == "mps" and not torch.backends.mps.is_available():
            print("⚠ MPS not available, using CPU")
            device = "cpu"

        self.device = device

        # Load model
        print(f"Loading model from: {self.model_path}")
        self.model = YOLO(self.model_path)
        self.model.to(device)

        print(f"✓ Model loaded on {device}")

        # Warmup
        self._warmup()

    def _warmup(self, img_size: int = 640):
        """Warmup model with dummy inference."""
        print("Warming up model...")
        dummy_img = np.zeros((img_size, img_size, 3), dtype=np.uint8)
        self.detect(dummy_img)
        print("✓ Model ready")

    def detect(
        self,
        image: np.ndarray,
        visualize: bool = False
    ) -> List[dict]:
        """
        Detect black ice in image.

        Args:
            image: Input image (BGR format)
            visualize: Whether to draw detections on image

        Returns:
            List of detections, each containing:
                - bbox: [x, y, w, h] (normalized 0-1)
                - confidence: Detection confidence
                - class_id: Class ID (0 for black_ice)
                - class_name: Class name
        """
        # Run inference
        results = self.model.predict(
            image,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False
        )[0]

        # Parse detections
        detections = []

        if results.boxes is not None:
            boxes = results.boxes
            img_h, img_w = image.shape[:2]

            for i in range(len(boxes)):
                # Get box in xyxy format
                xyxy = boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = xyxy

                # Convert to xywh (normalized)
                x_center = ((x1 + x2) / 2) / img_w
                y_center = ((y1 + y2) / 2) / img_h
                width = (x2 - x1) / img_w
                height = (y2 - y1) / img_h

                # Get confidence and class
                confidence = float(boxes.conf[i])
                class_id = int(boxes.cls[i])
                class_name = self.model.names[class_id]

                detections.append({
                    'bbox': [x_center, y_center, width, height],
                    'bbox_xyxy': [x1, y1, x2, y2],
                    'confidence': confidence,
                    'class_id': class_id,
                    'class_name': class_name
                })

        # Visualize if requested
        if visualize and results.plot is not None:
            results.plot()

        return detections

    def detect_with_timing(
        self,
        image: np.ndarray
    ) -> Tuple[List[dict], float]:
        """
        Detect with timing information.

        Args:
            image: Input image

        Returns:
            Tuple of (detections, inference_time_ms)
        """
        start_time = time.time()
        detections = self.detect(image)
        inference_time = (time.time() - start_time) * 1000  # Convert to ms

        return detections, inference_time

    def get_coverage_percentage(
        self,
        detections: List[dict]
    ) -> float:
        """
        Calculate estimated black ice coverage percentage.

        Args:
            detections: List of detections

        Returns:
            Coverage percentage (0-100)
        """
        if not detections:
            return 0.0

        total_area = sum(det['bbox'][2] * det['bbox'][3] for det in detections)
        return min(total_area * 100, 100.0)

    def get_highest_confidence(
        self,
        detections: List[dict]
    ) -> Optional[float]:
        """
        Get highest confidence among detections.

        Args:
            detections: List of detections

        Returns:
            Highest confidence, or None if no detections
        """
        if not detections:
            return None

        return max(det['confidence'] for det in detections)

    def update_thresholds(
        self,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ):
        """
        Update detection thresholds.

        Args:
            conf_threshold: New confidence threshold
            iou_threshold: New IoU threshold
        """
        if conf_threshold is not None:
            self.conf_threshold = conf_threshold

        if iou_threshold is not None:
            self.iou_threshold = iou_threshold


class ONNXDetector:
    """Black ice detector using ONNX Runtime (for deployment)."""

    def __init__(
        self,
        onnx_path: str | Path,
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        img_size: int = 640
    ):
        """
        Initialize ONNX detector.

        Args:
            onnx_path: Path to ONNX model
            conf_threshold: Confidence threshold
            iou_threshold: IoU threshold for NMS
            img_size: Input image size
        """
        import onnxruntime as ort

        self.onnx_path = Path(onnx_path)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.img_size = img_size

        # Create inference session
        print(f"Loading ONNX model from: {self.onnx_path}")
        self.session = ort.InferenceSession(str(self.onnx_path))

        # Get input/output names
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [out.name for out in self.session.get_outputs()]

        print(f"✓ ONNX model loaded")
        print(f"  Input: {self.input_name}")
        print(f"  Outputs: {self.output_names}")

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for ONNX model.

        Args:
            image: Input image (BGR)

        Returns:
            Preprocessed image tensor
        """
        # Resize
        img = cv2.resize(image, (self.img_size, self.img_size))

        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Normalize to [0, 1]
        img = img.astype(np.float32) / 255.0

        # Transpose to CHW format
        img = img.transpose(2, 0, 1)

        # Add batch dimension
        img = np.expand_dims(img, axis=0)

        return img

    def detect(self, image: np.ndarray) -> List[dict]:
        """
        Detect black ice using ONNX model.

        Args:
            image: Input image (BGR)

        Returns:
            List of detections
        """
        # Preprocess
        input_tensor = self.preprocess(image)

        # Run inference
        outputs = self.session.run(self.output_names, {self.input_name: input_tensor})

        # Post-process outputs
        # Note: Post-processing depends on YOLO export format
        # This is a simplified version - you may need to adjust based on actual output format
        detections = self._postprocess(outputs, image.shape[:2])

        return detections

    def _postprocess(
        self,
        outputs: List[np.ndarray],
        img_shape: Tuple[int, int]
    ) -> List[dict]:
        """
        Post-process ONNX outputs.

        Args:
            outputs: Model outputs
            img_shape: Original image shape (h, w)

        Returns:
            List of detections
        """
        # This is a placeholder - actual implementation depends on YOLO output format
        # You'll need to implement NMS and coordinate conversion based on your exported model
        detections = []

        # TODO: Implement proper post-processing for ONNX outputs
        # This typically involves:
        # 1. Parse output tensor
        # 2. Apply confidence threshold
        # 3. Apply NMS
        # 4. Convert coordinates back to original image space

        return detections


def test_detector(model_path: str | Path, image_path: str | Path):
    """
    Test detector on a single image.

    Args:
        model_path: Path to model
        image_path: Path to test image
    """
    # Load detector
    detector = BlackIceDetector(model_path)

    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Failed to load image: {image_path}")
        return

    print(f"\nTesting on: {image_path}")
    print(f"Image size: {image.shape[1]}x{image.shape[0]}")

    # Detect
    detections, inference_time = detector.detect_with_timing(image)

    print(f"\nInference time: {inference_time:.2f}ms")
    print(f"Detections: {len(detections)}")

    # Display detections
    for i, det in enumerate(detections, 1):
        print(f"\nDetection {i}:")
        print(f"  Class: {det['class_name']}")
        print(f"  Confidence: {det['confidence']:.3f}")
        print(f"  BBox (normalized): {[f'{x:.3f}' for x in det['bbox']]}")

    # Calculate coverage
    coverage = detector.get_coverage_percentage(detections)
    print(f"\nEstimated coverage: {coverage:.1f}%")

    # Visualize
    print("\nPress any key to close visualization...")
    results = detector.model.predict(image, conf=detector.conf_threshold)[0]
    annotated = results.plot()
    cv2.imshow('Detection', annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python detector.py <model_path> <image_path>")
        sys.exit(1)

    test_detector(sys.argv[1], sys.argv[2])
