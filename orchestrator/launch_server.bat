@echo off
set "FFMPEG_DIR=C:\Users\Antonio Demarchi\AppData\Local\Microsoft\WinGet\Links"
set "PATH=%FFMPEG_DIR%;%PATH%"
cd /d "%~dp0"
python main.py
