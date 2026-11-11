@echo off
rem Reconnaissance d objets (les 80 objets du modele). Touche Q pour quitter.
rem Webcam externe : remplacer --camera 0 par --camera 1 (voir lister_cameras.bat).
cd /d "%~dp0"
.venv\Scripts\python vision.py --camera 0 %*
pause
