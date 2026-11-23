@echo off
rem La camera repere la table (4 marqueurs). Lancer regler_table.bat avant. Touche Q pour quitter.
rem Utilise l installation de la tete (tete\installer.bat). Autre webcam : remplacer --camera 1 par --camera 0.
cd /d "%~dp0"
..\tete\.venv\Scripts\python voir_table.py --camera 1 %*
pause
