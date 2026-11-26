@echo off
rem Calin trie A LA VOIX : "range les ronds dans le bac de gauche et le reste a droite", "stop".
rem Utilise l'installation de la tete (tete\installer.bat deja fait : micro, Whisper, Claude) et la cle Anthropic de la tete.
rem FERMER FD et la fenetre de controle AVANT. 12 V, USB, camera et micro branches. Pour taper au lieu de parler : trier_voix.bat --clavier
cd /d "%~dp0"
if not exist ..\tete\.venv\Scripts\python.exe (echo Il faut d'abord installer la tete : tete\installer.bat & pause & exit /b)
..\tete\.venv\Scripts\python trier.py --camera 1 --voix %*
pause
