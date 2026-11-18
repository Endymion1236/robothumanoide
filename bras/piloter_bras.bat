@echo off
rem Piloter le bras : epaule 2, coude 1, pince 4. FERMER FD AVANT. Cavaliers de la carte sur B. 12 V et USB branches.
cd /d "%~dp0"
.venv\Scripts\python piloter_bras.py %*
pause
