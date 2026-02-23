# ReplaySwing

A free, open-source Windows application for recording and analyzing your golf swings. Features audio-triggered recording with pre-shot buffering, multi-camera synchronization, drawing overlays, swing comparison, and a Picture-in-Picture overlay for use with your simulator.

![ReplaySwing](screenshot.png)

## Features

- **Audio-Triggered Recording** — Detects the sound of club impact and automatically records. Dual-mode classifier: hand-tuned heuristic (default) or RandomForest trained on your environment (auto-activates after 10+ samples).
- **Pre-Trigger Buffer** — A circular frame buffer retroactively captures configurable seconds before impact (default 1 s) so you never miss the backswing.
- **Post-Trigger Recording** — Configurable seconds after trigger (default 2 s) for complete follow-through capture.
- **Multi-Camera Sync** — Record from multiple USB and network cameras simultaneously, triggered by a single audio event. Auto-layout: 1 → full, 2 → side-by-side, 3–4 → 2×2 grid.
- **Phone as Camera** — Use your phone as a wireless camera with DroidCam, IP Webcam, EpocCam, or any MJPEG/RTSP stream. Auto-reconnection with exponential backoff.
- **Picture-in-Picture** — Frameless, always-on-top overlay that floats your swing replay over any simulator. Drag, resize, position saved across sessions.
- **Looping Playback** — Captured clip loops continuously until the next shot. Six speed options (0.25×–2×) and frame-by-frame stepping.
- **Drawing Tools** — Annotate swings with lines and circles. Select/move/rotate/delete shapes. Normalised coordinates survive window resizing. Shapes persist per-session.
- **Swing Comparison** — Side-by-side synchronised playback with per-clip frame offset adjustment (±5 frames) for precise alignment.
- **Session Management** — Shots organised by timestamped session folders with auto-generated thumbnails, metadata, and a visual gallery.
- **Per-Camera Transforms** — Zoom (1–4×), rotation (0–360°), horizontal/vertical flip per camera.
- **Smart Detection** — 12-feature spectral analysis with configurable threshold. Learned classifier auto-trains when enough labeled samples exist.
- **Free & Open Source** — MIT licensed. No subscriptions, no accounts, no data collection.

## Installation

### Prerequisites

- Windows 10 or 11
- Python 3.10 or newer
- USB camera(s) or phone camera app
- Microphone (built-in, USB, or phone mic via DroidCam)

### Setup

1. **Install Python** from [python.org](https://www.python.org/downloads/) if not already installed.

2. **Clone or download** this repository.

3. **Install dependencies**:
   ```cmd
   cd replay-swing/app
   pip install -r requirements.txt
   ```

4. **PyAudio Installation** (for audio triggering):

   PyAudio can be tricky on Windows. Try these methods in order:

   ```cmd
   # Method 1: Direct pip install (may work on some systems)
   pip install pyaudio

   # Method 2: Using pipwin
   pip install pipwin
   pipwin install pyaudio
   ```

   The app works without PyAudio — audio triggering is disabled and you can use manual trigger (`T`) instead.

5. **Run the application**:
   ```cmd
   python swing_capture.py
   ```

## Usage

### Basic Workflow

1. **Launch the app** — it auto-detects your default USB camera.
2. **Select your microphone** from the Audio Device dropdown in Settings.
3. **Arm the system** — click **Arm** or press `A` to start listening for shots.
4. **Take your swing** — the app records automatically and loops playback.
5. **Review** — click any thumbnail in the Gallery, use frame stepping, or open PiP mode.

### Keyboard Shortcuts

Press `?` at any time to show shortcuts in the app.

| Key | Action |
|-----|--------|
| `Space` | Play / Pause playback |
| `←` | Step back one frame |
| `→` | Step forward one frame |
| `A` | Toggle armed (start/stop listening) |
| `T` | Manual trigger (force a recording) |
| `[` | Decrease playback speed |
| `]` | Increase playback speed |
| `P` | Toggle Picture-in-Picture overlay |
| `1` | Select tool (drawing) |
| `2` | Line tool (drawing) |
| `3` | Circle tool (drawing) |
| `Delete` | Delete selected drawing shape |
| `Escape` | Deselect drawing / cancel mode |
| `?` | Show keyboard shortcuts help |

### Camera Setup

**USB cameras** are detected automatically. The app tries DSHOW → MSMF → default backends.

**Phone as camera** — install a streaming app, connect to the same Wi-Fi, and enter the URL in Settings → Add Camera:

| App | Platform | Default URL |
|-----|----------|-------------|
| DroidCam | Android | `http://<ip>:4747/mjpegfeed` |
| IP Webcam | Android | `http://<ip>:8080/video` |
| DroidCam | iOS | `http://<ip>:4747/video` |
| EpocCam / Camo | iOS | Appears as USB camera |

**Per-camera transforms**: Each camera supports zoom (1–4×), rotation (0–360°), and horizontal/vertical flip.

### Audio Trigger

The audio classifier analyses 12 spectral features (crest factor, impact ratio, rise time, spectral centroid, etc.) and scores each sound chunk:

- **Heuristic mode** (default): Hand-tuned rules, threshold configurable via slider (1–100%, default 30%).
- **Learned mode**: RandomForest auto-trains when 10+ labeled samples exist in `~/GolfSwings/training_data/`.

**Tips**: Point the mic toward the hitting area, 3–6 feet away. Increase threshold if you get false triggers; decrease if swings are missed.

### Drawing Tools

| Tool | Key | Description |
|------|-----|-------------|
| Select | `1` | Click to select, drag to move, grab handles to resize/rotate |
| Line | `2` | Draw lines for swing plane, shaft angle analysis |
| Circle | `3` | Mark key positions — club head, ball, joints |

Shapes use normalised coordinates (0.0–1.0) and persist in `settings.json`.

### Swing Comparison

Open from the Gallery (right-click → Compare). Two synchronised video players with independent clip/angle selectors and ±5 frame offset adjustment for precise alignment.

### Picture-in-Picture

Press `P` to open a frameless, always-on-top overlay. Drag to move, resize by edges. Position and size are saved across sessions. Works with any simulator (GSPro, TGC 2019, E6 Connect, Awesome Golf, etc.).

## File Organisation

Sessions are saved to `~/GolfSwings/` with the following structure:

```
GolfSwings/
├── settings.json                   # Configuration
├── training_data/                  # Audio samples for classifier
├── logs/                           # Rotating log files (5 MB × 5)
├── 2026-02-01_14-30-00/            # Session folder (timestamp)
│   ├── shot_0001.mp4               # Primary camera video
│   ├── shot_0001_cam1.mp4          # Secondary camera (if configured)
│   ├── shot_0001.jpg               # Thumbnail
│   ├── shot_0002.mp4
│   ├── shot_0002.jpg
│   └── clips.json                  # Session metadata
└── 2026-02-01_16-45-00/
    └── ...
```

## Troubleshooting

### Camera not detected
- Ensure camera is connected before launching the app.
- Try a different USB port.
- Close other apps using the camera (Zoom, Teams, OBS).
- Click **Refresh Cameras** in Settings.

### Network camera won't connect
- Verify phone and PC are on the same Wi-Fi network.
- Check the IP address and port in the streaming app.
- Try 5 GHz Wi-Fi or a USB tether for reliability.
- The app reconnects automatically with up to 30 s backoff.

### No audio trigger
- Verify microphone is connected and selected in Settings.
- Check the audio level meter — ensure it responds to sound.
- Lower the threshold slider.
- DroidCam also provides a virtual microphone — the app auto-detects it.
- Use Manual Trigger (`T`) as a fallback.

### Too many false triggers
- Increase the threshold slider.
- Move the mic away from speakers, fans, and HVAC vents.
- Collect 10+ labeled samples to enable the learned classifier for better accuracy.

### Choppy video
- Reduce the recording FPS in Settings.
- Ensure adequate lighting for your camera.
- Close resource-heavy applications.

### PyAudio installation fails
- Try `pip install pipwin && pipwin install pyaudio`.
- Ensure you're using 64-bit Python on 64-bit Windows.
- The app works without PyAudio — use manual trigger instead.

### PiP not visible
- Press `P` to toggle. If it's off-screen, delete the `pip_position` entry in `settings.json` and restart.

### Drawings disappeared
- Drawing overlays are saved per-session. Check that the correct session is loaded.

## Settings Reference

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| Pre-trigger seconds | 1.0 | 0.5–30.0 | Video captured before trigger |
| Post-trigger seconds | 2.0 | 0.5–30.0 | Video captured after trigger |
| FPS | 30 | 1–120 | Recording frame rate |
| Audio threshold | 30% | 1–100% | Detection sensitivity |
| Audio sample rate | 44,100 Hz | 8,000–96,000 | Audio sampling frequency |
| PiP size | 480×270 | — | PiP window dimensions |
| PiP position | (100, 100) | — | PiP initial screen position |
| Thumbnail size | 160×90 | — | Gallery thumbnail dimensions |

All settings stored in `~/GolfSwings/settings.json` (atomic writes, auto-saved on change).

## License

MIT License — Feel free to modify and share!

## Contributing

Contributions welcome! Please open an issue or PR for any bugs or feature requests.
