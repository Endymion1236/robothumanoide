@echo off
rem Fenetre de commande du bras. FERMER FD AVANT. 12 V et USB branches.
cd /d "%~dp0"
.venv\Scripts\python controle_bras.py %*
if errorlevel 1 pause
