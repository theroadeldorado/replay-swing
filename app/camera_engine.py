"""
Camera capture engine with person detection, network camera support,
and per-camera transforms (zoom, rotate, flip).
"""

import logging
import os
import socket
import time
import threading
from typing import Optional, List, Dict, Any

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

# Tell FFMPEG to use TCP for RTSP (more reliable, less packet loss than UDP)
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")

from config import AppConfig, CameraPreset

logger = logging.getLogger(__name__)


# ============================================================================
# Camera Capture Thread
# ============================================================================

class CameraCapture(QThread):
    """Thread for capturing video from a USB or network camera."""

    frame_ready = pyqtSignal(object, np.ndarray, float)  # camera_id (int or str), frame, timestamp
    fps_update = pyqtSignal(object, float)  # camera_id, measured fps
    connection_state = pyqtSignal(object, str)  # camera_id, "connecting"|"connected"|"disconnected"

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
            self.connection_state.emit(self.camera_id, "connecting")
            self.cap = self._open_network_camera(self.camera_id)
        else:
            self.cap = self._open_usb_camera(self.camera_id)

        if self.cap is None or not self.cap.isOpened():
            logger.error("Failed to open camera %s", self.camera_id)
            if is_network:
                self._reconnect_loop()
            return

        if is_network:
            self.connection_state.emit(self.camera_id, "connected")
        logger.info("Camera %s opened successfully", self.camera_id)

        if not is_network:
            # Try to set preferred resolution/fps. If it fails (some MSMF
            # cameras crash on stream reconfiguration), just use the default
            # resolution the camera already opened with.
            try:
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                # Only attempt resolution change if camera supports it
                cur_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                cur_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                if cur_w < 1280 or cur_h < 720:
                    logger.info("Camera %s: native %dx%d, keeping default resolution",
                                self.camera_id, int(cur_w), int(cur_h))
                else:
                    logger.info("Camera %s: native %dx%d", self.camera_id, int(cur_w), int(cur_h))
            except Exception as e:
                logger.debug("Camera %s: failed to set properties: %s", self.camera_id, e)

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

        # FPS tracking
        fps_interval_start = time.time()
        fps_frame_count = 0
        fps_log_interval = 5.0  # log FPS every 5 seconds
        self._current_fps = 0.0

        try:
            while self.running:
                start_time = time.time()

                # read() blocks until a frame arrives (network) or is captured (USB).
                # With CAP_PROP_BUFFERSIZE=1 on network cameras, OpenCV only keeps
                # the latest frame so we always get near-live video.
                ret, frame = self.cap.read()
                timestamp = time.time()

                if ret and frame is not None:
                    consecutive_failures = 0
                    total_frames += 1
                    fps_frame_count += 1
                    frame = self._apply_transforms(frame)
                    self.frame_ready.emit(self.camera_id, frame, timestamp)
                else:
                    consecutive_failures += 1
                    if consecutive_failures == 1:
                        logger.debug("Camera %s: frame read failed (consecutive: %d)", self.camera_id, consecutive_failures)
                    if is_network and consecutive_failures > 30:
                        logger.warning("Camera %s: %d consecutive failures, reconnecting...", self.camera_id, consecutive_failures)
                        self.connection_state.emit(self.camera_id, "disconnected")
                        self.cap.release()
                        self._reconnect_loop()
                        if not self.running:
                            return
                        if self.cap is None or not self.cap.isOpened():
                            logger.error("Camera %s: reconnect failed, exiting thread", self.camera_id)
                            return
                        self.connection_state.emit(self.camera_id, "connected")
                        consecutive_failures = 0
                        total_frames = 0
                        fps_frame_count = 0
                        fps_interval_start = time.time()
                    elif is_network:
                        # Small sleep on failure to avoid tight-looping
                        time.sleep(0.05)

                # FPS calculation and logging
                now = time.time()
                elapsed_since_fps_log = now - fps_interval_start
                if elapsed_since_fps_log >= fps_log_interval:
                    self._current_fps = fps_frame_count / elapsed_since_fps_log
                    logger.info("Camera %s: %.1f FPS (frames: %d)", self.camera_id, self._current_fps, total_frames)
                    self.fps_update.emit(self.camera_id, self._current_fps)
                    fps_frame_count = 0
                    fps_interval_start = now

                # Throttle USB cameras to target FPS; network streams are
                # naturally paced by read() blocking on the next frame
                if not is_network:
                    elapsed = time.time() - start_time
                    sleep_time = frame_interval - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        except Exception as e:
            logger.exception("Camera %s thread crashed: %s", self.camera_id, e)
        finally:
            if self.cap:
                self.cap.release()
            logger.info("Camera %s stopped (%d frames)", self.camera_id, total_frames)

    def _open_usb_camera(self, camera_id):
        """Try multiple backends to open a USB camera."""
        for backend_name, backend in [("DSHOW", cv2.CAP_DSHOW), ("MSMF", cv2.CAP_MSMF), ("default", cv2.CAP_ANY)]:
            cap = cv2.VideoCapture(camera_id, backend)
            ret = False
            try:
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        logger.info("Camera %s: opened with %s", camera_id, backend_name)
                        return cap
                    logger.debug("Camera %s: %s opened but read failed", camera_id, backend_name)
            except Exception as e:
                logger.debug("Camera %s: %s backend exception: %s", camera_id, backend_name, e)
            finally:
                if not ret:
                    cap.release()

        logger.error("Camera %s: no working backend found", camera_id)
        return None

    def _open_network_camera(self, url):
        """Try to open a network camera (MJPEG, RTSP, or any URL OpenCV supports)."""
        for backend_name, backend in [("default", cv2.CAP_ANY), ("FFMPEG", cv2.CAP_FFMPEG)]:
            cap = cv2.VideoCapture(url, backend)
            ret = False
            try:
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    ret, _ = cap.read()
                    if ret:
                        logger.info("Network camera opened (%s backend): %s", backend_name, url)
                        return cap
                    logger.debug("Network camera %s: %s opened but read failed", url, backend_name)
            except Exception as e:
                logger.debug("Network camera %s: %s backend exception: %s", url, backend_name, e)
            finally:
                if not ret:
                    cap.release()

        logger.error("Network camera %s: could not open", url)
        return None

    def _reconnect_loop(self):
        """Try to reconnect to a network camera with backoff."""
        backoff = 1.0
        attempts = 0
        while self.running:
            attempts += 1
            self.connection_state.emit(self.camera_id, "connecting")
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
        if isinstance(self.camera_id, str):
            self.connection_state.emit(self.camera_id, "disconnected")
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

    For DroidCam URLs on port 4747, also tries alternate endpoint paths
    since iOS uses /video while Android uses /mjpegfeed.

    Returns (success: bool, message: str).  On success with an alternate
    URL, the message includes the working URL.
    """
    urls_to_try = [url]

    # DroidCam port 4747: try both /video and /mjpegfeed since iOS and
    # Android serve on different paths
    if ":4747/" in url:
        if url.endswith("/mjpegfeed"):
            urls_to_try.append(url.rsplit("/", 1)[0] + "/video")
        elif url.endswith("/video"):
            urls_to_try.append(url.rsplit("/", 1)[0] + "/mjpegfeed")

    for try_url in urls_to_try:
        logger.info("Testing network camera at %s", try_url)
        try:
            # Try default backend
            cap = cv2.VideoCapture(try_url)
            try:
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        h, w = frame.shape[:2]
                        suffix = f" (via {try_url})" if try_url != url else ""
                        return True, f"Connected! Receiving {w}x{h} video{suffix}"
            finally:
                cap.release()

            # Try FFMPEG backend as fallback
            cap = cv2.VideoCapture(try_url, cv2.CAP_FFMPEG)
            try:
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        h, w = frame.shape[:2]
                        suffix = f" (via {try_url})" if try_url != url else ""
                        return True, f"Connected! Receiving {w}x{h} video (FFMPEG){suffix}"
            finally:
                cap.release()
        except Exception as e:
            logger.debug("Test failed for %s: %s", try_url, e)

    return False, f"Could not connect to {url}"


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
        try:
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
        except Exception as e:
            logger.exception("DroidCam scanner thread crashed: %s", e)

        self.scan_complete.emit(found)

    def _get_local_subnet(self) -> Optional[str]:
        """Get local subnet prefix (e.g. '192.168.1')."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            finally:
                s.close()
            parts = ip.split(".")
            return ".".join(parts[:3])
        except Exception:
            return None

    @staticmethod
    def _check_port(ip: str, port: int, timeout: float = 0.2) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.settimeout(timeout)
                result = s.connect_ex((ip, port))
                return result == 0
            finally:
                s.close()
        except Exception:
            return False

    def stop(self):
        self._running = False
        self.wait(3000)
