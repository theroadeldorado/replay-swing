"""
Camera capture engine with person detection, network camera support,
and per-camera transforms (zoom, rotate, flip).
"""

import logging
import socket
import time
import threading
from typing import Optional, List, Dict, Any

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from config import AppConfig, CameraPreset

logger = logging.getLogger(__name__)


# ============================================================================
# Camera Capture Thread
# ============================================================================

class CameraCapture(QThread):
    """Thread for capturing video from a USB or network camera."""

    frame_ready = pyqtSignal(object, np.ndarray, float)  # camera_id (int or str), frame, timestamp

    def __init__(self, camera_id, fps: int = 30, preset: Optional[CameraPreset] = None):
        super().__init__()
        self.camera_id = camera_id
        self.fps = fps
        self.preset = preset or CameraPreset(id=camera_id)
        self.running = False
        self.cap = None

        self._lock = threading.Lock()
        self._zoom = self.preset.zoom
        self._rotation = self.preset.rotation
        self._flip_h = self.preset.flip_h
        self._flip_v = self.preset.flip_v

    # --- Transform setters (thread-safe) ---

    def set_zoom(self, zoom: float):
        with self._lock:
            self._zoom = max(1.0, min(4.0, zoom))

    def set_rotation(self, degrees: int):
        with self._lock:
            self._rotation = degrees % 360

    def set_flip_h(self, flip: bool):
        with self._lock:
            self._flip_h = flip

    def set_flip_v(self, flip: bool):
        with self._lock:
            self._flip_v = flip

    def run(self):
        self.running = True
        is_network = isinstance(self.camera_id, str)

        logger.info("Camera thread starting for %s (network=%s)", self.camera_id, is_network)

        if is_network:
            self.cap = self._open_network_camera(self.camera_id)
        else:
            self.cap = self._open_usb_camera(self.camera_id)

        if self.cap is None or not self.cap.isOpened():
            logger.error("Failed to open camera %s", self.camera_id)
            if is_network:
                self._reconnect_loop()
            return

        logger.info("Camera %s opened successfully", self.camera_id)

        if not is_network:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        # Log first frame attempt
        ret, frame = self.cap.read()
        if ret:
            logger.info("Camera %s: first frame OK (%dx%d)", self.camera_id, frame.shape[1], frame.shape[0])
            frame = self._apply_transforms(frame)
            self.frame_ready.emit(self.camera_id, frame, time.time())
        else:
            logger.warning("Camera %s: first frame read FAILED", self.camera_id)

        frame_interval = 1.0 / self.fps
        consecutive_failures = 0
        total_frames = 1 if ret else 0

        while self.running:
            start_time = time.time()

            ret, frame = self.cap.read()
            if ret:
                consecutive_failures = 0
                total_frames += 1
                frame = self._apply_transforms(frame)
                timestamp = time.time()
                self.frame_ready.emit(self.camera_id, frame, timestamp)

                # Log periodically
                if total_frames == 30:
                    logger.info("Camera %s: receiving frames OK (30 frames captured)", self.camera_id)
            else:
                consecutive_failures += 1
                if consecutive_failures == 1:
                    logger.debug("Camera %s: frame read failed (consecutive: %d)", self.camera_id, consecutive_failures)
                if is_network and consecutive_failures > 30:
                    logger.warning("Camera %s: %d consecutive failures, reconnecting...", self.camera_id, consecutive_failures)
                    self.cap.release()
                    self._reconnect_loop()
                    if not self.running:
                        return
                    consecutive_failures = 0
                    total_frames = 0

            elapsed = time.time() - start_time
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        logger.info("Camera %s thread stopping (total frames: %d)", self.camera_id, total_frames)
        if self.cap:
            self.cap.release()

    def _open_usb_camera(self, camera_id):
        """Try multiple backends to open a USB camera."""
        # Try DSHOW first (usually fastest on Windows)
        cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                logger.info("Camera %s: opened with DSHOW", camera_id)
                return cap
            cap.release()
            logger.debug("Camera %s: DSHOW opened but read failed", camera_id)

        # Fall back to MSMF
        cap = cv2.VideoCapture(camera_id, cv2.CAP_MSMF)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                logger.info("Camera %s: opened with MSMF", camera_id)
                return cap
            cap.release()
            logger.debug("Camera %s: MSMF opened but read failed", camera_id)

        # Fall back to default
        cap = cv2.VideoCapture(camera_id)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                logger.info("Camera %s: opened with default backend", camera_id)
                return cap
            cap.release()

        logger.error("Camera %s: no working backend found", camera_id)
        return None

    def _open_network_camera(self, url):
        """Try to open a network camera (MJPEG, RTSP, or any URL OpenCV supports)."""
        # Try default backend first
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                logger.info("Network camera opened: %s", url)
                return cap
            cap.release()
            logger.debug("Network camera %s: opened but read failed (default backend)", url)

        # Try FFMPEG backend as fallback (better RTSP/codec support)
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                logger.info("Network camera opened with FFMPEG backend: %s", url)
                return cap
            cap.release()
            logger.debug("Network camera %s: FFMPEG backend opened but read failed", url)

        logger.error("Network camera %s: could not open", url)
        return None

    def _reconnect_loop(self):
        """Try to reconnect to a network camera with backoff."""
        backoff = 1.0
        attempts = 0
        while self.running:
            attempts += 1
            logger.info("Reconnect attempt #%d to %s (waiting %.0fs)...", attempts, self.camera_id, backoff)
            time.sleep(backoff)
            if not self.running:
                return
            self.cap = self._open_network_camera(self.camera_id)
            if self.cap is not None and self.cap.isOpened():
                logger.info("Reconnected to %s", self.camera_id)
                return
            backoff = min(backoff * 2, 30.0)

    def _apply_transforms(self, frame: np.ndarray) -> np.ndarray:
        """Apply zoom, rotation, and flip transforms."""
        with self._lock:
            zoom = self._zoom
            rotation = self._rotation
            flip_h = self._flip_h
            flip_v = self._flip_v

        # Zoom (center crop)
        if zoom > 1.0:
            h, w = frame.shape[:2]
            crop_w = int(w / zoom)
            crop_h = int(h / zoom)
            x1 = (w - crop_w) // 2
            y1 = (h - crop_h) // 2
            frame = frame[y1:y1 + crop_h, x1:x1 + crop_w]
            frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)

        # Rotation
        if rotation == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif rotation == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif rotation != 0:
            h, w = frame.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, -rotation, 1.0)
            frame = cv2.warpAffine(frame, M, (w, h))

        # Flip
        if flip_h and flip_v:
            frame = cv2.flip(frame, -1)
        elif flip_h:
            frame = cv2.flip(frame, 1)
        elif flip_v:
            frame = cv2.flip(frame, 0)

        return frame

    def stop(self):
        self.running = False
        self.wait(5000)


# ============================================================================
# Person Detector
# ============================================================================

class PersonDetector:
    """Detects people using OpenCV HOG+SVM descriptor.

    Rate-limited to check every ~500ms. Uses hysteresis:
    - 3 consecutive detections to confirm presence (~1.5s)
    - 6 consecutive absences to confirm departure (~3s)
    """

    def __init__(self):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        self._detect_size = (320, 240)
        self._person_present = False
        self._consecutive_present = 0
        self._consecutive_absent = 0
        self._presence_threshold = 3
        self._absence_threshold = 6
        self._last_check_time = 0.0
        self._check_interval = 0.5  # seconds

    @property
    def person_present(self) -> bool:
        return self._person_present

    def check(self, frame: np.ndarray) -> Optional[bool]:
        """Check frame for person presence.

        Returns:
            None if rate-limited (no state change),
            True if person just became present,
            False if person just left,
        """
        now = time.time()
        if now - self._last_check_time < self._check_interval:
            return None
        self._last_check_time = now

        small = cv2.resize(frame, self._detect_size)
        rects, _ = self.hog.detectMultiScale(
            small, winStride=(8, 8), padding=(4, 4), scale=1.05
        )
        detected = len(rects) > 0

        if detected:
            self._consecutive_present += 1
            self._consecutive_absent = 0
        else:
            self._consecutive_absent += 1
            self._consecutive_present = 0

        old_state = self._person_present

        if not self._person_present and self._consecutive_present >= self._presence_threshold:
            self._person_present = True
        elif self._person_present and self._consecutive_absent >= self._absence_threshold:
            self._person_present = False

        if self._person_present != old_state:
            return self._person_present

        return None


# ============================================================================
# Network Camera Scanner
# ============================================================================

def droidcam_url(ip: str) -> str:
    """Build the correct DroidCam MJPEG stream URL for OpenCV."""
    return f"http://{ip}:4747/mjpegfeed"


def test_droidcam_connection(ip: str) -> tuple:
    """Try to connect to DroidCam at the given IP and read a frame.

    Returns (success: bool, message: str, url: str).
    """
    url = droidcam_url(ip)
    success, message = test_network_camera(url)
    return success, message, url


def test_network_camera(url: str) -> tuple:
    """Test if a URL serves video frames OpenCV can read.

    Returns (success: bool, message: str).
    """
    logger.info("Testing network camera at %s", url)
    try:
        # Try default backend
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                return True, f"Connected! Receiving {w}x{h} video"
        else:
            cap.release()

        # Try FFMPEG backend as fallback
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                return True, f"Connected! Receiving {w}x{h} video (FFMPEG)"
            cap.release()
            return False, "Connected but no video frames received"
        else:
            cap.release()

        return False, f"Could not connect to {url}"
    except Exception as e:
        return False, f"Connection error: {e}"


class DroidCamScanner(QThread):
    """Scans local subnet for DroidCam instances (port 4747)."""

    DROIDCAM_PORT = 4747

    scan_progress = pyqtSignal(int, int)  # current, total
    camera_found = pyqtSignal(str, str)  # url, description
    scan_complete = pyqtSignal(list)  # list of (url, description) tuples

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        found = []
        subnet = self._get_local_subnet()
        if not subnet:
            logger.warning("Could not determine local subnet for DroidCam scan")
            self.scan_complete.emit(found)
            return

        total = 254
        for i in range(1, 255):
            if not self._running:
                break
            self.scan_progress.emit(i, total)
            ip = f"{subnet}.{i}"

            if self._check_port(ip, self.DROIDCAM_PORT):
                url = droidcam_url(ip)
                desc = f"DroidCam ({ip})"
                logger.info("Found DroidCam: %s", url)
                found.append((url, desc))
                self.camera_found.emit(url, desc)

        self.scan_complete.emit(found)

    def _get_local_subnet(self) -> Optional[str]:
        """Get local subnet prefix (e.g. '192.168.1')."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            parts = ip.split(".")
            return ".".join(parts[:3])
        except Exception:
            return None

    @staticmethod
    def _check_port(ip: str, port: int, timeout: float = 0.2) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            result = s.connect_ex((ip, port))
            s.close()
            return result == 0
        except Exception:
            return False

    def stop(self):
        self._running = False
        self.wait(3000)
