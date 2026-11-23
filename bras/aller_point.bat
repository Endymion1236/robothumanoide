@echo off
rem Envoyer la pince a un point de la table (v X Y). FERMER FD et la fenetre de controle AVANT. 12 V et USB branches.
cd /d "%~dp0"
.venv\Scripts\python aller_point.py %*
pause
