@echo off
rem Essai du socle tournant (servo n 1, coude deja au n 3). FERMER FD AVANT. Cavaliers de la carte sur B. 12 V et USB branches.
cd /d "%~dp0"
.venv\Scripts\python test_socle.py %*
pause
