@echo off
rem Protocole d essai des articulations. FERMER FD et la fenetre de controle AVANT. 12 V et USB branches.
cd /d "%~dp0"
.venv\Scripts\python protocole_bras.py %*
pause
