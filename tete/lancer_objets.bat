@echo off
rem Cherche les objets de la liste objets.txt (modifiable avec le Bloc-notes). Touche Q pour quitter.
rem Webcam du portable : remplacer --camera 1 par --camera 0 (voir lister_cameras.bat).
cd /d "%~dp0"
.venv\Scripts\python vision.py --camera 1 --objets objets.txt %*
pause
