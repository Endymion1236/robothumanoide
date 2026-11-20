@echo off
rem Essai de la rotation du poignet (servo n 5). FERMER FD AVANT. Bras pose a plat. 12 V et USB branches.
cd /d "%~dp0"
.venv\Scripts\python test_poignet.py %*
pause
