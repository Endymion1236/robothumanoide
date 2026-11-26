@echo off
rem Calin joue au morpion. FERMER FD et la fenetre de controle AVANT. 12 V, USB et camera branches.
rem Avec l'installation de la tete (tete\installer.bat), Calin parle ; sinon il ecrit seulement ses phrases.
rem Niveau : jouer_morpion.bat --niveau facile   (ou normal, imbattable ; touches 1 2 3 pendant le jeu)
cd /d "%~dp0"
if exist ..\tete\.venv\Scripts\python.exe (
  ..\tete\.venv\Scripts\python -c "import serial, cv2" 2>nul || (echo Installation des servos et de la vision dans la tete, une seule fois... & ..\tete\.venv\Scripts\python -m pip install pyserial opencv-python)
  ..\tete\.venv\Scripts\python jouer_morpion.py --camera 1 %*
) else (
  .venv\Scripts\python jouer_morpion.py --camera 1 --muet %*
)
pause
