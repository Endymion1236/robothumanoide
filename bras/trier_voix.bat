@echo off
rem Calin trie A LA VOIX : "range les ronds dans le bac de gauche et le reste a droite", "stop".
rem Utilise l'installation de la tete (tete\installer.bat deja fait : micro, Whisper, Claude) et la cle Anthropic de la tete.
rem FERMER FD et la fenetre de controle AVANT. 12 V, USB, camera et micro branches. Pour taper au lieu de parler : trier_voix.bat --clavier
cd /d "%~dp0"
if not exist ..\tete\.venv\Scripts\python.exe (echo Il faut d'abord installer la tete : tete\installer.bat & pause & exit /b)
rem L'installation de la tete n'a pas toujours ce qu'il faut pour les servos et la camera : on complete, une seule fois.
..\tete\.venv\Scripts\python -c "import serial, cv2" 2>nul || (echo Installation des servos et de la vision dans la tete, une seule fois... & ..\tete\.venv\Scripts\python -m pip install pyserial opencv-python)
..\tete\.venv\Scripts\python trier.py --camera 1 --voix %*
pause
