@echo off
rem Etalonner la largeur lue par la pince avec le gros rond (40 mm) et le petit rond (28 mm). Le bras ne bouge pas.
cd /d "%~dp0"
.venv\Scripts\python etalonner_largeur.py
pause
