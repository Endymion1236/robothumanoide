@echo off
rem Essai de la flexion du poignet (servo n 6). FERMER FD AVANT. Avant-bras pose a plat. 12 V et USB branches.
cd /d "%~dp0"
.venv\Scripts\python test_flexion.py %*
pause
