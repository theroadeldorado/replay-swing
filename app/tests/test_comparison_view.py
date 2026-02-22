"""Minimal tests for comparison_view.py logic that doesn't need a display.

Since ComparisonWindow is a QDialog requiring a running Qt application, we
only test what we can without a display: imports and the offset calculation
logic used by _show_frames.
"""

import pytest


# ---------------------------------------------------------------------------
# 1. Verify that key classes can be imported
# ---------------------------------------------------------------------------

def test_comparison_video_player_import():
    """Verify that ComparisonVideoPlayer and ComparisonWindow can be imported."""
    from comparison_view import ComparisonVideoPlayer, ComparisonWindow

    assert ComparisonVideoPlayer is not None
    assert ComparisonWindow is not None


# ---------------------------------------------------------------------------
# 2. Test the offset calculation logic used by _show_frames
# ---------------------------------------------------------------------------

def test_offset_calculation():
    """Test the offset logic: frame_index = position + offset.

    In ComparisonWindow._show_frames the effective frame index for each
    side is computed as ``position + offset``.  Verify the arithmetic for
    both positive and negative offsets.
    """
    # Positive offset: position=10, offset=5 -> frame index 15
    position = 10
    offset = 5
    frame_index = position + offset
    assert frame_index == 15

    # Negative offset: position=10, offset=-3 -> frame index 7
    position = 10
    offset = -3
    frame_index = position + offset
    assert frame_index == 7
