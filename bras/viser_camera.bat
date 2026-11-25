@echo off
rem La camera et le bras dans une seule fenetre : on clique sur un point de la table, le bras y va.
rem FERMER FD et la fenetre de controle AVANT. 12 V, USB et camera branches. camera\regler_table.bat deja fait.
rem Autre webcam : remplacer --camera 1 par --camera 0.
cd /d "%~dp0"
.venv\Scripts\python -c "import cv2" 2>nul || (echo Installation de la vision, une seule fois... & .venv\Scripts\python -m pip install opencv-python)
.venv\Scripts\python viser_camera.py --camera 1 %*
pause
