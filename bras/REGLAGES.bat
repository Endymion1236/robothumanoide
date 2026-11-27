@echo off
rem Ouvre les reglages de la pince et des pions dans le Bloc-notes.
cd /d "%~dp0"
if not exist mes_reglages.bat copy /y reglages_modele.bat mes_reglages.bat >nul
start notepad mes_reglages.bat
