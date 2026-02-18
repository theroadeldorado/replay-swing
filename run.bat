@echo off
title Golf Swing Capture
echo Starting Golf Swing Capture...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "swing_capture.py" (
    echo ERROR: swing_capture.py not found
    echo Please run this from the golf_swing_capture folder
    pause
    exit /b 1
)

REM Run the application
python swing_capture.py

REM If there was an error, pause so user can see it
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
