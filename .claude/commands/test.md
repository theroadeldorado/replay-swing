Run the test suite. $ARGUMENTS

If an argument is provided, run tests for that specific module:
- `camera` -> `python -m pytest tests/test_camera_engine.py -v`
- `audio` -> `python -m pytest tests/test_audio_engine.py -v`
- `recording` -> `python -m pytest tests/test_recording.py -v`
- `config` -> `python -m pytest tests/test_config.py -v`
- `drawing` -> `python -m pytest tests/test_drawing_overlay.py -v`
- `comparison` -> `python -m pytest tests/test_comparison_view.py -v`

If no argument or "all", run: `python -m pytest tests/ -v`

Run the appropriate pytest command and report results.
