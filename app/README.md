# ⛳ Golf Swing Capture

A polished Windows application for recording and analyzing your golf swings using USB cameras. Features audio-triggered recording with pre-shot buffering, multi-camera synchronization, and a Picture-in-Picture overlay for use with your simulator.

![Golf Swing Capture](screenshot.png)

## Features

- **Audio-Triggered Recording**: Automatically detects the sound of club impact and records your swing
- **Pre-Trigger Buffer**: Captures 2 seconds before the impact sound so you never miss the backswing
- **Post-Trigger Recording**: Records 4 seconds after the trigger for complete follow-through capture
- **Multi-Camera Sync**: Support for multiple synchronized camera angles
- **Picture-in-Picture**: Overlay your swing replay on top of your simulator software
- **Looping Playback**: Current shot loops continuously until the next shot is detected
- **Session Management**: Shots organized by date/session with automatic numbering
- **Thumbnail Gallery**: Visual gallery of all captured swings with easy deletion
- **Adjustable Threshold**: Fine-tune audio sensitivity for your environment

## Installation

### Prerequisites

- Windows 10 or 11
- Python 3.10 or newer
- USB camera(s)
- Microphone (can use camera's built-in mic)

### Setup

1. **Install Python** from [python.org](https://www.python.org/downloads/) if not already installed

2. **Clone or download** this repository

3. **Install dependencies**:
   ```cmd
   cd golf_swing_capture
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
   
   # Method 3: Download wheel manually
   # Go to https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
   # Download the appropriate wheel for your Python version
   # pip install PyAudio‑0.2.13‑cp310‑cp310‑win_amd64.whl
   ```

5. **Run the application**:
   ```cmd
   python swing_capture.py
   ```

## Usage

### Basic Workflow

1. **Launch the app** - It will automatically detect and start your default camera

2. **Configure cameras** (optional) - Click "Configure Cameras" to add additional angles

3. **Adjust threshold** - Use the slider to set audio sensitivity. The audio level meter shows current sound level; set the threshold just above your ambient noise

4. **Arm the system** - Click "🎯 Arm" to start listening for shots

5. **Take your swing** - When the impact sound is detected:
   - Recording automatically captures 2s before + 4s after
   - Shot is saved to your session folder
   - Playback starts automatically
   - System remains armed for the next shot

6. **Review shots** - Click any thumbnail to play that shot

7. **Use PiP mode** - Click "🖼️ PiP" to open a floating window that stays on top of your simulator

### Controls

| Control | Function |
|---------|----------|
| **Arm** | Enable/disable automatic recording |
| **Manual Trigger** | Force a recording without audio trigger |
| **Play/Pause** | Control looping playback |
| **Slider** | Scrub through current shot |
| **PiP** | Toggle Picture-in-Picture overlay |
| **Threshold** | Adjust audio detection sensitivity |
| **Configure Cameras** | Add/remove cameras |
| **Open Folder** | Open session folder in Explorer |
| **New Session** | Start a fresh recording session |

### Tips for Best Results

1. **Camera Placement**:
   - Down-the-line (behind you, facing target)
   - Face-on (perpendicular to target line)
   - Position camera at hand height for best swing plane view

2. **Audio Triggering**:
   - Place microphone close to impact zone
   - Adjust threshold to trigger on ball strike but not club movement
   - If false triggers occur, increase threshold

3. **Lighting**:
   - Ensure consistent, bright lighting
   - Avoid backlighting (windows behind you)
   - High frame rate cameras work best with good lighting

4. **Multiple Cameras**:
   - Use identical cameras when possible for consistent frame rates
   - Primary camera should be your preferred analysis angle
   - All cameras record simultaneously and sync to the same audio trigger

## File Organization

Sessions are saved to `~/GolfSwings/` with the following structure:

```
GolfSwings/
├── 2026-02-01_14-30-00/          # Session folder (date_time)
│   ├── shot_0001.mp4             # Primary camera video
│   ├── shot_0001_cam1.mp4        # Secondary camera (if configured)
│   ├── shot_0001.jpg             # Thumbnail
│   ├── shot_0002.mp4
│   ├── shot_0002.jpg
│   └── clips.json                # Session metadata
└── 2026-02-01_16-45-00/
    └── ...
```

## Troubleshooting

### Camera not detected
- Ensure camera is connected before launching the app
- Try a different USB port
- Check if other apps are using the camera

### No audio trigger
- Verify microphone is connected and working
- Check Windows sound settings to ensure correct input device
- Lower the threshold slider
- Use Manual Trigger as a fallback

### Choppy video
- Reduce camera resolution in camera settings
- Ensure adequate lighting
- Close other applications using system resources

### PyAudio installation fails
- Try the wheel file method described above
- Ensure you're using 64-bit Python on 64-bit Windows
- Check that Visual C++ Redistributable is installed

## Phase 2 Roadmap (Coming Soon)

- 📱 **Phone as Camera**: Use your smartphone as a wireless camera via WiFi
- 🎨 **Swing Comparison**: Side-by-side comparison with previous swings or pro swings
- 📊 **Basic Analysis**: Swing tempo, position markers
- ☁️ **Cloud Backup**: Optional sync to cloud storage

## License

MIT License - Feel free to modify and share!

## Contributing

Contributions welcome! Please open an issue or PR for any bugs or feature requests.
