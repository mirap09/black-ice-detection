"""
Alert severity classification for black ice detections.
"""

from typing import List, Dict, Tuple
from pathlib import Path
import yaml


class AlertClassifier:
    """Classify detection severity based on confidence and area."""

    def __init__(self, config_path: str | Path = "configs/alerts.yaml"):
        """
        Initialize alert classifier.

        Args:
            config_path: Path to alert configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load alert configuration from YAML."""
        if not self.config_path.exists():
            # Default configuration
            return {
                'severity': {
                    'low': {
                        'confidence_min': 0.3,
                        'confidence_max': 0.6,
                        'bbox_area_max': 0.1,
                        'message': 'Possible black ice detected - Exercise caution',
                        'color': [255, 255, 0]
                    },
                    'medium': {
                        'confidence_min': 0.6,
                        'confidence_max': 0.85,
                        'bbox_area_max': 0.3,
                        'message': 'Black ice detected - Reduce speed',
                        'color': [0, 165, 255]
                    },
                    'high': {
                        'confidence_min': 0.85,
                        'confidence_max': 1.0,
                        'bbox_area_max': 1.0,
                        'message': 'WARNING: Significant black ice ahead!',
                        'color': [0, 0, 255]
                    }
                }
            }

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def classify(self, confidence: float, bbox_area: float) -> str:
        """
        Classify detection severity.

        Args:
            confidence: Detection confidence (0-1)
            bbox_area: Normalized bounding box area (0-1)

        Returns:
            Severity level: 'low', 'medium', or 'high'
        """
        # High severity
        high_conf_min = self.config['severity']['high']['confidence_min']
        if confidence >= high_conf_min:
            return 'high'

        # Medium severity
        med_conf_min = self.config['severity']['medium']['confidence_min']
        med_area_max = self.config['severity']['medium']['bbox_area_max']

        if confidence >= med_conf_min:
            if bbox_area <= med_area_max:
                return 'medium'
            else:
                # Large area is more dangerous
                return 'high'

        # Low severity
        return 'low'

    def classify_batch(self, detections: List[dict]) -> List[Tuple[dict, str]]:
        """
        Classify multiple detections.

        Args:
            detections: List of detection dictionaries

        Returns:
            List of (detection, severity) tuples
        """
        results = []

        for det in detections:
            bbox = det['bbox']
            bbox_area = bbox[2] * bbox[3]  # width * height
            severity = self.classify(det['confidence'], bbox_area)
            results.append((det, severity))

        return results

    def get_highest_severity(self, detections: List[dict]) -> str:
        """
        Get the highest severity level from detections.

        Args:
            detections: List of detection dictionaries

        Returns:
            Highest severity: 'high', 'medium', 'low', or 'none'
        """
        if not detections:
            return 'none'

        classified = self.classify_batch(detections)
        severities = [sev for _, sev in classified]

        if 'high' in severities:
            return 'high'
        elif 'medium' in severities:
            return 'medium'
        elif 'low' in severities:
            return 'low'
        else:
            return 'none'

    def get_alert_message(self, severity: str) -> str:
        """
        Get alert message for severity level.

        Args:
            severity: Severity level

        Returns:
            Alert message string
        """
        if severity == 'none':
            return 'No black ice detected'

        return self.config['severity'][severity]['message']

    def get_alert_color(self, severity: str) -> List[int]:
        """
        Get BGR color for severity level.

        Args:
            severity: Severity level

        Returns:
            BGR color as [B, G, R]
        """
        if severity == 'none':
            return [0, 255, 0]  # Green

        return self.config['severity'][severity]['color']

    def should_trigger_audio(self, severity: str) -> bool:
        """
        Determine if audio alert should be triggered.

        Args:
            severity: Severity level

        Returns:
            True if audio alert should play
        """
        audio_config = self.config.get('audio', {})

        if not audio_config.get('enabled', True):
            return False

        # Audio for medium and high severity
        return severity in ['medium', 'high']
