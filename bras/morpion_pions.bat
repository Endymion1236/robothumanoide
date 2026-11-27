@echo off
rem Morpion avec les pions raccourcis de Nicolas (28 x 40 mm) : double-clic, rien a taper.
rem Pour changer un reglage : clic droit sur ce fichier, Modifier, puis changer les nombres de la ligne du dessous.
cd /d "%~dp0"
call jouer_morpion.bat --hauteur 40 --decale 6 %*
