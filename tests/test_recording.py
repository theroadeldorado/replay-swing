"""Tests for recording.py — FrameBuffer and RecordingManager."""

import json
from pathlib import Path

import cv2
import numpy as np
import pytest


# ============================================================================
# FrameBuffer tests
# ============================================================================


def test_frame_buffer_add_get():
    """Add frames to a FrameBuffer and verify get_frames returns them."""
    from recording import FrameBuffer

    buf = FrameBuffer(duration=1.0, fps=10)  # capacity = 10

    frames_in = []
    for i in range(5):
        frame = np.full((20, 20, 3), i, dtype=np.uint8)
        ts = 100.0 + i
        buf.add_frame(frame, ts)
        frames_in.append((frame, ts))

    result = buf.get_frames()

    assert len(result) == 5
    for (expected_frame, expected_ts), (actual_frame, actual_ts) in zip(
        frames_in, result
    ):
        np.testing.assert_array_equal(actual_frame, expected_frame)
        assert actual_ts == expected_ts


def test_frame_buffer_circular():
    """Adding more frames than maxlen keeps only the most recent ones."""
    from recording import FrameBuffer

    buf = FrameBuffer(duration=1.0, fps=4)  # capacity = 4

    for i in range(10):
        frame = np.full((10, 10, 3), i, dtype=np.uint8)
        buf.add_frame(frame, float(i))

    result = buf.get_frames()

    assert len(result) == 4
    # Should contain frames 6, 7, 8, 9
    for idx, (frame, ts) in enumerate(result):
        expected_value = 6 + idx
        assert ts == float(expected_value)
        assert frame[0, 0, 0] == expected_value


def test_frame_buffer_clear():
    """Clearing a FrameBuffer makes it empty."""
    from recording import FrameBuffer

    buf = FrameBuffer(duration=1.0, fps=10)

    for i in range(5):
        buf.add_frame(np.zeros((10, 10, 3), dtype=np.uint8), float(i))

    assert len(buf.get_frames()) == 5

    buf.clear()

    assert buf.get_frames() == []


# ============================================================================
# RecordingManager tests
# ============================================================================


def test_save_clip_single_camera(recording_manager, sample_frames_with_timestamps):
    """Saving a single-camera clip creates an MP4 and a JPG thumbnail."""
    frames_by_camera = {0: sample_frames_with_timestamps}
    clip_info = recording_manager.save_clip(
        frames_by_camera, primary_camera=0
    )

    assert clip_info is not None
    assert clip_info["file"] == "shot_0001.mp4"
    assert clip_info["cameras"] == 1

    session = Path(recording_manager.session_folder)
    assert (session / "shot_0001.mp4").exists()
    assert (session / "shot_0001.jpg").exists()

    # Verify the MP4 is a readable video with the correct frame count
    cap = cv2.VideoCapture(str(session / "shot_0001.mp4"))
    try:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        assert frame_count == len(sample_frames_with_timestamps)
    finally:
        cap.release()


def test_save_clip_multi_camera(recording_manager, sample_frames_with_timestamps):
    """Saving a multi-camera clip creates separate MP4 files per camera."""
    frames_by_camera = {
        0: sample_frames_with_timestamps,
        "cam1": sample_frames_with_timestamps,
    }
    clip_info = recording_manager.save_clip(
        frames_by_camera, primary_camera=0
    )

    assert clip_info is not None
    assert clip_info["cameras"] == 2

    session = Path(recording_manager.session_folder)
    # Primary camera -> shot_0001.mp4
    assert (session / "shot_0001.mp4").exists()
    # Secondary camera -> shot_0001_camcam1.mp4
    assert (session / "shot_0001_camcam1.mp4").exists()
    # Thumbnail from primary camera
    assert (session / "shot_0001.jpg").exists()

    # camera_files should reference both
    assert "0" in clip_info["camera_files"]
    assert "cam1" in clip_info["camera_files"]


def test_delete_clip(recording_manager, sample_frames_with_timestamps):
    """Deleting a clip removes its video and thumbnail files."""
    frames_by_camera = {0: sample_frames_with_timestamps}
    recording_manager.save_clip(frames_by_camera, primary_camera=0)

    session = Path(recording_manager.session_folder)
    assert (session / "shot_0001.mp4").exists()
    assert (session / "shot_0001.jpg").exists()

    result = recording_manager.delete_clip(0)

    assert result is True
    assert not (session / "shot_0001.mp4").exists()
    assert not (session / "shot_0001.jpg").exists()
    assert len(recording_manager.clips) == 0


def test_mark_as_not_shot(recording_manager, sample_frames_with_timestamps):
    """Marking a clip as not-shot sets the flag and deletes the video file."""
    frames_by_camera = {0: sample_frames_with_timestamps}
    recording_manager.save_clip(frames_by_camera, primary_camera=0)

    session = Path(recording_manager.session_folder)
    assert (session / "shot_0001.mp4").exists()

    result = recording_manager.mark_as_not_shot(0)

    assert result is True
    assert recording_manager.clips[0]["marked_not_shot"] is True
    assert not (session / "shot_0001.mp4").exists()
    assert not (session / "shot_0001.jpg").exists()


def test_get_visible_clips(recording_manager, sample_frames_with_timestamps):
    """get_visible_clips excludes clips marked as not-shot."""
    # Save two clips
    recording_manager.save_clip(
        {0: sample_frames_with_timestamps}, primary_camera=0
    )
    recording_manager.save_clip(
        {0: sample_frames_with_timestamps}, primary_camera=0
    )

    assert len(recording_manager.get_visible_clips()) == 2

    # Mark the first one as not-shot
    recording_manager.mark_as_not_shot(0)

    visible = recording_manager.get_visible_clips()
    assert len(visible) == 1
    assert visible[0]["file"] == "shot_0002.mp4"


def test_orphan_file_recovery(app_config):
    """_load_existing_clips only picks up primary shot files, not _camX files.

    When orphan MP4 files exist on disk without a clips.json entry, the
    RecordingManager should recover shot_NNNN.mp4 files but must ignore
    shot_NNNN_camX.mp4 files (those are secondary-camera files belonging
    to the primary clip, not standalone clips).
    """
    from recording import RecordingManager

    session = Path(app_config.session_folder)
    session.mkdir(parents=True, exist_ok=True)

    # Create stub MP4 files using cv2.VideoWriter
    stub_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    for filename in ("shot_0001.mp4", "shot_0001_cam1.mp4", "shot_0002.mp4"):
        filepath = session / filename
        writer = cv2.VideoWriter(str(filepath), fourcc, 30, (100, 100))
        writer.write(stub_frame)
        writer.release()

    # No clips.json exists — RecordingManager should discover orphan files
    rm = RecordingManager(app_config)

    # Only the two primary files should have been loaded
    assert len(rm.clips) == 2
    loaded_files = {c["file"] for c in rm.clips}
    assert "shot_0001.mp4" in loaded_files
    assert "shot_0002.mp4" in loaded_files
    assert "shot_0001_cam1.mp4" not in loaded_files
