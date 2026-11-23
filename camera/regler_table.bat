@echo off
rem Enregistre la position des 4 marqueurs (mesures a la regle, en mm).
cd /d "%~dp0"
..\tete\.venv\Scripts\python regler_table.py
pause
