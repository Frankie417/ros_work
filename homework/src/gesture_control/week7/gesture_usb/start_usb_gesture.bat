@echo off
setlocal
cd /d "%~dp0"
if exist "..\..\..\..\.venv-gesture\Scripts\python.exe" (
  "..\..\..\..\.venv-gesture\Scripts\python.exe" app_usb.py
) else (
  py -3.11 app_usb.py
)
if errorlevel 1 pause
