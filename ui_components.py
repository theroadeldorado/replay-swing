"""
Reusable UI components for Golf Swing Capture.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict

import cv2
import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QGridLayout, QScrollArea, QMenu, QTextEdit,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QImage, QPixmap, QCursor, QColor, QPainter, QPen, QTextCursor,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Multi-Angle Grid Composite
# ============================================================================

def composite_grid(frames: Dict[str, np.ndarray], labels: Dict[str, str],
                   target_size: tuple = (1280, 720)) -> np.ndarray:
    """Composite multiple camera frames into a grid with labels.

    - 1 camera: full frame
    - 2 cameras: side by side (2x1)
    - 3-4 cameras: 2x2 grid
    """
    cam_ids = list(frames.keys())
    n = len(cam_ids)
    if n == 0:
        return np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)

    tw, th = target_size

    if n == 1:
        cell_w, cell_h = tw, th
        cols, rows = 1, 1
    elif n == 2:
        cell_w, cell_h = tw // 2, th
        cols, rows = 2, 1
    else:
        cell_w, cell_h = tw // 2, th // 2
        cols, rows = 2, 2

    canvas = np.zeros((th, tw, 3), dtype=np.uint8)

    for i, cam_id in enumerate(cam_ids):
        if i >= rows * cols:
            break
        row = i // cols
        col = i % cols
        x0 = col * cell_w
        y0 = row * cell_h

        frame = frames[cam_id]
        resized = cv2.resize(frame, (cell_w, cell_h))

        # Draw label
        label = labels.get(cam_id, f"Camera {cam_id}")
        cv2.putText(resized, label, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        canvas[y0:y0 + cell_h, x0:x0 + cell_w] = resized

    return canvas


# ============================================================================
# Video Player Widget
# ============================================================================

class VideoPlayer(QLabel):
    """Widget for displaying video frames with overlay support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 360)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")
        self.setScaledContents(False)
        self._last_frame = None
        self._video_rect = (0, 0, 0, 0)  # x, y, w, h of the displayed video

    @property
    def video_rect(self):
        return self._video_rect

    def display_frame(self, frame: np.ndarray):
        if frame is None:
            return

        self._last_frame = frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        scaled = q_img.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Calculate video rect position (centered)
        sx = (self.width() - scaled.width()) // 2
        sy = (self.height() - scaled.height()) // 2
        self._video_rect = (sx, sy, scaled.width(), scaled.height())

        self.setPixmap(QPixmap.fromImage(scaled))


# ============================================================================
# Picture-in-Picture Window
# ============================================================================

class PiPWindow(QWidget):
    """Floating Picture-in-Picture window for overlay playback."""

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool,
        )

        self.setWindowTitle("Golf Swing - PiP")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 2px solid #4a9eff;
                border-radius: 12px;
            }
        """)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(4, 4, 4, 4)
        container_layout.setSpacing(2)

        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(24)
        title_bar.setStyleSheet("background-color: transparent;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 0, 8, 0)

        title_label = QLabel("Swing Replay")
        title_label.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 11px;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        close_btn = QPushButton("X")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #888; border: none; font-size: 14px; }
            QPushButton:hover { color: #ff5555; }
        """)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)

        container_layout.addWidget(title_bar)

        self.video_display = QLabel()
        self.video_display.setMinimumSize(320, 180)
        self.video_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_display.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")
        container_layout.addWidget(self.video_display)

        layout.addWidget(self.container)

        self._drag_pos = None
        self.resize(480, 300)

    def display_frame(self, frame: np.ndarray):
        if frame is None:
            return
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        scaled = q_img.scaled(
            self.video_display.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_display.setPixmap(QPixmap.fromImage(scaled))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


# ============================================================================
# Thumbnail Widget
# ============================================================================

class ThumbnailWidget(QFrame):
    """Widget displaying a single clip thumbnail."""

    clicked = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    mark_not_shot_requested = pyqtSignal(int)

    def __init__(self, index: int, clip_info: Dict, thumbnail_path: Optional[Path], parent=None):
        super().__init__(parent)
        self.index = index
        self.clip_info = clip_info
        self.selected = False

        self.setFixedSize(170, 130)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(160, 90)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")

        if thumbnail_path and thumbnail_path.exists():
            pixmap = QPixmap(str(thumbnail_path))
            scaled = pixmap.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)
        else:
            self.thumb_label.setText("Golf")
            self.thumb_label.setStyleSheet(
                "background-color: #1a1a1a; border-radius: 4px; color: #4a9eff; font-size: 18px;"
            )

        layout.addWidget(self.thumb_label)

        shot_num = clip_info["file"].replace("shot_", "").replace(".mp4", "")
        cameras_text = f" ({clip_info.get('cameras', 1)} cam)" if clip_info.get("cameras", 1) > 1 else ""
        label = QLabel(f"Shot {int(shot_num)}{cameras_text}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #ccc; font-size: 11px;")
        layout.addWidget(label)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _update_style(self):
        if self.selected:
            self.setStyleSheet("""
                QFrame { background-color: #3d5a80; border: 2px solid #4a9eff; border-radius: 8px; }
            """)
        else:
            self.setStyleSheet("""
                QFrame { background-color: #2d2d2d; border: 1px solid #444; border-radius: 8px; }
                QFrame:hover { border: 1px solid #4a9eff; background-color: #363636; }
            """)

    def set_selected(self, selected: bool):
        self.selected = selected
        self._update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2d2d2d; border: 1px solid #444; border-radius: 4px; padding: 4px; }
            QMenu::item { padding: 6px 20px; color: #ccc; }
            QMenu::item:selected { background-color: #4a9eff; color: white; }
        """)

        delete_action = menu.addAction("Delete Shot")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.index))

        not_shot_action = menu.addAction("Mark as Not a Shot")
        not_shot_action.triggered.connect(lambda: self.mark_not_shot_requested.emit(self.index))

        menu.exec(self.mapToGlobal(pos))


# ============================================================================
# Clip Gallery Widget
# ============================================================================

class ClipGallery(QScrollArea):
    """Scrollable gallery of shot thumbnails."""

    clip_selected = pyqtSignal(int)
    clip_deleted = pyqtSignal(int)
    clip_mark_not_shot = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("""
            QScrollArea { background-color: #1e1e1e; border: none; }
            QScrollBar:vertical {
                background-color: #1e1e1e; width: 10px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #444; border-radius: 5px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background-color: #555; }
        """)

        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.setWidget(self.container)

        self.thumbnails: List[ThumbnailWidget] = []
        self.selected_index = -1

    def add_clip(self, clip_info: Dict, thumbnail_path: Optional[Path]):
        index = len(self.thumbnails)
        thumb = ThumbnailWidget(index, clip_info, thumbnail_path)
        thumb.clicked.connect(self._on_thumbnail_clicked)
        thumb.delete_requested.connect(self._on_delete_requested)
        thumb.mark_not_shot_requested.connect(self._on_mark_not_shot)

        row = index // 3
        col = index % 3
        self.grid_layout.addWidget(thumb, row, col)
        self.thumbnails.append(thumb)

        self._on_thumbnail_clicked(index)

        QTimer.singleShot(100, lambda: self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        ))

    def refresh(self, clips: List[Dict], session_folder: Path):
        for thumb in self.thumbnails:
            self.grid_layout.removeWidget(thumb)
            thumb.deleteLater()
        self.thumbnails.clear()
        self.selected_index = -1

        for i, clip_info in enumerate(clips):
            thumb_file = clip_info.get("thumbnail")
            thumb_path = session_folder / thumb_file if thumb_file else None

            thumb = ThumbnailWidget(i, clip_info, thumb_path)
            thumb.clicked.connect(self._on_thumbnail_clicked)
            thumb.delete_requested.connect(self._on_delete_requested)
            thumb.mark_not_shot_requested.connect(self._on_mark_not_shot)

            row = i // 3
            col = i % 3
            self.grid_layout.addWidget(thumb, row, col)
            self.thumbnails.append(thumb)

    def _on_thumbnail_clicked(self, index: int):
        if 0 <= self.selected_index < len(self.thumbnails):
            self.thumbnails[self.selected_index].set_selected(False)

        self.selected_index = index
        if 0 <= index < len(self.thumbnails):
            self.thumbnails[index].set_selected(True)

        self.clip_selected.emit(index)

    def _on_delete_requested(self, index: int):
        self.clip_deleted.emit(index)

    def _on_mark_not_shot(self, index: int):
        self.clip_mark_not_shot.emit(index)


# ============================================================================
# Log Panel Handler
# ============================================================================

class QTextEditLogHandler(logging.Handler):
    """Logging handler that writes to a QTextEdit widget via signal."""

    class _Emitter(QWidget):
        log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._emitter = self._Emitter()
        self.max_lines = 500

    @property
    def signal(self):
        return self._emitter.log_signal

    def emit(self, record):
        msg = self.format(record)
        self._emitter.log_signal.emit(msg)


class LogPanel(QWidget):
    """Scrollable log output panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a; color: #aaa;
                border: none; font-family: Consolas, monospace; font-size: 11px;
            }
        """)
        layout.addWidget(self.text_edit)

        clear_btn = QPushButton("Clear Log")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d; color: #ccc;
                border: 1px solid #555; border-radius: 4px; padding: 4px 8px;
            }
            QPushButton:hover { background-color: #4d4d4d; }
        """)
        clear_btn.clicked.connect(self.text_edit.clear)
        layout.addWidget(clear_btn)

        self._max_lines = 500

    def append_log(self, message: str):
        self.text_edit.append(message)
        # Trim excess lines
        doc = self.text_edit.document()
        if doc.blockCount() > self._max_lines:
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(
                QTextCursor.MoveOperation.Down,
                QTextCursor.MoveMode.KeepAnchor,
                doc.blockCount() - self._max_lines,
            )
            cursor.removeSelectedText()
        # Scroll to bottom
        sb = self.text_edit.verticalScrollBar()
        sb.setValue(sb.maximum())
