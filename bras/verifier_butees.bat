@echo off
rem Verifie les butees de tous les servos, sans rien bouger. FERMER FD AVANT. 12 V et USB branches.
cd /d "%~dp0"
.venv\Scripts\python verifier_butees.py %*
pause
