"""
Logging utilities for detection events.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import cv2
import numpy as np


class DetectionLogger:
    """Logger for black ice detection events."""

    def __init__(self, db_path: str | Path, save_images: bool = True):
        """
        Initialize detection logger.

        Args:
            db_path: Path to SQLite database
            save_images: Whether to save detection images
        """
        self.db_path = Path(db_path)
        self.save_images = save_images
        self.images_dir = self.db_path.parent / "detection_images"

        if self.save_images:
            self.images_dir.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create detections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                confidence REAL NOT NULL,
                bbox_x REAL NOT NULL,
                bbox_y REAL NOT NULL,
                bbox_w REAL NOT NULL,
                bbox_h REAL NOT NULL,
                severity TEXT NOT NULL,
                image_path TEXT,
                metadata TEXT
            )
        """)

        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                total_detections INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)

        # Create index on timestamp
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON detections(timestamp)
        """)

        conn.commit()
        conn.close()

    def log_detection(
        self,
        confidence: float,
        bbox: List[float],
        severity: str,
        frame: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log a detection event.

        Args:
            confidence: Detection confidence score
            bbox: Bounding box [x, y, w, h] (normalized 0-1)
            severity: Severity level (low, medium, high)
            frame: Optional frame image to save
            metadata: Optional additional metadata

        Returns:
            Detection ID
        """
        timestamp = datetime.now().isoformat()
        image_path = None

        # Save image if provided
        if frame is not None and self.save_images:
            image_filename = f"detection_{timestamp.replace(':', '-')}.jpg"
            image_path = self.images_dir / image_filename
            cv2.imwrite(str(image_path), frame)
            image_path = str(image_path)

        # Insert into database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO detections
            (timestamp, confidence, bbox_x, bbox_y, bbox_w, bbox_h, severity, image_path, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            confidence,
            bbox[0], bbox[1], bbox[2], bbox[3],
            severity,
            image_path,
            json.dumps(metadata) if metadata else None
        ))

        detection_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return detection_id

    def start_session(self, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Start a new detection session.

        Args:
            metadata: Optional session metadata

        Returns:
            Session ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sessions (start_time, metadata)
            VALUES (?, ?)
        """, (
            datetime.now().isoformat(),
            json.dumps(metadata) if metadata else None
        ))

        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return session_id

    def end_session(self, session_id: int):
        """
        End a detection session.

        Args:
            session_id: Session ID to end
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count detections in this session
        cursor.execute("""
            SELECT COUNT(*) FROM detections
            WHERE timestamp >= (
                SELECT start_time FROM sessions WHERE id = ?
            )
        """, (session_id,))

        total_detections = cursor.fetchone()[0]

        # Update session
        cursor.execute("""
            UPDATE sessions
            SET end_time = ?, total_detections = ?
            WHERE id = ?
        """, (
            datetime.now().isoformat(),
            total_detections,
            session_id
        ))

        conn.commit()
        conn.close()

    def get_detections(
        self,
        limit: int = 100,
        min_confidence: float = 0.0,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve detection records.

        Args:
            limit: Maximum number of records to return
            min_confidence: Minimum confidence threshold
            severity: Filter by severity level

        Returns:
            List of detection records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT id, timestamp, confidence, bbox_x, bbox_y, bbox_w, bbox_h,
                   severity, image_path, metadata
            FROM detections
            WHERE confidence >= ?
        """
        params = [min_confidence]

        if severity:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        detections = []
        for row in cursor.fetchall():
            detections.append({
                'id': row[0],
                'timestamp': row[1],
                'confidence': row[2],
                'bbox': [row[3], row[4], row[5], row[6]],
                'severity': row[7],
                'image_path': row[8],
                'metadata': json.loads(row[9]) if row[9] else None
            })

        conn.close()
        return detections

    def get_statistics(self, time_range: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detection statistics.

        Args:
            time_range: Optional time range filter (e.g., "24 hours")

        Returns:
            Dictionary of statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total detections
        cursor.execute("SELECT COUNT(*) FROM detections")
        total = cursor.fetchone()[0]

        # By severity
        cursor.execute("""
            SELECT severity, COUNT(*)
            FROM detections
            GROUP BY severity
        """)
        by_severity = dict(cursor.fetchall())

        # Average confidence
        cursor.execute("SELECT AVG(confidence) FROM detections")
        avg_confidence = cursor.fetchone()[0]

        # Recent detections (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM detections
            WHERE timestamp >= datetime('now', '-24 hours')
        """)
        recent_24h = cursor.fetchone()[0]

        conn.close()

        return {
            'total_detections': total,
            'by_severity': by_severity,
            'average_confidence': avg_confidence,
            'last_24_hours': recent_24h
        }

    def clear_old_detections(self, days: int = 30):
        """
        Clear detection records older than specified days.

        Args:
            days: Number of days to keep
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get image paths to delete
        cursor.execute("""
            SELECT image_path FROM detections
            WHERE timestamp < datetime('now', ? || ' days')
            AND image_path IS NOT NULL
        """, (f"-{days}",))

        image_paths = [row[0] for row in cursor.fetchall()]

        # Delete images
        for path in image_paths:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                pass

        # Delete records
        cursor.execute("""
            DELETE FROM detections
            WHERE timestamp < datetime('now', ? || ' days')
        """, (f"-{days}",))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count
