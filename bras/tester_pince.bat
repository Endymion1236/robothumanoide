@echo off
rem Essai de la pince (servo n 4). FERMER FD AVANT. Cavaliers de la carte sur B. 12 V et USB branches.
cd /d "%~dp0"
.venv\Scripts\python test_pince.py %*
pause
