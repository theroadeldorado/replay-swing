Start the mock MJPEG camera server for testing. $ARGUMENTS

The mock camera server simulates phone camera feeds without physical devices.

## Usage
Default (single camera on port 4747):
```
python tests/mock_camera_server.py --port 4747 --fps 30
```

Multi-camera (2 cameras on consecutive ports):
```
python tests/mock_camera_server.py --port 4747 --fps 30 --multi 2
```

From a video file:
```
python tests/mock_camera_server.py --video path/to/swing.mp4
```

## Instructions
Start the mock camera server with the arguments provided. If no arguments given, start a single synthetic camera on port 4747. Tell the user the URL(s) to add as network cameras in the app.
