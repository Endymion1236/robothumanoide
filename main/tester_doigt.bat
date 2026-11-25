@echo off
rem Essai du doigt motorise (servo SCS0009 sur la DEUXIEME carte Waveshare, alimentee en 6 V). FD ferme.
rem Utilise l installation du bras (bras\installer.bat). Pour choisir la carte : tester_doigt.bat --port COM5
cd /d "%~dp0"
..\bras\.venv\Scripts\python tester_doigt.py %*
pause
