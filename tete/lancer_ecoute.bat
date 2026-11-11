@echo off
rem Ecoute le micro et ecrit ce qu on dit. Ctrl + C pour arreter.
rem Autre micro : ajouter --micro N (numero donne par lister_micros.bat).
cd /d "%~dp0"
.venv\Scripts\python ecouter.py %*
pause
