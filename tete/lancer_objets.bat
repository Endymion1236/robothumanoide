@echo off
rem Cherche les objets de la liste objets.txt (modifiable avec le Bloc-notes). Touche Q pour quitter.
rem Webcam externe : remplacer --camera 0 par --camera 1 (voir lister_cameras.bat).
cd /d "%~dp0"
.venv\Scripts\python vision.py --camera 0 --objets objets.txt %*
pause
