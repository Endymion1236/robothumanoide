@echo off
rem Tri avec les reglages de Nicolas : double-clic, rien a taper.
rem Pour changer un reglage : double-clic sur mes_reglages.txt (cree au premier lancement), change le nombre, enregistre.
cd /d "%~dp0"
call trier.bat --reglages %*
