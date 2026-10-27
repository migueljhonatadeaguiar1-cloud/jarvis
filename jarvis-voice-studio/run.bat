@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
python -m jarvis_voice_studio.app
if errorlevel 1 pause
