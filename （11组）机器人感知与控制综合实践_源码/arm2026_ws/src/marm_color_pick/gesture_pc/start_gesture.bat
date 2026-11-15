@echo off
setlocal
set "GESTURE_PY=D:\robot_new\.venv-arm2026-gesture\Scripts\python.exe"
if not exist "%GESTURE_PY%" (
  echo Python environment not found. See README.md.
  pause
  exit /b 1
)
"%GESTURE_PY%" "%~dp0app.py"
if errorlevel 1 pause
