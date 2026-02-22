"""
Side-by-side comparison view for Golf Swing Capture.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional

import cv2
import numpy as np

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSlider, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

logger = logging.getLogger(__name__)


class ComparisonVideoPlayer(QLabel):
    """Lightweight video display for comparison view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 225)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def display_frame(self, frame: np.ndarray):
        if frame is None:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bpl = ch * w
        q_img = QImage(rgb.tobytes(), w, h, bpl, QImage.Format.Format_RGB888)
        scaled = q_img.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(QPixmap.fromImage(scaled))


class ComparisonWindow(QDialog):
    """Side-by-side comparison of two clips with synchronized playback."""

    def __init__(self, clips: List[Dict], session_folder: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Swing Comparison")
        self.setMinimumSize(1000, 600)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; }
            QLabel { color: #ccc; }
            QComboBox {
                background-color: #2d2d2d; color: #ccc;
                border: 1px solid #444; border-radius: 4px; padding: 4px 8px;
            }
            QPushButton {
                background-color: #3d3d3d; color: #ccc;
                border: 1px solid #555; border-radius: 6px; padding: 6px 12px;
            }
            QPushButton:hover { background-color: #4d4d4d; }
            QPushButton:checked { background-color: #4a9eff; color: white; }
            QSlider::groove:horizontal {
                height: 6px; background-color: #444; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 14px; height: 14px; margin: -4px 0;
                background-color: #4a9eff; border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background-color: #4a9eff; border-radius: 3px;
            }
        """)

        self.clips = clips
        self.session_folder = session_folder

        self.left_frames: List[np.ndarray] = []
        self.right_frames: List[np.ndarray] = []
        self.left_offset = 0
        self.right_offset = 0
        self.position = 0
        self.is_playing = False
        self.speed = 1.0

        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Video panels
        videos = QHBoxLayout()

        # Left panel
        left_panel = QVBoxLayout()
        self.left_combo = QComboBox()
        for i, clip in enumerate(self.clips):
            self.left_combo.addItem(f"Shot {clip['file'].replace('shot_', '').replace('.mp4', '')}", i)
        self.left_combo.currentIndexChanged.connect(lambda: self._load_clip("left"))
        left_panel.addWidget(self.left_combo)

        self.left_angle_combo = QComboBox()
        self.left_angle_combo.addItem("Primary", None)
        self.left_angle_combo.currentIndexChanged.connect(lambda: self._load_clip("left"))
        left_panel.addWidget(self.left_angle_combo)

        self.left_player = ComparisonVideoPlayer()
        left_panel.addWidget(self.left_player, stretch=1)

        self.left_offset_label = QLabel("Offset: 0 frames")
        left_panel.addWidget(self.left_offset_label)

        left_offset_layout = QHBoxLayout()
        left_minus = QPushButton("-5")
        left_minus.clicked.connect(lambda: self._adjust_offset("left", -5))
        left_offset_layout.addWidget(left_minus)
        left_plus = QPushButton("+5")
        left_plus.clicked.connect(lambda: self._adjust_offset("left", 5))
        left_offset_layout.addWidget(left_plus)
        left_panel.addLayout(left_offset_layout)

        videos.addLayout(left_panel)

        # Divider
        divider = QWidget()
        divider.setFixedWidth(2)
        divider.setStyleSheet("background-color: #444;")
        videos.addWidget(divider)

        # Right panel
        right_panel = QVBoxLayout()
        self.right_combo = QComboBox()
        for i, clip in enumerate(self.clips):
            self.right_combo.addItem(f"Shot {clip['file'].replace('shot_', '').replace('.mp4', '')}", i)
        if len(self.clips) > 1:
            self.right_combo.setCurrentIndex(1)
        self.right_combo.currentIndexChanged.connect(lambda: self._load_clip("right"))
        right_panel.addWidget(self.right_combo)

        self.right_angle_combo = QComboBox()
        self.right_angle_combo.addItem("Primary", None)
        self.right_angle_combo.currentIndexChanged.connect(lambda: self._load_clip("right"))
        right_panel.addWidget(self.right_angle_combo)

        self.right_player = ComparisonVideoPlayer()
        right_panel.addWidget(self.right_player, stretch=1)

        self.right_offset_label = QLabel("Offset: 0 frames")
        right_panel.addWidget(self.right_offset_label)

        right_offset_layout = QHBoxLayout()
        right_minus = QPushButton("-5")
        right_minus.clicked.connect(lambda: self._adjust_offset("right", -5))
        right_offset_layout.addWidget(right_minus)
        right_plus = QPushButton("+5")
        right_plus.clicked.connect(lambda: self._adjust_offset("right", 5))
        right_offset_layout.addWidget(right_plus)
        right_panel.addLayout(right_offset_layout)

        videos.addLayout(right_panel)
        layout.addLayout(videos, stretch=1)

        # Shared controls
        controls = QHBoxLayout()

        self.play_btn = QPushButton("Play")
        self.play_btn.setCheckable(True)
        self.play_btn.clicked.connect(self._toggle_play)
        controls.addWidget(self.play_btn)

        self.scrub_slider = QSlider(Qt.Orientation.Horizontal)
        self.scrub_slider.setMinimum(0)
        self.scrub_slider.setMaximum(100)
        self.scrub_slider.valueChanged.connect(self._on_scrub)
        controls.addWidget(self.scrub_slider, stretch=1)

        self.frame_label = QLabel("0 / 0")
        self.frame_label.setFixedWidth(80)
        controls.addWidget(self.frame_label)

        self.speed_combo = QComboBox()
        for s in ["0.25x", "0.5x", "0.75x", "1.0x"]:
            self.speed_combo.addItem(s)
        self.speed_combo.setCurrentIndex(3)
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        controls.addWidget(self.speed_combo)

        layout.addLayout(controls)

        # Load initial clips
        self._load_clip("left")
        self._load_clip("right")

    def _setup_timer(self):
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self._tick)

    def _load_clip(self, side: str):
        combo = self.left_combo if side == "left" else self.right_combo
        angle_combo = self.left_angle_combo if side == "left" else self.right_angle_combo
        idx = combo.currentData()
        if idx is None or idx < 0 or idx >= len(self.clips):
            return

        clip = self.clips[idx]

        # Populate angle selector (block signals to avoid recursive load)
        current_angle = angle_combo.currentData()
        angle_combo.blockSignals(True)
        angle_combo.clear()
        angle_combo.addItem("Primary", None)
        if "camera_files" in clip:
            labels = clip.get("camera_labels", {})
            for cam_id, filename in clip["camera_files"].items():
                label = labels.get(cam_id, f"Camera {cam_id}")
                angle_combo.addItem(label, cam_id)
        angle_combo.blockSignals(False)

        # Restore previous angle selection if still valid
        if current_angle is not None:
            for i in range(angle_combo.count()):
                if angle_combo.itemData(i) == current_angle:
                    angle_combo.blockSignals(True)
                    angle_combo.setCurrentIndex(i)
                    angle_combo.blockSignals(False)
                    break

        # Determine which file to load based on selected angle
        cam_id = angle_combo.currentData()
        if cam_id and "camera_files" in clip:
            filename = clip["camera_files"].get(cam_id, clip["file"])
        else:
            filename = clip["file"]

        path = self.session_folder / filename
        if not path.exists():
            return

        frames = []
        cap = cv2.VideoCapture(str(path))
        try:
            if not cap.isOpened():
                return
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
        finally:
            cap.release()

        if side == "left":
            self.left_frames = frames
        else:
            self.right_frames = frames

        self._update_slider_range()
        self._show_frames()

    def _adjust_offset(self, side: str, delta: int):
        if side == "left":
            self.left_offset += delta
            self.left_offset_label.setText(f"Offset: {self.left_offset} frames")
        else:
            self.right_offset += delta
            self.right_offset_label.setText(f"Offset: {self.right_offset} frames")
        self._show_frames()

    def _update_slider_range(self):
        max_len = max(len(self.left_frames), len(self.right_frames), 1)
        self.scrub_slider.setMaximum(max_len - 1)

    def _toggle_play(self):
        self.is_playing = self.play_btn.isChecked()
        if self.is_playing:
            interval = int(33 / self.speed)
            self.play_timer.start(interval)
            self.play_btn.setText("Pause")
        else:
            self.play_timer.stop()
            self.play_btn.setText("Play")

    def _on_scrub(self, value: int):
        self.position = value
        self._show_frames()

    def _on_speed_changed(self, text: str):
        try:
            self.speed = float(text.replace("x", ""))
        except (ValueError, TypeError):
            self.speed = 1.0
        if self.speed <= 0:
            self.speed = 1.0
        if self.is_playing:
            self.play_timer.setInterval(int(33 / self.speed))

    def _tick(self):
        max_len = max(len(self.left_frames), len(self.right_frames), 1)
        self.position = (self.position + 1) % max_len
        self.scrub_slider.blockSignals(True)
        self.scrub_slider.setValue(self.position)
        self.scrub_slider.blockSignals(False)
        self._show_frames()

    def _show_frames(self):
        max_len = max(len(self.left_frames), len(self.right_frames), 1)
        self.frame_label.setText(f"{self.position + 1} / {max_len}")

        left_idx = self.position + self.left_offset
        if 0 <= left_idx < len(self.left_frames):
            self.left_player.display_frame(self.left_frames[left_idx])

        right_idx = self.position + self.right_offset
        if 0 <= right_idx < len(self.right_frames):
            self.right_player.display_frame(self.right_frames[right_idx])
