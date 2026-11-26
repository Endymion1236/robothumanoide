@echo off
rem Calin trie les objets de la table : camera + bras. FERMER FD et la fenetre de controle AVANT. 12 V, USB et camera branches.
rem camera\regler_table.bat deja fait. Autre webcam : remplacer --camera 1 par --camera 0.
cd /d "%~dp0"
.venv\Scripts\python -c "import cv2" 2>nul || (echo Installation de la vision, une seule fois... & .venv\Scripts\python -m pip install opencv-python)
.venv\Scripts\python trier.py --camera 1 %*
pause
