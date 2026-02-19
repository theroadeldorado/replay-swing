# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
pip install -r requirements.txt
python swing_capture.py
```

PyAudio requires special installation on Windows (`pipwin install pyaudio` or manual wheel). Optional dependencies (PyAudio, scikit-learn, qrcode) degrade gracefully — features are disabled at runtime via `AUDIO_AVAILABLE` / `SKLEARN_AVAILABLE` flags.

There is no test suite, linter configuration, or build system. The app is run directly as a Python script.

## Architecture

This is a PyQt6 desktop application (Windows) for recording golf swings via audio-triggered capture with USB/network cameras. The entry point is `swing_capture.py`.

### Signal-Driven Threading Model

All heavy I/O runs in QThreads that communicate with the main UI thread via PyQt6 signals — never direct callbacks:

- **CameraCapture** (QThread per camera) emits `frame_ready(camera_id, frame, timestamp)`
- **AudioDetector** (QThread) emits `trigger_detected(confidence, features)`
- **MainWindow** connects these signals to update UI, start recording, etc.

Thread safety uses `threading.Lock()` on shared state (frame buffers, audio classifier model, camera transforms).

### Module Responsibilities

| Module | Role |
|---|---|
| `swing_capture.py` | MainWindow — UI, state machine, playback, keyboard shortcuts, all dialogs |
| `camera_engine.py` | CameraCapture thread, per-camera transforms (zoom/rotate/flip), PersonDetector (HOG+SVM), network camera utilities |
| `audio_engine.py` | AudioDetector thread, AudioFeatureExtractor (12 spectral features), AudioClassifier (heuristic + RandomForest learned mode) |
| `recording.py` | FrameBuffer (circular pre-trigger buffer), RecordingManager (save/delete clips, session folders, clips.json metadata) |
| `config.py` | AppConfig and CameraPreset dataclasses, JSON persistence to `~/GolfSwings/settings.json` |
| `drawing_overlay.py` | Shape hierarchy (LineShape, CircleShape), transparent DrawingOverlay widget, normalized 0.0–1.0 coordinates |
| `comparison_view.py` | ComparisonWindow dialog — side-by-side synchronized playback with per-clip frame offset |
| `ui_components.py` | VideoPlayer, PiPWindow, ThumbnailWidget, ClipGallery, LogPanel, `composite_grid()` for multi-camera layout |

### Recording Workflow

Arm → AudioDetector fires trigger → RecordingManager saves pre-buffer (2s) + post-trigger (4s) from all cameras → auto-playback loops → stays armed for next shot. Manual trigger available as fallback.

### Key Design Patterns

- **Circular buffers**: `collections.deque(maxlen=N)` for pre-trigger frames and audio history — constant memory usage.
- **Graceful degradation**: Optional imports wrapped in try/except with feature flags. Always check these flags before touching audio/ML code paths.
- **Normalized coordinates**: Drawing overlay uses 0.0–1.0 relative coords so shapes survive window resizing.
- **Config persistence**: JSON with temp-file-then-rename for atomic writes. Settings auto-saved on changes.
- **Session storage**: `~/GolfSwings/{timestamp}/` folders with `clips.json` metadata, MP4 files, and JPG thumbnails.

### Audio Classifier Dual Mode

The classifier in `audio_engine.py` operates in two modes:
1. **Heuristic** (default): Hand-tuned weights on crest factor, impact ratio (2–6kHz), rise time, spectral centroid. Threshold 0.45.
2. **Learned**: RandomForest trained on 10+ user-labeled samples from `~/GolfSwings/training_data/`. Activates automatically when enough data exists.
