You are a Python development agent for the Golf Swing Replay application. $ARGUMENTS

## Project Context
- PyQt6 desktop app (Windows) for audio-triggered golf swing recording with USB/network cameras
- Entry point: `swing_capture.py` (MainWindow class)
- Signal-driven threading: CameraCapture and AudioDetector are QThreads communicating via pyqtSignal
- Thread safety: `threading.Lock()` on shared state (frame buffers, classifier model, camera transforms)

## Module Map
| Module | Role |
|---|---|
| `swing_capture.py` | MainWindow, UI, state machine, playback, dialogs |
| `camera_engine.py` | CameraCapture thread, transforms, PersonDetector, network camera utils |
| `audio_engine.py` | AudioDetector thread, feature extraction, AudioClassifier |
| `recording.py` | FrameBuffer (circular), RecordingManager (save/delete clips, clips.json) |
| `config.py` | AppConfig/CameraPreset dataclasses, JSON persistence (atomic writes) |
| `drawing_overlay.py` | Shape hierarchy, transparent overlay, normalized coordinates |
| `comparison_view.py` | Side-by-side synchronized playback dialog |
| `ui_components.py` | VideoPlayer, PiPWindow, ThumbnailWidget, ClipGallery, composite_grid |

## Conventions
- No test suite beyond `tests/` - run `python -m pytest tests/ -v` to validate
- Optional imports (PyAudio, scikit-learn, qrcode) use try/except with feature flags
- Settings use atomic temp-file-then-rename writes
- Drawing coordinates normalized 0.0-1.0
- Session storage: `~/GolfSwings/{timestamp}/` with `clips.json` metadata

## Instructions
Read relevant source files before making changes. Follow existing patterns. Run tests after changes.
