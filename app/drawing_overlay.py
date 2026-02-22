"""
Drawing overlay system for Golf Swing Capture.
Provides line and circle drawing tools rendered on top of the video feed.
Coordinates are normalized 0.0-1.0 relative to video frame.
"""

import math
import logging
from typing import Optional, List

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QMouseEvent

logger = logging.getLogger(__name__)

# Hit-test distance (pixels)
HIT_DISTANCE = 10
HANDLE_RADIUS = 6


# ============================================================================
# Shape Data Classes
# ============================================================================

class Shape:
    """Base shape with normalized coordinates (0.0-1.0)."""

    def __init__(self, color: str = "#ff0000", thickness: int = 2):
        self.color = color
        self.thickness = thickness
        self.selected = False

    def to_dict(self) -> dict:
        raise NotImplementedError

    @staticmethod
    def from_dict(data: dict) -> "Shape":
        t = data.get("type")
        if t == "line":
            return LineShape.from_dict(data)
        elif t == "circle":
            return CircleShape.from_dict(data)
        return None

    def hit_test(self, nx: float, ny: float, vw: int, vh: int) -> bool:
        raise NotImplementedError

    def draw(self, painter: QPainter, vx: int, vy: int, vw: int, vh: int):
        raise NotImplementedError

    def draw_handles(self, painter: QPainter, vx: int, vy: int, vw: int, vh: int):
        raise NotImplementedError

    def move(self, dx: float, dy: float):
        raise NotImplementedError

    def get_handle_at(self, nx: float, ny: float, vw: int, vh: int) -> Optional[str]:
        return None

    def move_handle(self, handle: str, nx: float, ny: float):
        raise NotImplementedError


class LineShape(Shape):
    def __init__(self, x1=0.0, y1=0.0, x2=1.0, y2=1.0, color="#ff0000", thickness=2, rotation=0.0):
        super().__init__(color, thickness)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.rotation = rotation

    def to_dict(self) -> dict:
        return {
            "type": "line",
            "x1": self.x1, "y1": self.y1,
            "x2": self.x2, "y2": self.y2,
            "color": self.color, "thickness": self.thickness,
            "rotation": self.rotation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LineShape":
        return cls(
            x1=data.get("x1", 0), y1=data.get("y1", 0),
            x2=data.get("x2", 1), y2=data.get("y2", 1),
            color=data.get("color", "#ff0000"),
            thickness=data.get("thickness", 2),
            rotation=data.get("rotation", 0),
        )

    def _get_rotated_points(self):
        """Get endpoints after applying rotation around midpoint."""
        if self.rotation == 0:
            return self.x1, self.y1, self.x2, self.y2
        cx = (self.x1 + self.x2) / 2
        cy = (self.y1 + self.y2) / 2
        angle = math.radians(self.rotation)
        cos_a, sin_a = math.cos(angle), math.sin(angle)

        def rotate(px, py):
            dx, dy = px - cx, py - cy
            return cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a

        rx1, ry1 = rotate(self.x1, self.y1)
        rx2, ry2 = rotate(self.x2, self.y2)
        return rx1, ry1, rx2, ry2

    def hit_test(self, nx: float, ny: float, vw: int, vh: int) -> bool:
        rx1, ry1, rx2, ry2 = self._get_rotated_points()
        px, py = nx * vw, ny * vh
        ax, ay = rx1 * vw, ry1 * vh
        bx, by = rx2 * vw, ry2 * vh
        return _point_to_line_dist(px, py, ax, ay, bx, by) < HIT_DISTANCE

    def draw(self, painter: QPainter, vx: int, vy: int, vw: int, vh: int):
        rx1, ry1, rx2, ry2 = self._get_rotated_points()
        pen = QPen(QColor(self.color), self.thickness)
        painter.setPen(pen)
        painter.drawLine(
            int(vx + rx1 * vw), int(vy + ry1 * vh),
            int(vx + rx2 * vw), int(vy + ry2 * vh),
        )

    def draw_handles(self, painter: QPainter, vx: int, vy: int, vw: int, vh: int):
        rx1, ry1, rx2, ry2 = self._get_rotated_points()
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(QColor(self.color))
        for px, py in [(rx1, ry1), (rx2, ry2)]:
            painter.drawEllipse(
                QPointF(vx + px * vw, vy + py * vh), HANDLE_RADIUS, HANDLE_RADIUS
            )
        # Rotation handle at midpoint offset
        mx, my = (rx1 + rx2) / 2, (ry1 + ry2) / 2
        # Offset perpendicular to line
        dx, dy = rx2 - rx1, ry2 - ry1
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0.001:
            offset = 0.03
            rx = mx + (-dy / length) * offset
            ry_h = my + (dx / length) * offset
            painter.setBrush(QColor("#ffff00"))
            painter.drawEllipse(
                QPointF(vx + rx * vw, vy + ry_h * vh), HANDLE_RADIUS - 1, HANDLE_RADIUS - 1
            )

    def get_handle_at(self, nx: float, ny: float, vw: int, vh: int) -> Optional[str]:
        rx1, ry1, rx2, ry2 = self._get_rotated_points()
        r = HIT_DISTANCE / max(vw, vh, 1)
        if _dist(nx, ny, rx1, ry1) < r:
            return "p1"
        if _dist(nx, ny, rx2, ry2) < r:
            return "p2"
        # Rotation handle
        mx, my = (rx1 + rx2) / 2, (ry1 + ry2) / 2
        dx, dy = rx2 - rx1, ry2 - ry1
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0.001:
            offset = 0.03
            rhx = mx + (-dy / length) * offset
            rhy = my + (dx / length) * offset
            if _dist(nx, ny, rhx, rhy) < r:
                return "rotate"
        return None

    def move_handle(self, handle: str, nx: float, ny: float):
        if handle == "p1":
            self.x1 = nx
            self.y1 = ny
        elif handle == "p2":
            self.x2 = nx
            self.y2 = ny
        elif handle == "rotate":
            cx = (self.x1 + self.x2) / 2
            cy = (self.y1 + self.y2) / 2
            dx = self.x2 - self.x1
            dy = self.y2 - self.y1
            if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                return
            angle = math.degrees(math.atan2(ny - cy, nx - cx))
            base_angle = math.degrees(math.atan2(-dx / 2, dy / 2))
            self.rotation = angle - base_angle

    def move(self, dx: float, dy: float):
        self.x1 += dx
        self.y1 += dy
        self.x2 += dx
        self.y2 += dy


class CircleShape(Shape):
    def __init__(self, cx=0.5, cy=0.5, radius=0.1, color="#00ff00", thickness=2):
        super().__init__(color, thickness)
        self.cx = cx
        self.cy = cy
        self.radius = radius

    def to_dict(self) -> dict:
        return {
            "type": "circle",
            "cx": self.cx, "cy": self.cy,
            "radius": self.radius,
            "color": self.color, "thickness": self.thickness,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CircleShape":
        return cls(
            cx=data.get("cx", 0.5), cy=data.get("cy", 0.5),
            radius=data.get("radius", 0.1),
            color=data.get("color", "#00ff00"),
            thickness=data.get("thickness", 2),
        )

    def hit_test(self, nx: float, ny: float, vw: int, vh: int) -> bool:
        # Check if near circumference
        d = _dist(nx, ny, self.cx, self.cy)
        r_pixels = self.radius * max(vw, vh)
        d_pixels = d * max(vw, vh)
        return abs(d_pixels - r_pixels) < HIT_DISTANCE

    def draw(self, painter: QPainter, vx: int, vy: int, vw: int, vh: int):
        pen = QPen(QColor(self.color), self.thickness)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        r_px = self.radius * max(vw, vh)
        painter.drawEllipse(
            QPointF(vx + self.cx * vw, vy + self.cy * vh), r_px, r_px
        )

    def draw_handles(self, painter: QPainter, vx: int, vy: int, vw: int, vh: int):
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(QColor(self.color))
        # Center handle
        painter.drawEllipse(
            QPointF(vx + self.cx * vw, vy + self.cy * vh), HANDLE_RADIUS, HANDLE_RADIUS
        )
        # Edge handle (right)
        r_px = self.radius * max(vw, vh)
        painter.drawEllipse(
            QPointF(vx + self.cx * vw + r_px, vy + self.cy * vh), HANDLE_RADIUS, HANDLE_RADIUS
        )

    def get_handle_at(self, nx: float, ny: float, vw: int, vh: int) -> Optional[str]:
        r = HIT_DISTANCE / max(vw, vh, 1)
        if _dist(nx, ny, self.cx, self.cy) < r:
            return "center"
        # Edge handle
        edge_x = self.cx + self.radius * max(vw, vh) / max(vw, vh)
        if _dist(nx, ny, edge_x, self.cy) < r:
            return "edge"
        return None

    def move_handle(self, handle: str, nx: float, ny: float):
        if handle == "center":
            self.cx = nx
            self.cy = ny
        elif handle == "edge":
            self.radius = _dist(nx, ny, self.cx, self.cy)

    def move(self, dx: float, dy: float):
        self.cx += dx
        self.cy += dy


# ============================================================================
# Drawing Overlay Widget
# ============================================================================

class DrawingOverlay(QWidget):
    """Transparent overlay widget for drawing shapes on top of the video."""

    shapes_changed = pyqtSignal()

    # Drawing modes
    MODE_SELECT = "select"
    MODE_LINE = "line"
    MODE_CIRCLE = "circle"

    # Color palette
    COLORS = ["#ff0000", "#f0c040", "#34d17e", "#a855f7"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.shapes: List[Shape] = []
        self.mode = self.MODE_SELECT
        self.current_color = self.COLORS[0]

        self._selected_shape: Optional[Shape] = None
        self._drag_start: Optional[QPointF] = None
        self._drag_handle: Optional[str] = None
        self._creating_shape: Optional[Shape] = None
        self._video_rect = QRectF(0, 0, 1, 1)  # Will be set by parent

    def set_video_rect(self, x: int, y: int, w: int, h: int):
        """Set the region of the widget that corresponds to the video frame."""
        self._video_rect = QRectF(x, y, w, h)
        self.update()

    def load_shapes(self, shape_dicts: List[dict]):
        self.shapes.clear()
        for d in shape_dicts:
            s = Shape.from_dict(d)
            if s:
                self.shapes.append(s)
            else:
                logger.warning("Failed to deserialize shape: %s", d)
        self.update()

    def save_shapes(self) -> List[dict]:
        return [s.to_dict() for s in self.shapes]

    def clear_all(self):
        self.shapes.clear()
        self._selected_shape = None
        self.shapes_changed.emit()
        self.update()

    def delete_selected(self):
        if self._selected_shape and self._selected_shape in self.shapes:
            self.shapes.remove(self._selected_shape)
            self._selected_shape = None
            self.shapes_changed.emit()
            self.update()

    def set_mode(self, mode: str):
        self.mode = mode
        if mode != self.MODE_SELECT:
            self._deselect_all()
        self.update()

    def change_selected_color(self, color: str):
        if self._selected_shape:
            self._selected_shape.color = color
            self.shapes_changed.emit()
            self.update()

    def _deselect_all(self):
        for s in self.shapes:
            s.selected = False
        self._selected_shape = None

    def _pixel_to_norm(self, pos) -> tuple:
        """Convert widget pixel position to normalized video coordinates."""
        vr = self._video_rect
        if vr.width() < 1 or vr.height() < 1:
            return 0.0, 0.0
        nx = (pos.x() - vr.x()) / vr.width()
        ny = (pos.y() - vr.y()) / vr.height()
        return nx, ny

    # --- Mouse events ---

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        nx, ny = self._pixel_to_norm(event.position())
        vw = int(self._video_rect.width())
        vh = int(self._video_rect.height())

        if self.mode == self.MODE_SELECT:
            # Check handles first
            if self._selected_shape:
                handle = self._selected_shape.get_handle_at(nx, ny, vw, vh)
                if handle:
                    self._drag_handle = handle
                    self._drag_start = QPointF(nx, ny)
                    return

            # Hit test shapes
            clicked = None
            for s in reversed(self.shapes):
                if s.hit_test(nx, ny, vw, vh):
                    clicked = s
                    break

            self._deselect_all()
            if clicked:
                clicked.selected = True
                self._selected_shape = clicked
                self._drag_start = QPointF(nx, ny)
            self.update()

        elif self.mode == self.MODE_LINE:
            self._creating_shape = LineShape(nx, ny, nx, ny, self.current_color)
            self._drag_start = QPointF(nx, ny)

        elif self.mode == self.MODE_CIRCLE:
            self._creating_shape = CircleShape(nx, ny, 0.0, self.current_color)
            self._drag_start = QPointF(nx, ny)

    def mouseMoveEvent(self, event: QMouseEvent):
        nx, ny = self._pixel_to_norm(event.position())

        if self._drag_handle and self._selected_shape:
            self._selected_shape.move_handle(self._drag_handle, nx, ny)
            self.update()
            return

        if self._creating_shape:
            if isinstance(self._creating_shape, LineShape):
                self._creating_shape.x2 = nx
                self._creating_shape.y2 = ny
            elif isinstance(self._creating_shape, CircleShape):
                self._creating_shape.radius = _dist(nx, ny, self._creating_shape.cx, self._creating_shape.cy)
            self.update()
            return

        if self._drag_start and self._selected_shape and self.mode == self.MODE_SELECT:
            dx = nx - self._drag_start.x()
            dy = ny - self._drag_start.y()
            self._selected_shape.move(dx, dy)
            self._drag_start = QPointF(nx, ny)
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self._creating_shape:
            # Finalize shape
            if isinstance(self._creating_shape, LineShape):
                dx = self._creating_shape.x2 - self._creating_shape.x1
                dy = self._creating_shape.y2 - self._creating_shape.y1
                if math.sqrt(dx * dx + dy * dy) > 0.01:
                    self.shapes.append(self._creating_shape)
                    self.shapes_changed.emit()
            elif isinstance(self._creating_shape, CircleShape):
                if self._creating_shape.radius > 0.005:
                    self.shapes.append(self._creating_shape)
                    self.shapes_changed.emit()
            self._creating_shape = None
            self.update()
            return

        if self._drag_start or self._drag_handle:
            self.shapes_changed.emit()

        self._drag_start = None
        self._drag_handle = None

    def paintEvent(self, event):
        if not self.shapes and not self._creating_shape:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        vx = int(self._video_rect.x())
        vy = int(self._video_rect.y())
        vw = int(self._video_rect.width())
        vh = int(self._video_rect.height())

        for shape in self.shapes:
            shape.draw(painter, vx, vy, vw, vh)
            if shape.selected:
                shape.draw_handles(painter, vx, vy, vw, vh)

        if self._creating_shape:
            self._creating_shape.draw(painter, vx, vy, vw, vh)

        painter.end()


# ============================================================================
# Helpers
# ============================================================================

def _dist(x1, y1, x2, y2) -> float:
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def _point_to_line_dist(px, py, ax, ay, bx, by) -> float:
    """Distance from point (px,py) to line segment (ax,ay)-(bx,by)."""
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-10:
        return _dist(px, py, ax, ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return _dist(px, py, proj_x, proj_y)
