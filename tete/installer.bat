@echo off
rem Installe ce qu il faut pour la tete du robot (une seule fois, environ 10 minutes).
cd /d "%~dp0"
py -3 -m venv .venv || python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
echo.
echo Installation terminee. Lancer maintenant lancer_vision.bat
pause
