@echo off
rem Affiche les numeros des webcams branchees.
cd /d "%~dp0"
.venv\Scripts\python vision.py --lister
pause
