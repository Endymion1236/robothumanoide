@echo off
rem Conversation avec Calin : parler au micro, il repond a voix haute. Dire "au revoir" ou Ctrl + C pour arreter.
rem Options a ajouter apres parler.py : --clavier (taper au lieu de parler), --voix-pc (voix gratuite de Windows), --micro N, --ia opus (IA plus puissante, plus lente)
cd /d "%~dp0"
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set HF_HUB_VERBOSITY=error
set PYTHONWARNINGS=ignore
.venv\Scripts\python parler.py %*
pause
