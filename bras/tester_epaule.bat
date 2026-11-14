@echo off
rem Essai de l epaule. FERMER FD AVANT. Cavaliers de la carte sur B. 12 V et USB branches.
rem Si l avant-bras est monte : tester_epaule.bat --coude N  (N = numero du servo du coude)
cd /d "%~dp0"
.venv\Scripts\python test_epaule.py %*
pause
