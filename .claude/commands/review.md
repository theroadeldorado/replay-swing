Review code changes for bugs, thread safety, resource leaks, and PyQt6 patterns. $ARGUMENTS

## Review Checklist
1. **Thread safety**: Shared state accessed from QThreads must use locks. Signals must be used for cross-thread communication (never direct method calls).
2. **Resource leaks**: cv2.VideoCapture must be released. PyAudio streams must be closed. QTimer must be stopped.
3. **PyQt6 patterns**: No blocking calls on the main thread. Use QTimer or QThread for long operations. Signal/slot connections must match signatures.
4. **Error handling**: External I/O (file, network, camera) must have try/except. Optional imports use feature flags.
5. **Settings safety**: save_settings uses atomic temp-then-rename. Values validated before use.
6. **Memory**: Frame buffers use deque(maxlen=N). Large numpy arrays should be .copy()'d when stored.

## Instructions
If arguments provided, review those specific files. Otherwise, review staged and unstaged git changes (`git diff` and `git diff --cached`). Report issues found with file:line references and severity (critical/warning/info).
