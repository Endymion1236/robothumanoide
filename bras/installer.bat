@echo off
rem Installe ce qu il faut pour piloter les servos (une seule fois).
cd /d "%~dp0"
py -3 -m venv .venv || python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
echo.
echo Installation terminee.
pause
