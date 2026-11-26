@echo off
rem Regler un bac de tri (position, taille, hauteur du bord). Le bras ne bouge pas.
cd /d "%~dp0"
.venv\Scripts\python -c "import cv2" 2>nul || (echo Installation de la vision, une seule fois... & .venv\Scripts\python -m pip install opencv-python)
.venv\Scripts\python regler_bac.py
pause
