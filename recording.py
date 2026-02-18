"""
Recording manager and frame buffer for Golf Swing Capture.
"""

import json
import logging
import threading
import time
from pathlib import Path
from collections import deque
from typing import Optional, List, Dict

import cv2
import numpy as np

from config import AppConfig, TRAINING_DATA_DIR

logger = logging.getLogger(__name__)


# ============================================================================
# Frame Buffer Manager
# ============================================================================

class FrameBuffer:
    """Manages circular buffer for pre-trigger frames."""

    def __init__(self, duration: float, fps: int):
        self.max_frames = int(duration * fps)
        self.buffer: deque = deque(maxlen=self.max_frames)
        self._lock = threading.Lock()

    def add_frame(self, frame: np.ndarray, timestamp: float):
        with self._lock:
            self.buffer.append((frame.copy(), timestamp))

    def get_frames(self) -> List[tuple]:
        with self._lock:
            return list(self.buffer)

    def clear(self):
        with self._lock:
            self.buffer.clear()


# ============================================================================
# Recording Manager
# ============================================================================

class RecordingManager:
    """Manages the recording state and clip saving."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.session_folder = Path(config.session_folder)
        self.session_folder.mkdir(parents=True, exist_ok=True)

        self.shot_count = self._get_next_shot_number()
        self.clips: List[Dict] = []
        self._load_existing_clips()

    def _get_next_shot_number(self) -> int:
        existing = list(self.session_folder.glob("shot_*.mp4"))
        if not existing:
            return 1
        numbers = []
        for f in existing:
            try:
                num = int(f.stem.split("_")[1])
                numbers.append(num)
            except (IndexError, ValueError):
                pass
        return max(numbers, default=0) + 1

    def _load_existing_clips(self):
        clips_file = self.session_folder / "clips.json"
        if clips_file.exists():
            try:
                with open(clips_file, "r") as f:
                    self.clips = json.load(f)
            except Exception:
                self.clips = []

        for video_file in sorted(self.session_folder.glob("shot_*.mp4")):
            if not any(c.get("file") == video_file.name for c in self.clips):
                thumb_file = video_file.with_suffix(".jpg")
                self.clips.append({
                    "file": video_file.name,
                    "thumbnail": thumb_file.name if thumb_file.exists() else None,
                    "timestamp": video_file.stat().st_mtime,
                    "cameras": 1,
                })

    def _save_clips_metadata(self):
        clips_file = self.session_folder / "clips.json"
        with open(clips_file, "w") as f:
            json.dump(self.clips, f, indent=2)

    def save_clip(self, frames_by_camera: Dict, primary_camera, camera_labels: Dict = None) -> Optional[Dict]:
        """Save a multi-camera clip."""
        if not frames_by_camera:
            return None

        shot_name = f"shot_{self.shot_count:04d}"
        clip_info = {
            "file": f"{shot_name}.mp4",
            "timestamp": time.time(),
            "cameras": len(frames_by_camera),
            "camera_files": {},
            "camera_labels": camera_labels or {},
        }

        for cam_id, frames in frames_by_camera.items():
            if not frames:
                continue

            if cam_id == primary_camera:
                filename = f"{shot_name}.mp4"
            else:
                filename = f"{shot_name}_cam{cam_id}.mp4"

            filepath = self.session_folder / filename
            clip_info["camera_files"][str(cam_id)] = filename

            first_frame = frames[0][0]
            height, width = first_frame.shape[:2]

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(str(filepath), fourcc, self.config.fps, (width, height))

            for frame, _ in frames:
                out.write(frame)

            out.release()

            if cam_id == primary_camera and frames:
                mid_idx = len(frames) // 3
                thumb_frame = frames[mid_idx][0]
                thumb_path = self.session_folder / f"{shot_name}.jpg"

                thumb_h, thumb_w = self.config.thumbnail_size[1], self.config.thumbnail_size[0]
                thumb = cv2.resize(thumb_frame, (thumb_w, thumb_h))
                cv2.imwrite(str(thumb_path), thumb)
                clip_info["thumbnail"] = f"{shot_name}.jpg"

        self.clips.append(clip_info)
        self._save_clips_metadata()
        self.shot_count += 1

        logger.info("Saved shot %s (%d cameras)", shot_name, len(frames_by_camera))
        return clip_info

    def delete_clip(self, index: int) -> bool:
        """Delete a clip by index."""
        if 0 <= index < len(self.clips):
            clip = self.clips[index]

            if "camera_files" in clip:
                for filename in clip["camera_files"].values():
                    filepath = self.session_folder / filename
                    if filepath.exists():
                        filepath.unlink()
            else:
                filepath = self.session_folder / clip["file"]
                if filepath.exists():
                    filepath.unlink()

            if clip.get("thumbnail"):
                thumb_path = self.session_folder / clip["thumbnail"]
                if thumb_path.exists():
                    thumb_path.unlink()

            self.clips.pop(index)
            self._save_clips_metadata()
            logger.info("Deleted clip index %d", index)
            return True
        return False

    def mark_as_not_shot(self, index: int) -> bool:
        """Mark a clip as 'not a shot' - deletes video, relabels audio sample.

        Returns True if successful.
        """
        if not (0 <= index < len(self.clips)):
            return False

        clip = self.clips[index]

        # Delete video files
        if "camera_files" in clip:
            for filename in clip["camera_files"].values():
                filepath = self.session_folder / filename
                if filepath.exists():
                    filepath.unlink()
        else:
            filepath = self.session_folder / clip["file"]
            if filepath.exists():
                filepath.unlink()

        # Delete thumbnail
        if clip.get("thumbnail"):
            thumb_path = self.session_folder / clip["thumbnail"]
            if thumb_path.exists():
                thumb_path.unlink()

        # Relabel audio training sample if we can find it by timestamp
        trigger_ts = clip.get("trigger_timestamp")
        if trigger_ts:
            self._relabel_audio_sample(trigger_ts)

        # Mark in metadata
        clip["marked_not_shot"] = True
        self._save_clips_metadata()
        logger.info("Marked clip index %d as not a shot", index)
        return True

    def _relabel_audio_sample(self, trigger_timestamp: int):
        """Rename _shot.wav to _not_shot.wav and update metadata."""
        base_name = f"trigger_{trigger_timestamp}"
        shot_wav = TRAINING_DATA_DIR / f"{base_name}_shot.wav"
        not_shot_wav = TRAINING_DATA_DIR / f"{base_name}_not_shot.wav"
        meta_file = TRAINING_DATA_DIR / f"{base_name}_meta.json"

        if shot_wav.exists():
            shot_wav.rename(not_shot_wav)
            logger.info("Relabeled %s -> not_shot", base_name)

        if meta_file.exists():
            try:
                with open(meta_file, "r") as f:
                    meta = json.load(f)
                meta["label"] = 0
                with open(meta_file, "w") as f:
                    json.dump(meta, f, indent=2)
            except Exception as e:
                logger.warning("Failed to update meta for %s: %s", base_name, e)

    def get_visible_clips(self) -> List[Dict]:
        """Return clips that aren't marked as not-shot."""
        return [c for c in self.clips if not c.get("marked_not_shot")]

    def get_clip_path(self, index: int, camera_id=None) -> Optional[Path]:
        """Get the file path for a clip (index into visible clips)."""
        visible = self.get_visible_clips()
        if 0 <= index < len(visible):
            clip = visible[index]
            if camera_id is not None and "camera_files" in clip:
                filename = clip["camera_files"].get(str(camera_id))
                if filename:
                    return self.session_folder / filename
            return self.session_folder / clip["file"]
        return None

    def get_real_index(self, visible_index: int) -> int:
        """Convert visible clip index to real index in self.clips."""
        visible = self.get_visible_clips()
        if 0 <= visible_index < len(visible):
            target = visible[visible_index]
            for i, clip in enumerate(self.clips):
                if clip is target:
                    return i
        return -1
