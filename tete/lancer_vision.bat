@echo off
rem Lance la reconnaissance d objets avec la webcam. Touche Q pour quitter.
cd /d "%~dp0"
.venv\Scripts\python vision.py %*
pause
