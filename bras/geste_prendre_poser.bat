@echo off
rem Geste prendre et poser (coude n 1 + pince n 4). FERMER FD AVANT. Cavaliers de la carte sur B. 12 V et USB branches.
cd /d "%~dp0"
.venv\Scripts\python geste_prendre_poser.py %*
pause
