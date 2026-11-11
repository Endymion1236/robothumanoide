@echo off
rem Affiche les numeros des micros.
cd /d "%~dp0"
.venv\Scripts\python ecouter.py --lister
pause
