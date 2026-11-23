# Le buste — illustration de principe (23/11/2026)

`sortie/apercu_buste.png` (produit par `apercu_buste.py`) montre le bras actuel monté sur un buste, avec la tête de poney.
**Ce n'est pas un plan : le buste n'est pas dessiné.** Seules les longueurs du bras sont les vraies
(haut du bras 120 mm, avant-bras 161 mm, poignet et pince 200 mm).

Ce que l'illustration suppose :
- ossature de la feuille de route (profilés 20 × 20, boîte de 20 × 15 × 40 cm, pied en croix) ;
- une tablette d'épaule de chaque côté, le socle tournant fixé dessous **tête en bas** : le bras pend au lieu de se dresser ;
- le deuxième bras (gris clair) est le même en symétrique, plus tard.

Ce qu'elle fait apparaître, à trancher quand on dessinera vraiment le buste :
- **hauteur de l'épaule** : à 34,5 cm de la table, la pince atteint la table à plat, mais le bras (48 cm) ne peut pas pendre
  tout droit : au repos le coude reste plié. Plus haut (50 cm), il pendrait, mais n'atteindrait plus la table qu'en pointant
  la pince vers le bas ;
- bras pendu = pesanteur inversée par rapport au montage de table : le ressort et la course de l'épaule sont à revoir ;
- la tête et le bras tendu déplacent le poids vers l'avant : pied large et lesté.

## Décisions

- **24/11/2026 : épaule à environ 35 cm de la table** (choix de Nicolas) : la pince atteint la table à plat ; au repos le coude reste plié.
- Orientation du socle tournant sur le buste, à trancher :
  **A. axe vertical, socle fixé tête en bas sous une tablette d'épaule** (celle de l'illustration) : le bras fonctionne comme sur la
  table, mêmes programmes et mêmes calculs ; conseillé pour commencer.
  **B. axe horizontal, socle fixé sur le flanc du buste** : plus proche d'une épaule humaine (lever devant + écarter), mais le servo du
  socle porterait alors tout le bras, les roulements travailleraient en porte-à-faux et le calcul des positions serait à refaire.
