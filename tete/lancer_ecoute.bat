@echo off
rem Ecoute le micro et ecrit ce qu on dit. Ctrl + C pour arreter.
rem Autre micro : ajouter --micro N (numero donne par lister_micros.bat).
cd /d "%~dp0"
rem Masque des avertissements sans gravite du telechargement du modele.
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set HF_HUB_VERBOSITY=error
set PYTHONWARNINGS=ignore
.venv\Scripts\python ecouter.py %*
pause
