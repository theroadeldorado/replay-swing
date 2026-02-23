export interface DocSection {
  id: string;
  title: string;
  iconName: string;
  content: string;
}

export const docSections: DocSection[] = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    iconName: 'Rocket',
    content: `
      <h3>Prerequisites</h3>
      <ul>
        <li><strong>Windows 10 or 11</strong> (macOS &amp; Linux coming soon)</li>
        <li>A USB webcam <em>or</em> a phone running a camera app (DroidCam, IP Webcam, EpocCam)</li>
        <li>A microphone (built-in laptop mic, USB mic, or phone mic via DroidCam)</li>
      </ul>

      <h3>Installation</h3>
      <ol>
        <li>Download the latest <code>.exe</code> installer from the <a href="#download">Download section</a> or the <a href="https://github.com/theroadeldorado/golf-cam-replay/releases/latest" target="_blank" rel="noopener noreferrer">GitHub Releases</a> page.</li>
        <li>Run the installer &mdash; no admin privileges required.</li>
        <li>Launch <strong>Golf Cam Replay</strong> from the Start Menu or desktop shortcut.</li>
      </ol>

      <h3>First Launch</h3>
      <ol>
        <li>The app auto-detects your first USB camera. If no camera is found, connect one and click <strong>Refresh Cameras</strong> in Settings.</li>
        <li>Select your microphone from the <strong>Audio Device</strong> dropdown in Settings.</li>
        <li>Click <strong>Arm</strong> (or press <kbd>A</kbd>) to begin listening for club impact.</li>
        <li>Take a swing &mdash; the app records automatically and starts looping playback.</li>
      </ol>
      <p>Recordings are saved to <code>~/GolfSwings/</code> organized by session timestamp.</p>
    `,
  },
  {
    id: 'camera-setup',
    title: 'Camera Setup',
    iconName: 'Camera',
    content: `
      <h3>USB Cameras</h3>
      <p>Plug in any USB webcam and the app detects it automatically. Golf Cam Replay tries multiple capture backends (DSHOW &rarr; MSMF &rarr; default) so most cameras work out of the box.</p>
      <p>For best results, use a camera that supports <strong>720p or higher</strong> at 30 fps.</p>

      <h3>Multi-Camera Recording</h3>
      <p>Add cameras in the <strong>Settings</strong> tab. When armed, all cameras record simultaneously from a single audio trigger. Each camera saves a separate file:</p>
      <ul>
        <li>Primary: <code>shot_0001.mp4</code></li>
        <li>Secondary: <code>shot_0001_cam1.mp4</code></li>
      </ul>
      <p>The live view auto-layouts cameras: 1 &rarr; full, 2 &rarr; side-by-side, 3&ndash;4 &rarr; 2&times;2 grid.</p>

      <h3>Per-Camera Transforms</h3>
      <p>Each camera supports individual transforms applied in real time:</p>
      <table>
        <thead><tr><th>Transform</th><th>Range</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td>Zoom</td><td>1.0&ndash;4.0&times;</td><td>Center crop with scaling</td></tr>
          <tr><td>Rotation</td><td>0&deg;&ndash;360&deg;</td><td>Rotate by 90&deg; steps or arbitrary angle</td></tr>
          <tr><td>Flip Horizontal</td><td>On / Off</td><td>Mirror image left-right</td></tr>
          <tr><td>Flip Vertical</td><td>On / Off</td><td>Mirror image top-bottom</td></tr>
        </tbody>
      </table>
    `,
  },
  {
    id: 'phone-as-camera',
    title: 'Phone as Camera',
    iconName: 'Smartphone',
    content: `
      <p>Turn any phone into a wireless camera using a free streaming app. No extra hardware needed.</p>

      <h3>Supported Apps</h3>
      <table>
        <thead><tr><th>App</th><th>Platform</th><th>Port</th><th>URL Format</th></tr></thead>
        <tbody>
          <tr><td><strong>DroidCam</strong></td><td>Android</td><td>4747</td><td><code>http://&lt;ip&gt;:4747/mjpegfeed</code></td></tr>
          <tr><td><strong>IP Webcam</strong></td><td>Android</td><td>8080</td><td><code>http://&lt;ip&gt;:8080/video</code></td></tr>
          <tr><td><strong>DroidCam</strong></td><td>iOS</td><td>4747</td><td><code>http://&lt;ip&gt;:4747/video</code></td></tr>
          <tr><td><strong>EpocCam / Camo</strong></td><td>iOS</td><td>&mdash;</td><td>Appears as USB camera</td></tr>
          <tr><td><strong>Custom URL</strong></td><td>Any</td><td>&mdash;</td><td>Any MJPEG or RTSP stream</td></tr>
        </tbody>
      </table>

      <h3>Setup Steps</h3>
      <ol>
        <li>Install the camera app on your phone and the desktop companion (if required).</li>
        <li>Connect your phone and PC to the <strong>same Wi-Fi network</strong>.</li>
        <li>Start streaming on the phone &mdash; note the IP address shown.</li>
        <li>In Golf Cam Replay, go to <strong>Settings &rarr; Add Camera</strong> and enter the URL.</li>
      </ol>

      <h3>Tips</h3>
      <ul>
        <li><strong>DroidCam also provides a virtual microphone</strong> &mdash; useful if your PC doesn&rsquo;t have a mic. The app auto-detects it and labels it "(phone mic)".</li>
        <li>For the most reliable connection, use <strong>5 GHz Wi-Fi</strong> or a USB tether.</li>
        <li>The app auto-reconnects if the stream drops, with exponential backoff up to 30 seconds.</li>
      </ul>
    `,
  },
  {
    id: 'audio-trigger',
    title: 'Audio Trigger',
    iconName: 'AudioLines',
    content: `
      <p>Golf Cam Replay listens for the distinctive sound of club impact and triggers recording automatically. Two detection modes are available.</p>

      <h3>Heuristic Classifier (Default)</h3>
      <p>Hand-tuned rules analyse 12 spectral features of each audio chunk, scoring for characteristics typical of a golf impact:</p>
      <ul>
        <li><strong>Crest factor</strong> &mdash; high peak-to-RMS ratio (sharp transient)</li>
        <li><strong>Impact ratio</strong> &mdash; concentration of energy in the 2&ndash;6 kHz band</li>
        <li><strong>Rise time</strong> &mdash; fast onset (&lt; 30 samples for strongest signal)</li>
        <li><strong>Zero-crossing rate</strong> &mdash; 0.05&ndash;0.35 range typical of impacts</li>
        <li><strong>Spectral centroid</strong> &mdash; 1.5&ndash;5 kHz sweet spot</li>
      </ul>
      <p>A low-frequency penalty suppresses false triggers from footsteps or speech.</p>

      <h3>Learned Classifier</h3>
      <p>Once you&rsquo;ve collected <strong>10+ labeled samples</strong>, the app automatically switches to a RandomForest model trained on your specific environment. This improves accuracy for your room, club type, and mat combination.</p>
      <p>To train: use the <strong>Mark Not Shot</strong> button to label false positives, and take real swings to accumulate positive samples. The classifier retrains automatically when enough data is available.</p>

      <h3>Threshold Tuning</h3>
      <p>The <strong>sensitivity slider</strong> (1&ndash;100%) controls how confident the classifier must be before triggering. Lower values trigger more easily (more false positives); higher values are more selective.</p>
      <ul>
        <li>Default: <strong>30%</strong></li>
        <li>If you get too many false triggers, increase the threshold.</li>
        <li>If real swings are missed, decrease the threshold or check mic placement.</li>
      </ul>

      <h3>Microphone Tips</h3>
      <ul>
        <li>Point the mic toward the hitting area, 3&ndash;6 feet away.</li>
        <li>Avoid placing the mic near speakers or HVAC vents.</li>
        <li>A phone mic via DroidCam works well &mdash; place the phone near the tee.</li>
      </ul>
    `,
  },
  {
    id: 'recording',
    title: 'Recording',
    iconName: 'Circle',
    content: `
      <h3>Arm &amp; Disarm</h3>
      <p>Press <kbd>A</kbd> or click the <strong>Arm</strong> button to start listening for triggers. While armed, the status bar shows a pulsing red indicator and "Listening for impact&hellip;"</p>

      <h3>Manual Trigger</h3>
      <p>Press <kbd>T</kbd> to force a recording at any time, even when armed. Useful for testing or capturing without audio (e.g., putting).</p>

      <h3>Pre-Buffer &amp; Post-Trigger Timing</h3>
      <p>The app maintains a <strong>circular frame buffer</strong> so it can retroactively capture video from <em>before</em> you swung:</p>
      <table>
        <thead><tr><th>Setting</th><th>Default</th><th>Range</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td>Pre-trigger</td><td>1.0 s</td><td>0.5&ndash;30 s</td><td>Seconds of video kept before the trigger</td></tr>
          <tr><td>Post-trigger</td><td>2.0 s</td><td>0.5&ndash;30 s</td><td>Seconds of video captured after the trigger</td></tr>
          <tr><td>FPS</td><td>30</td><td>1&ndash;120</td><td>Recording frame rate</td></tr>
        </tbody>
      </table>
      <p><strong>Example:</strong> With defaults, each clip is (1 + 2) &times; 30 = 90 frames &asymp; 3 seconds.</p>

      <h3>What Happens on Trigger</h3>
      <ol>
        <li>Audio or manual trigger fires.</li>
        <li>The pre-buffer (last 1 s of frames) is frozen.</li>
        <li>Post-trigger frames are appended for 2 s.</li>
        <li>The clip is saved as <code>shot_NNNN.mp4</code> with a thumbnail.</li>
        <li>Playback starts looping automatically.</li>
        <li>The system stays armed for the next shot.</li>
      </ol>
    `,
  },
  {
    id: 'playback',
    title: 'Playback',
    iconName: 'Play',
    content: `
      <h3>Looping Replay</h3>
      <p>After each shot, the captured clip <strong>loops continuously</strong> until the next trigger or until you manually pause. This lets you study your swing on repeat without touching any controls.</p>

      <h3>Speed Control</h3>
      <p>Use the speed selector or keyboard shortcuts to change playback speed:</p>
      <table>
        <thead><tr><th>Speed</th><th>Shortcut</th><th>Use Case</th></tr></thead>
        <tbody>
          <tr><td>0.25&times;</td><td><kbd>[</kbd> to decrease</td><td>Ultra slow-mo for fine detail</td></tr>
          <tr><td>0.5&times;</td><td></td><td>Slow motion</td></tr>
          <tr><td>0.75&times;</td><td></td><td>Slightly slowed</td></tr>
          <tr><td>1.0&times;</td><td></td><td>Real-time</td></tr>
          <tr><td>1.5&times;</td><td></td><td>Quick review</td></tr>
          <tr><td>2.0&times;</td><td><kbd>]</kbd> to increase</td><td>Fast scan</td></tr>
        </tbody>
      </table>

      <h3>Frame Stepping</h3>
      <p>Pause playback (press <kbd>Space</kbd>), then use <kbd>&larr;</kbd> and <kbd>&rarr;</kbd> to move one frame at a time. This is ideal for analysing exact positions at key moments &mdash; address, top of backswing, impact, and follow-through.</p>

      <h3>Multi-Camera View</h3>
      <p>When recording with 2+ cameras, toggle between single-camera and grid view. An angle bar lets you switch between camera perspectives (e.g., "Down-the-Line" vs "Face-On").</p>
    `,
  },
  {
    id: 'pip',
    title: 'Picture-in-Picture',
    iconName: 'PictureInPicture2',
    content: `
      <h3>Overview</h3>
      <p>The PiP window is a frameless, always-on-top overlay that floats your swing replay over any application &mdash; your simulator software, launch monitor, or any full-screen app. No alt-tabbing needed.</p>

      <h3>Opening PiP</h3>
      <p>Press <kbd>P</kbd> or click the <strong>PiP</strong> button. The overlay appears at its last saved position (default: top-left corner, 480&times;270 px).</p>

      <h3>Controls</h3>
      <table>
        <thead><tr><th>Action</th><th>How</th></tr></thead>
        <tbody>
          <tr><td>Move</td><td>Drag anywhere on the window</td></tr>
          <tr><td>Resize</td><td>Drag the window edges or corners</td></tr>
          <tr><td>Close</td><td>Click the <strong>&times;</strong> button or press <kbd>P</kbd> again</td></tr>
        </tbody>
      </table>

      <h3>Behaviour</h3>
      <ul>
        <li>Plays the same clip as the main window, at the same speed.</li>
        <li>Loops automatically alongside the main player.</li>
        <li>Position and size are saved to settings and restored on next launch.</li>
        <li>Works with any simulator: GSPro, TGC 2019, E6 Connect, Awesome Golf, etc.</li>
      </ul>
    `,
  },
  {
    id: 'drawing-tools',
    title: 'Drawing Tools',
    iconName: 'PenTool',
    content: `
      <h3>Available Tools</h3>
      <table>
        <thead><tr><th>Tool</th><th>Shortcut</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td>Select</td><td><kbd>1</kbd></td><td>Click to select shapes, drag to move, grab handles to resize or rotate</td></tr>
          <tr><td>Line</td><td><kbd>2</kbd></td><td>Draw lines for swing plane, shaft angle, or alignment analysis</td></tr>
          <tr><td>Circle</td><td><kbd>3</kbd></td><td>Mark key positions &mdash; club head, ball, joints</td></tr>
        </tbody>
      </table>

      <h3>Drawing</h3>
      <ol>
        <li>Select a tool (Line or Circle) from the Drawing tab or press <kbd>2</kbd>/<kbd>3</kbd>.</li>
        <li>Click and drag on the video frame to create the shape.</li>
        <li>Use the colour picker to change the shape colour.</li>
        <li>Shapes are drawn using <strong>normalised coordinates</strong> (0.0&ndash;1.0), so they scale correctly when the window resizes.</li>
      </ol>

      <h3>Editing Shapes</h3>
      <ul>
        <li>Switch to the <strong>Select</strong> tool (<kbd>1</kbd>) to interact with existing shapes.</li>
        <li><strong>Move:</strong> Click and drag a shape.</li>
        <li><strong>Resize:</strong> Drag the endpoint handles (lines) or the radius handle (circles).</li>
        <li><strong>Rotate lines:</strong> Drag the yellow rotation handle perpendicular to the line.</li>
        <li><strong>Delete:</strong> Select a shape, then press <kbd>Delete</kbd>.</li>
        <li><strong>Deselect:</strong> Press <kbd>Escape</kbd> to clear the selection.</li>
      </ul>

      <h3>Persistence</h3>
      <p>All drawing overlays are saved per-session in <code>settings.json</code> and restored when you reopen the app.</p>
    `,
  },
  {
    id: 'swing-comparison',
    title: 'Swing Comparison',
    iconName: 'Columns2',
    content: `
      <h3>Overview</h3>
      <p>Compare two swings side-by-side with synchronised playback. This is invaluable for tracking improvement over time or comparing different clubs and techniques.</p>

      <h3>Opening the Comparison View</h3>
      <p>Right-click a clip thumbnail in the Gallery and choose <strong>Compare</strong>, or use the comparison button in the main window. A new dialog opens with two video players.</p>

      <h3>Controls</h3>
      <table>
        <thead><tr><th>Control</th><th>Function</th></tr></thead>
        <tbody>
          <tr><td>Left / Right clip selectors</td><td>Choose which clips to compare</td></tr>
          <tr><td>Angle selectors</td><td>Pick camera angle per side (primary, secondary, etc.)</td></tr>
          <tr><td>Play / Pause</td><td>Synchronised playback of both clips</td></tr>
          <tr><td>Playback slider</td><td>Scrub both clips together</td></tr>
          <tr><td>Speed selector</td><td>Adjust playback speed for both clips</td></tr>
        </tbody>
      </table>

      <h3>Frame Offset</h3>
      <p>Swings rarely start at exactly the same moment. Use the <strong>&minus;5 / +5</strong> frame offset buttons on each side to fine-tune alignment &mdash; for example, sync both clips to the moment of impact.</p>
      <p>The current offset is displayed as "Offset: X frames" for each clip.</p>
    `,
  },
  {
    id: 'session-management',
    title: 'Session Management',
    iconName: 'FolderOpen',
    content: `
      <h3>Session Folders</h3>
      <p>Each session is stored in a timestamped folder under <code>~/GolfSwings/</code>:</p>
      <pre><code>GolfSwings/
├── 2026-02-01_14-30-00/
│   ├── shot_0001.mp4
│   ├── shot_0001_cam1.mp4
│   ├── shot_0001.jpg          (thumbnail)
│   ├── shot_0002.mp4
│   ├── shot_0002.jpg
│   └── clips.json             (metadata)
└── 2026-02-01_16-45-00/
    └── ...</code></pre>
      <p>A new session folder is created automatically when the app launches. Click <strong>New Session</strong> to start a fresh folder mid-session.</p>

      <h3>Clip Gallery</h3>
      <p>The <strong>Gallery</strong> tab shows thumbnail previews of every clip in the current session. Click a thumbnail to load the clip for playback.</p>

      <h3>Managing Clips</h3>
      <table>
        <thead><tr><th>Action</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td>Delete</td><td>Remove the clip and all associated files (with confirmation dialog)</td></tr>
          <tr><td>Mark Not Shot</td><td>Deletes the video but keeps the audio sample for classifier training</td></tr>
          <tr><td>Open Folder</td><td>Opens the session directory in Windows Explorer</td></tr>
        </tbody>
      </table>

      <h3>Thumbnails</h3>
      <p>Thumbnails are auto-generated from approximately one-third through each clip, giving a representative frame of the swing. They are saved as <code>shot_NNNN.jpg</code> alongside the video.</p>
    `,
  },
  {
    id: 'keyboard-shortcuts',
    title: 'Keyboard Shortcuts',
    iconName: 'Keyboard',
    content: `
      <p>Press <kbd>?</kbd> at any time to show the shortcuts help dialog within the app.</p>
      <table>
        <thead><tr><th>Key</th><th>Action</th></tr></thead>
        <tbody>
          <tr><td><kbd>Space</kbd></td><td>Play / Pause playback</td></tr>
          <tr><td><kbd>&larr;</kbd></td><td>Step back one frame</td></tr>
          <tr><td><kbd>&rarr;</kbd></td><td>Step forward one frame</td></tr>
          <tr><td><kbd>A</kbd></td><td>Toggle armed (start/stop listening for triggers)</td></tr>
          <tr><td><kbd>T</kbd></td><td>Manual trigger (force a recording)</td></tr>
          <tr><td><kbd>[</kbd></td><td>Decrease playback speed</td></tr>
          <tr><td><kbd>]</kbd></td><td>Increase playback speed</td></tr>
          <tr><td><kbd>P</kbd></td><td>Toggle Picture-in-Picture overlay</td></tr>
          <tr><td><kbd>1</kbd></td><td>Select tool (drawing)</td></tr>
          <tr><td><kbd>2</kbd></td><td>Line tool (drawing)</td></tr>
          <tr><td><kbd>3</kbd></td><td>Circle tool (drawing)</td></tr>
          <tr><td><kbd>Delete</kbd></td><td>Delete selected drawing shape</td></tr>
          <tr><td><kbd>Escape</kbd></td><td>Deselect drawing / cancel mode</td></tr>
          <tr><td><kbd>?</kbd></td><td>Show keyboard shortcuts help</td></tr>
        </tbody>
      </table>
    `,
  },
  {
    id: 'settings',
    title: 'Settings',
    iconName: 'Settings',
    content: `
      <h3>Configuration File</h3>
      <p>All settings are stored in <code>~/GolfSwings/settings.json</code> and auto-saved whenever you change a setting. The file is written atomically (temp file then rename) to prevent corruption.</p>

      <h3>Recording Settings</h3>
      <table>
        <thead><tr><th>Option</th><th>Default</th><th>Range</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td>Pre-trigger seconds</td><td>1.0</td><td>0.5&ndash;30.0</td><td>How far back in time to capture</td></tr>
          <tr><td>Post-trigger seconds</td><td>2.0</td><td>0.5&ndash;30.0</td><td>How long to keep recording after trigger</td></tr>
          <tr><td>FPS</td><td>30</td><td>1&ndash;120</td><td>Recording frame rate</td></tr>
        </tbody>
      </table>

      <h3>Audio Settings</h3>
      <table>
        <thead><tr><th>Option</th><th>Default</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td>Audio device</td><td>System default</td><td>Microphone input to use for trigger detection</td></tr>
          <tr><td>Threshold</td><td>30%</td><td>Detection sensitivity (1&ndash;100%)</td></tr>
          <tr><td>Sample rate</td><td>44,100 Hz</td><td>Audio sampling frequency</td></tr>
          <tr><td>Chunk size</td><td>1,024</td><td>Audio buffer size</td></tr>
        </tbody>
      </table>

      <h3>Display Settings</h3>
      <table>
        <thead><tr><th>Option</th><th>Default</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td>PiP size</td><td>480 &times; 270</td><td>Picture-in-Picture window dimensions</td></tr>
          <tr><td>PiP position</td><td>(100, 100)</td><td>PiP initial screen position</td></tr>
          <tr><td>Thumbnail size</td><td>160 &times; 90</td><td>Gallery thumbnail dimensions</td></tr>
          <tr><td>Window geometry</td><td>Auto</td><td>Main window position/size (auto-saved on exit)</td></tr>
        </tbody>
      </table>

      <h3>File Locations</h3>
      <table>
        <thead><tr><th>Path</th><th>Contents</th></tr></thead>
        <tbody>
          <tr><td><code>~/GolfSwings/settings.json</code></td><td>All configuration</td></tr>
          <tr><td><code>~/GolfSwings/&lt;timestamp&gt;/</code></td><td>Session recordings</td></tr>
          <tr><td><code>~/GolfSwings/training_data/</code></td><td>Audio samples for classifier</td></tr>
          <tr><td><code>~/GolfSwings/logs/</code></td><td>Rotating log files (5 MB &times; 5 backups)</td></tr>
        </tbody>
      </table>
    `,
  },
  {
    id: 'troubleshooting',
    title: 'Troubleshooting',
    iconName: 'LifeBuoy',
    content: `
      <h3>Camera Issues</h3>
      <table>
        <thead><tr><th>Problem</th><th>Solution</th></tr></thead>
        <tbody>
          <tr><td>No camera detected</td><td>Check USB connection, then click <strong>Refresh Cameras</strong> in Settings. Try a different USB port.</td></tr>
          <tr><td>Black/frozen feed</td><td>Close other apps using the camera (Zoom, Teams, OBS). Restart the app.</td></tr>
          <tr><td>Low frame rate</td><td>Lower the resolution in your camera&rsquo;s software, or reduce the FPS setting in Golf Cam Replay.</td></tr>
          <tr><td>Network camera won&rsquo;t connect</td><td>Verify phone and PC are on the same Wi-Fi. Check the IP and port. Ensure the streaming app is running.</td></tr>
          <tr><td>Network camera keeps dropping</td><td>Switch to 5 GHz Wi-Fi or use a USB tether. The app reconnects automatically with up to 30 s backoff.</td></tr>
        </tbody>
      </table>

      <h3>Audio Issues</h3>
      <table>
        <thead><tr><th>Problem</th><th>Solution</th></tr></thead>
        <tbody>
          <tr><td>No audio device listed</td><td>Connect a microphone and click <strong>Refresh Devices</strong>. For DroidCam, make sure the desktop client is installed.</td></tr>
          <tr><td>Too many false triggers</td><td>Increase the threshold slider. Move the mic away from speakers and fans.</td></tr>
          <tr><td>Swings aren&rsquo;t detected</td><td>Decrease the threshold. Move the mic closer to the hitting area. Try pointing it at the mat.</td></tr>
          <tr><td>PyAudio not installed</td><td>Audio triggering requires PyAudio. If running from source, install it with: <code>pip install pyaudio</code>. On Windows you may need: <code>pip install pipwin &amp;&amp; pipwin install pyaudio</code>. The app still works without it &mdash; use manual trigger (<kbd>T</kbd>) instead.</td></tr>
        </tbody>
      </table>

      <h3>Video &amp; Playback Issues</h3>
      <table>
        <thead><tr><th>Problem</th><th>Solution</th></tr></thead>
        <tbody>
          <tr><td>Choppy playback</td><td>Reduce the playback speed or lower the recording FPS. Close resource-heavy apps.</td></tr>
          <tr><td>Clip too short / too long</td><td>Adjust the pre-trigger and post-trigger times in Settings.</td></tr>
          <tr><td>PiP not visible</td><td>Press <kbd>P</kbd> to toggle PiP. If it&rsquo;s off-screen, delete the <code>pip_position</code> entry in <code>settings.json</code> and restart.</td></tr>
          <tr><td>Drawings disappeared</td><td>Drawing overlays are saved per-session. Check that the correct session is loaded.</td></tr>
        </tbody>
      </table>

      <h3>General</h3>
      <ul>
        <li><strong>Check the logs</strong> &mdash; the Log tab shows real-time messages. Log files are saved in <code>~/GolfSwings/logs/</code>.</li>
        <li><strong>Reset settings</strong> &mdash; delete <code>~/GolfSwings/settings.json</code> to restore all defaults.</li>
        <li><strong>Report a bug</strong> &mdash; use the <a href="#bug-report">bug report form</a> or open an issue on <a href="https://github.com/theroadeldorado/golf-cam-replay/issues" target="_blank" rel="noopener noreferrer">GitHub</a>.</li>
      </ul>
    `,
  },
];
