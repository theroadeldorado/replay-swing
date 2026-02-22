"""Tests for drawing_overlay.py shapes (no GUI, just the shape data classes)."""

import pytest

from drawing_overlay import LineShape, CircleShape, Shape


# ---------------------------------------------------------------------------
# 1. LineShape round-trip via to_dict / from_dict
# ---------------------------------------------------------------------------

def test_line_shape_to_dict_from_dict():
    """Round-trip through to_dict then from_dict preserves all attributes."""
    line = LineShape(x1=0.1, y1=0.2, x2=0.8, y2=0.9,
                     color="#00ff00", thickness=3, rotation=45.0)
    d = line.to_dict()
    restored = LineShape.from_dict(d)

    assert restored.x1 == pytest.approx(0.1)
    assert restored.y1 == pytest.approx(0.2)
    assert restored.x2 == pytest.approx(0.8)
    assert restored.y2 == pytest.approx(0.9)
    assert restored.color == "#00ff00"
    assert restored.thickness == 3
    assert restored.rotation == pytest.approx(45.0)
    assert d["type"] == "line"


# ---------------------------------------------------------------------------
# 2. CircleShape round-trip via to_dict / from_dict
# ---------------------------------------------------------------------------

def test_circle_shape_to_dict_from_dict():
    """Round-trip through to_dict then from_dict preserves all attributes."""
    circle = CircleShape(cx=0.3, cy=0.7, radius=0.15,
                         color="#0000ff", thickness=4)
    d = circle.to_dict()
    restored = CircleShape.from_dict(d)

    assert restored.cx == pytest.approx(0.3)
    assert restored.cy == pytest.approx(0.7)
    assert restored.radius == pytest.approx(0.15)
    assert restored.color == "#0000ff"
    assert restored.thickness == 4
    assert d["type"] == "circle"


# ---------------------------------------------------------------------------
# 3. Shape.from_dict dispatches type="line" to LineShape
# ---------------------------------------------------------------------------

def test_shape_from_dict_line():
    """Shape.from_dict with type='line' returns a LineShape instance."""
    data = {
        "type": "line",
        "x1": 0.0, "y1": 0.0,
        "x2": 1.0, "y2": 1.0,
        "color": "#ff0000",
        "thickness": 2,
        "rotation": 0.0,
    }
    shape = Shape.from_dict(data)

    assert isinstance(shape, LineShape)
    assert shape.x1 == pytest.approx(0.0)
    assert shape.x2 == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 4. Shape.from_dict dispatches type="circle" to CircleShape
# ---------------------------------------------------------------------------

def test_shape_from_dict_circle():
    """Shape.from_dict with type='circle' returns a CircleShape instance."""
    data = {
        "type": "circle",
        "cx": 0.5, "cy": 0.5,
        "radius": 0.2,
        "color": "#00ff00",
        "thickness": 2,
    }
    shape = Shape.from_dict(data)

    assert isinstance(shape, CircleShape)
    assert shape.cx == pytest.approx(0.5)
    assert shape.radius == pytest.approx(0.2)


# ---------------------------------------------------------------------------
# 5. Shape.from_dict with unknown type returns None
# ---------------------------------------------------------------------------

def test_shape_from_dict_unknown():
    """Shape.from_dict with type='unknown' returns None."""
    data = {"type": "unknown", "x": 0.5, "y": 0.5}
    result = Shape.from_dict(data)

    assert result is None


# ---------------------------------------------------------------------------
# 6. LineShape hit_test near midpoint of diagonal line returns True
# ---------------------------------------------------------------------------

def test_line_hit_test():
    """Hit test near the midpoint of a diagonal line should return True."""
    line = LineShape(x1=0.1, y1=0.1, x2=0.9, y2=0.9)
    # Midpoint is (0.5, 0.5); test exactly there
    assert line.hit_test(0.5, 0.5, vw=1000, vh=1000) is True


# ---------------------------------------------------------------------------
# 7. LineShape hit_test far from line returns False
# ---------------------------------------------------------------------------

def test_line_hit_test_miss():
    """Hit test at a point far from the diagonal line should return False."""
    line = LineShape(x1=0.1, y1=0.1, x2=0.9, y2=0.9)
    # (0.1, 0.9) is far from the y=x diagonal
    assert line.hit_test(0.1, 0.9, vw=1000, vh=1000) is False


# ---------------------------------------------------------------------------
# 8. CircleShape hit_test on circumference returns True
# ---------------------------------------------------------------------------

def test_circle_hit_test():
    """Hit test on the circumference of a circle should return True."""
    circle = CircleShape(cx=0.5, cy=0.5, radius=0.2)
    # Point on circumference: (0.7, 0.5) is exactly 0.2 from center
    assert circle.hit_test(0.7, 0.5, vw=1000, vh=1000) is True


# ---------------------------------------------------------------------------
# 9. LineShape move shifts both endpoints
# ---------------------------------------------------------------------------

def test_line_move():
    """Moving a line by (0.1, 0.1) shifts both endpoints accordingly."""
    line = LineShape(x1=0.2, y1=0.3, x2=0.6, y2=0.7)
    line.move(0.1, 0.1)

    assert line.x1 == pytest.approx(0.3)
    assert line.y1 == pytest.approx(0.4)
    assert line.x2 == pytest.approx(0.7)
    assert line.y2 == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# 10. CircleShape move shifts center
# ---------------------------------------------------------------------------

def test_circle_move():
    """Moving a circle by (0.1, 0.1) shifts the center accordingly."""
    circle = CircleShape(cx=0.5, cy=0.5, radius=0.2)
    circle.move(0.1, 0.1)

    assert circle.cx == pytest.approx(0.6)
    assert circle.cy == pytest.approx(0.6)
    # Radius should be unchanged
    assert circle.radius == pytest.approx(0.2)


# ---------------------------------------------------------------------------
# 11. LineShape handle manipulation — move p1 endpoint
# ---------------------------------------------------------------------------

def test_line_handle_manipulation():
    """Get handle at p1 position and move it; verify endpoint moved."""
    line = LineShape(x1=0.1, y1=0.1, x2=0.9, y2=0.9)
    vw, vh = 1000, 1000

    # get_handle_at the p1 endpoint position should return "p1"
    handle = line.get_handle_at(0.1, 0.1, vw, vh)
    assert handle == "p1"

    # Move that handle to a new position
    line.move_handle("p1", 0.3, 0.4)

    assert line.x1 == pytest.approx(0.3)
    assert line.y1 == pytest.approx(0.4)
    # p2 should be unchanged
    assert line.x2 == pytest.approx(0.9)
    assert line.y2 == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# 12. CircleShape handle manipulation — move center handle
# ---------------------------------------------------------------------------

def test_circle_handle_manipulation():
    """Move the center handle of a circle; verify cx/cy changed."""
    circle = CircleShape(cx=0.5, cy=0.5, radius=0.2)
    vw, vh = 1000, 1000

    # get_handle_at the center position should return "center"
    handle = circle.get_handle_at(0.5, 0.5, vw, vh)
    assert handle == "center"

    # Move center handle to a new position
    circle.move_handle("center", 0.7, 0.3)

    assert circle.cx == pytest.approx(0.7)
    assert circle.cy == pytest.approx(0.3)
    # Radius should be unchanged
    assert circle.radius == pytest.approx(0.2)
