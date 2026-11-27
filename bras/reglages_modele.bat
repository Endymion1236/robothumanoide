@echo off
rem ============================================================
rem   REGLAGES DE LA PINCE ET DES PIONS (tri et morpion)
rem   Change seulement le NOMBRE apres le signe =, sans espace.
rem   Enregistre (Ctrl+S), ferme, puis relance le tri ou le morpion.
rem ============================================================

rem Hauteur des pions, en mm (60 pour les objets d'essai, 40 pour les pions raccourcis).
set HAUTEUR=40

rem Distance, en mm, entre la machoire FIXE (celle de droite, tapis compris) et le milieu de l'avant-bras.
rem A la prise : la machoire de DROITE passe trop pres du pion -> baisse de 3. Celle de GAUCHE trop pres -> monte de 3.
set MACHOIRE_FIXE=36

rem Apres avoir lache un pion, la pince s'ecarte de ce nombre de mm vers la droite avant de remonter.
rem Le pion accroche encore a droite en remontant -> monte a 10. Il est bouscule -> baisse a 3 ou 0.
set DECALE=6

rem Retouche de la visee de prise, en mm vers la droite (negatif = vers la gauche). Laisse 0 en temps normal.
set DECALE_PRISE=0
