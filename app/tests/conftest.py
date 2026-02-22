"""Shared pytest fixtures for Golf Swing Replay tests."""

import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

# ---------------------------------------------------------------------------
# 1. sys_path -- ensure the project root is importable
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True, scope="session")
def sys_path():
    """Add the project root to sys.path so source modules can be imported."""
    root_str = str(PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


# Imports that depend on sys_path being set at module level are fine because
# conftest.py is loaded after sys.path manipulation during collection.  We
# perform the actual project imports lazily inside fixtures so that the
# session-scoped sys_path fixture has already executed.

# ---------------------------------------------------------------------------
# 2. app_config -- lightweight AppConfig backed by a temp directory
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def app_config(tmp_path):
    """Create an AppConfig whose session_folder points to a temp directory."""
    from config import AppConfig

    config = AppConfig(session_folder=str(tmp_path / "test_session"))
    return config


# ---------------------------------------------------------------------------
# 3. recording_manager -- RecordingManager wired to the temp-backed config
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def recording_manager(app_config):
    """Create a RecordingManager using the temporary app_config."""
    from recording import RecordingManager

    return RecordingManager(app_config)


# ---------------------------------------------------------------------------
# 4. sample_frames -- 30 distinguishable BGR frames
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def sample_frames():
    """Return a list of 30 numpy frames (480x640x3, uint8).

    Each frame has a unique grey shade and the frame number drawn on it so
    that individual frames are visually distinguishable.
    """
    frames = []
    for i in range(30):
        shade = int(255 * i / 29)  # 0 .. 255
        frame = np.full((480, 640, 3), shade, dtype=np.uint8)
        cv2.putText(
            frame,
            str(i),
            (260, 260),
            cv2.FONT_HERSHEY_SIMPLEX,
            3,
            (0, 0, 255),
            3,
            cv2.LINE_AA,
        )
        frames.append(frame)
    return frames


# ---------------------------------------------------------------------------
# 5. sample_frames_with_timestamps -- (frame, timestamp) tuples at 30 fps
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def sample_frames_with_timestamps(sample_frames):
    """Like *sample_frames* but returns ``[(frame, timestamp), ...]``.

    Timestamps are spaced 1/30 s apart starting from 1000.0.
    """
    return [
        (frame, 1000.0 + i / 30.0)
        for i, frame in enumerate(sample_frames)
    ]
