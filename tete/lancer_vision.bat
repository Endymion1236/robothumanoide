@echo off
rem Reconnaissance d objets (les 80 objets du modele). Touche Q pour quitter.
rem Webcam du portable : remplacer --camera 1 par --camera 0 (voir lister_cameras.bat).
cd /d "%~dp0"
.venv\Scripts\python vision.py --camera 1 %*
pause
