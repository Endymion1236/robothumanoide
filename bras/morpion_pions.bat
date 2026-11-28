@echo off
rem Morpion avec les reglages de Nicolas : double-clic, rien a taper.
rem Pour changer un reglage : double-clic sur REGLAGES.bat (il ouvre mes_reglages.bat dans le Bloc-notes).
cd /d "%~dp0"
if not exist mes_reglages.bat copy /y reglages_modele.bat mes_reglages.bat >nul
call mes_reglages.bat
if not defined APPUI set APPUI=12
echo Reglages : pions de %HAUTEUR% mm, machoire fixe a %MACHOIRE_FIXE% mm, decalage au lacher %DECALE% mm, retouche de prise %DECALE_PRISE% mm, appui %APPUI% mm.
call jouer_morpion.bat --hauteur %HAUTEUR% --decale %DECALE% --machoire-fixe %MACHOIRE_FIXE% --decale-prise %DECALE_PRISE% --appui %APPUI% %*
