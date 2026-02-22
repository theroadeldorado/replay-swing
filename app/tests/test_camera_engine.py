"""Tests for camera_engine.py — CameraCapture transforms, droidcam_url,
PersonDetector init, and test_network_camera failure path."""

import numpy as np
import pytest

from config import CameraPreset
from camera_engine import CameraCapture, droidcam_url, PersonDetector
from camera_engine import test_network_camera as _test_network_camera


# ---------------------------------------------------------------------------
# 1. droidcam_url builds the expected MJPEG URL
# ---------------------------------------------------------------------------

def test_droidcam_url():
    """droidcam_url should return the standard DroidCam MJPEG feed URL."""
    url = droidcam_url("192.168.1.50")
    assert url == "http://192.168.1.50:4747/mjpegfeed"


# ---------------------------------------------------------------------------
# 2. _apply_transforms with default preset is a no-op
# ---------------------------------------------------------------------------

def test_apply_transforms_no_op():
    """With default preset (zoom=1, rotation=0, no flip), the frame should
    pass through unchanged in shape and content."""
    preset = CameraPreset(id=0)
    cap = CameraCapture(camera_id=0, fps=30, preset=preset)

    frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    original = frame.copy()
    result = cap._apply_transforms(frame)

    assert result.shape == original.shape
    np.testing.assert_array_equal(result, original)


# ---------------------------------------------------------------------------
# 3. _apply_transforms zoom: center crop + resize keeps dimensions
# ---------------------------------------------------------------------------

def test_apply_transforms_zoom():
    """Zoom > 1.0 should center-crop then resize back to original dimensions."""
    preset = CameraPreset(id=0)
    cap = CameraCapture(camera_id=0, fps=30, preset=preset)
    cap.set_zoom(2.0)

    frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    result = cap._apply_transforms(frame)

    assert result.shape == (100, 100, 3), (
        "Zoomed frame must retain original dimensions after resize"
    )


# ---------------------------------------------------------------------------
# 4. _apply_transforms rotation 90 swaps width and height
# ---------------------------------------------------------------------------

def test_apply_transforms_rotation_90():
    """90-degree rotation should swap width and height."""
    preset = CameraPreset(id=0, rotation=90)
    cap = CameraCapture(camera_id=0, fps=30, preset=preset)

    frame = np.zeros((200, 100, 3), dtype=np.uint8)  # h=200, w=100
    result = cap._apply_transforms(frame)

    assert result.shape == (100, 200, 3), (
        "90-degree rotation should produce h=100, w=200"
    )


# ---------------------------------------------------------------------------
# 5. _apply_transforms flip_h swaps left and right
# ---------------------------------------------------------------------------

def test_apply_transforms_flip_h():
    """Horizontal flip should mirror columns: left pixel becomes right."""
    preset = CameraPreset(id=0, flip_h=True)
    cap = CameraCapture(camera_id=0, fps=30, preset=preset)

    # Create a 1-row, 2-column frame where left != right
    frame = np.zeros((1, 2, 3), dtype=np.uint8)
    frame[0, 0] = [10, 20, 30]   # left pixel
    frame[0, 1] = [200, 210, 220]  # right pixel

    result = cap._apply_transforms(frame)

    np.testing.assert_array_equal(result[0, 0], [200, 210, 220],
                                  err_msg="Left pixel should now be the original right pixel")
    np.testing.assert_array_equal(result[0, 1], [10, 20, 30],
                                  err_msg="Right pixel should now be the original left pixel")


# ---------------------------------------------------------------------------
# 6. _apply_transforms flip_v swaps top and bottom
# ---------------------------------------------------------------------------

def test_apply_transforms_flip_v():
    """Vertical flip should mirror rows: top pixel becomes bottom."""
    preset = CameraPreset(id=0, flip_v=True)
    cap = CameraCapture(camera_id=0, fps=30, preset=preset)

    # Create a 2-row, 1-column frame where top != bottom
    frame = np.zeros((2, 1, 3), dtype=np.uint8)
    frame[0, 0] = [10, 20, 30]   # top pixel
    frame[1, 0] = [200, 210, 220]  # bottom pixel

    result = cap._apply_transforms(frame)

    np.testing.assert_array_equal(result[0, 0], [200, 210, 220],
                                  err_msg="Top pixel should now be the original bottom pixel")
    np.testing.assert_array_equal(result[1, 0], [10, 20, 30],
                                  err_msg="Bottom pixel should now be the original top pixel")


# ---------------------------------------------------------------------------
# 7. PersonDetector initializes with person_present = False
# ---------------------------------------------------------------------------

def test_person_detector_init():
    """A freshly created PersonDetector should report no person present."""
    detector = PersonDetector()
    assert detector.person_present is False


# ---------------------------------------------------------------------------
# 8. test_network_camera returns (False, str) for unreachable URL
# ---------------------------------------------------------------------------

def test_test_network_camera_failure():
    """test_network_camera with an unreachable address should return
    (False, message) without raising.  This also exercises the
    try/finally double-release fix."""
    success, message = _test_network_camera("http://127.0.0.1:1")

    assert success is False
    assert isinstance(message, str)
    assert len(message) > 0
