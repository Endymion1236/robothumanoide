@echo off
rem Calin complet : il voit (camera), entend (micro) et repond a voix haute.
rem Dire "au revoir" ou Ctrl + C pour arreter.
rem Options a ajouter apres --camera 0 :
rem   --ia sonnet      IA plus rapide et moins chere (celle de la borne)
rem   --objets objets.txt   detecter sa propre liste d objets
rem   --voix-pc        voix gratuite de Windows    --micro N    autre micro
rem Webcam USB : remplacer --camera 0 par --camera 1.
cd /d "%~dp0"
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set HF_HUB_VERBOSITY=error
set PYTHONWARNINGS=ignore
.venv\Scripts\python robot.py --camera 0 %*
pause
