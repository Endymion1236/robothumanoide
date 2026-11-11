@echo off
rem Essai du coude. FERMER FD AVANT. Cavaliers de la carte sur B. 12 V et USB branches.
cd /d "%~dp0"
.venv\Scripts\python test_coude.py %*
pause
