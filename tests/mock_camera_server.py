"""
MJPEG HTTP server that simulates phone camera feeds (DroidCam, IP Webcam)
for testing without physical devices.

Usage:
    # Single camera on default port 4747
    python tests/mock_camera_server.py

    # Four cameras on consecutive ports with different colors
    python tests/mock_camera_server.py --multi 4

    # Loop a real video file
    python tests/mock_camera_server.py --video path/to/clip.mp4
"""

import argparse
import http.server
import socket
import struct
import threading
import time

import cv2
import numpy as np


# ============================================================================
# Frame Generators
# ============================================================================

class SyntheticFrameGenerator:
    """Generates colored test frames with frame number, timestamp, and grid."""

    def __init__(self, width: int = 640, height: int = 480,
                 color: tuple = (0, 128, 0)):
        self.width = width
        self.height = height
        self.color = color  # BGR
        self.frame_number = 0
        self._start_time = time.monotonic()

    def next_frame(self) -> np.ndarray:
        """Return the next synthetic BGR frame."""
        frame = np.full((self.height, self.width, 3), self.color,
                        dtype=np.uint8)

        # Draw grid pattern
        grid_spacing = 40
        grid_color = tuple(min(c + 60, 255) for c in self.color)
        for x in range(0, self.width, grid_spacing):
            cv2.line(frame, (x, 0), (x, self.height), grid_color, 1)
        for y in range(0, self.height, grid_spacing):
            cv2.line(frame, (0, y), (self.width, y), grid_color, 1)

        # Draw crosshair at center
        cx, cy = self.width // 2, self.height // 2
        cv2.line(frame, (cx - 20, cy), (cx + 20, cy), (255, 255, 255), 1)
        cv2.line(frame, (cx, cy - 20), (cx, cy + 20), (255, 255, 255), 1)

        # Overlay frame number
        elapsed = time.monotonic() - self._start_time
        text_frame = f"Frame: {self.frame_number}"
        text_time = f"Time: {elapsed:.2f}s"
        cv2.putText(frame, text_frame, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, text_time, (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Moving marker so the stream is visually "alive"
        marker_x = int((self.frame_number * 3) % self.width)
        cv2.circle(frame, (marker_x, self.height - 20), 8,
                   (0, 0, 255), -1)

        self.frame_number += 1
        return frame


class VideoFileFrameGenerator:
    """Loops a real video file as the frame source."""

    def __init__(self, video_path: str):
        self.video_path = video_path
        self._cap = cv2.VideoCapture(video_path)
        if not self._cap.isOpened():
            raise FileNotFoundError(
                f"Cannot open video file: {video_path}")

    def next_frame(self) -> np.ndarray:
        """Return the next frame from the video, looping at the end."""
        ret, frame = self._cap.read()
        if not ret:
            # Reached end of file — loop back to the beginning
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._cap.read()
            if not ret:
                raise RuntimeError(
                    f"Cannot read frames from {self.video_path}")
        return frame


# ============================================================================
# MJPEG HTTP Handler
# ============================================================================

class MockCameraHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler that serves an MJPEG stream.

    The ``frame_generator`` and ``fps`` attributes are set on the handler
    class by ``MockCameraServer`` before the server starts accepting
    requests.
    """

    frame_generator = None  # set by MockCameraServer
    fps: int = 30           # set by MockCameraServer

    def do_GET(self):
        if self.path in ("/mjpegfeed", "/video"):
            self._stream_mjpeg()
        else:
            self.send_error(404, "Not Found")

    def _stream_mjpeg(self):
        """Send a continuous multipart MJPEG stream until the client
        disconnects."""
        boundary = "frame"
        self.send_response(200)
        self.send_header("Content-Type",
                         f"multipart/x-mixed-replace; boundary={boundary}")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Pragma", "no-cache")
        self.end_headers()

        interval = 1.0 / self.fps

        try:
            while True:
                frame = self.frame_generator.next_frame()
                _, jpeg = cv2.imencode(".jpg", frame,
                                       [cv2.IMWRITE_JPEG_QUALITY, 80])
                jpeg_bytes = jpeg.tobytes()

                self.wfile.write(f"--{boundary}\r\n".encode())
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(
                    f"Content-Length: {len(jpeg_bytes)}\r\n".encode())
                self.wfile.write(b"\r\n")
                self.wfile.write(jpeg_bytes)
                self.wfile.write(b"\r\n")
                self.wfile.flush()

                time.sleep(interval)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError,
                OSError):
            # Client disconnected — nothing to do
            pass

    # Silence per-request log lines to keep test output clean
    def log_message(self, format, *args):
        pass


# ============================================================================
# Mock Camera Server
# ============================================================================

class MockCameraServer:
    """Threaded HTTP server that streams MJPEG frames.

    Parameters
    ----------
    port : int
        TCP port to listen on (default 4747).
    fps : int
        Target frames per second for the stream.
    generator : SyntheticFrameGenerator | VideoFileFrameGenerator | None
        Frame source.  If *None*, a default ``SyntheticFrameGenerator`` is
        created with a green background.
    """

    def __init__(self, port: int = 4747, fps: int = 30, generator=None):
        self.port = port
        self.fps = fps
        self.generator = generator or SyntheticFrameGenerator()

        # Build a handler subclass with the generator and fps baked in so
        # that every request handler instance can access them.
        handler_class = type(
            "BoundHandler",
            (MockCameraHandler,),
            {
                "frame_generator": self.generator,
                "fps": self.fps,
            },
        )

        self._httpd = http.server.HTTPServer(
            ("0.0.0.0", self.port), handler_class)
        self._httpd.timeout = 0.5
        self._thread = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def url(self) -> str:
        """Base URL of the running server (e.g. ``http://localhost:4747``)."""
        return f"http://localhost:{self.port}"

    def start(self):
        """Start the server in a background daemon thread."""
        self._thread = threading.Thread(
            target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        """Shut down the server and wait for the thread to exit."""
        self._httpd.shutdown()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None


# ============================================================================
# Pytest Fixture
# ============================================================================

def mock_camera_fixture(port: int = 0):
    """Generator-based pytest fixture that yields a running
    ``MockCameraServer`` and tears it down after the test.

    Parameters
    ----------
    port : int
        TCP port. If 0 (default), a random free port is selected
        automatically.

    Yields
    ------
    MockCameraServer
        A started server ready to accept connections.

    Example usage in a conftest or test module::

        import pytest
        from tests.mock_camera_server import mock_camera_fixture

        @pytest.fixture
        def mock_camera():
            yield from mock_camera_fixture()
    """
    if port == 0:
        # Let the OS pick a free port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            port = s.getsockname()[1]

    server = MockCameraServer(port=port)
    server.start()
    try:
        yield server
    finally:
        server.stop()


# ============================================================================
# CLI entry point
# ============================================================================

_MULTI_COLORS = [
    (0, 128, 0),    # green
    (128, 0, 0),    # blue  (BGR)
    (0, 0, 128),    # red   (BGR)
    (0, 200, 200),  # yellow (BGR)
]


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Mock MJPEG camera server for testing")
    parser.add_argument("--port", type=int, default=4747,
                        help="Base TCP port (default: 4747)")
    parser.add_argument("--fps", type=int, default=30,
                        help="Target FPS (default: 30)")
    parser.add_argument("--width", type=int, default=640,
                        help="Frame width (default: 640)")
    parser.add_argument("--height", type=int, default=480,
                        help="Frame height (default: 480)")
    parser.add_argument("--video", type=str, default=None,
                        help="Path to a video file to loop instead of "
                             "synthetic frames")
    parser.add_argument("--multi", type=int, default=None, metavar="N",
                        help="Start N servers on consecutive ports with "
                             "different colors")
    return parser.parse_args()


def main():
    args = _parse_args()
    servers = []

    try:
        if args.multi:
            n = min(args.multi, len(_MULTI_COLORS))
            for i in range(n):
                color = _MULTI_COLORS[i]
                gen = SyntheticFrameGenerator(
                    width=args.width, height=args.height, color=color)
                port = args.port + i
                srv = MockCameraServer(port=port, fps=args.fps,
                                       generator=gen)
                srv.start()
                servers.append(srv)
                print(f"Camera {i + 1}: {srv.url}/mjpegfeed  "
                      f"(color BGR {color})")
        else:
            if args.video:
                gen = VideoFileFrameGenerator(args.video)
            else:
                gen = SyntheticFrameGenerator(
                    width=args.width, height=args.height)
            srv = MockCameraServer(port=args.port, fps=args.fps,
                                   generator=gen)
            srv.start()
            servers.append(srv)
            print(f"Mock camera streaming at {srv.url}/mjpegfeed")
            print(f"  Also available at      {srv.url}/video")

        print("\nPress Ctrl+C to stop.")
        # Block the main thread until interrupted
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        for srv in servers:
            srv.stop()


if __name__ == "__main__":
    main()
