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
- **24/11/2026 : option A retenue** (socle tête en bas sous une tablette). Nicolas voyait plutôt une épaule humaine (option B) mais y
  renonce si c'est trop lourd. Raison : en B, trois articulations devraient porter le bras (lever devant, écarter, coude) alors que
  seuls 2 servos plus forts sont commandés, et tout le calcul serait à refaire. En A, le bras a déjà deux des trois mouvements d'une
  épaule humaine (lever devant, pivoter) ; il lui manque « écarter le bras du corps ». À rouvrir quand le buste et les deux bras marcheront.

## Habillage (choix de Nicolas, 23/11/2026)

**Peluche palomino, comme la tête.** L'ossature devient un T (barre d'épaules plus longue en haut) et l'habillage se pose
par-dessus sans rien porter : `sortie/apercu_buste_peluche.png` (squelette nu, puis habillé). Illustration de principe : les
formes seront celles de la couturière. À prévoir au dessin : dessous des épaules ouvert pour que le bras tourne, habillage
démontable (accès aux cartes et à l'arrêt d'urgence), aérations, et pas de tissu près des engrenages ou de la pince.
Les bras restent nus pour l'instant (une manche ne doit ni gêner le coude ni chauffer les servos).

**Proportions validées par Nicolas le 23/11/2026** (celles de l'illustration, à reprendre pour le dessin de l'ossature) :
colonne de 200 mm de large × 150 mm de profondeur × 400 mm de haut, barre d'épaules de 420 mm, 350 mm entre les deux axes
d'épaule, axe de l'épaule à 345 mm de la table, pied de 350 mm. Ce sont des proportions, pas encore des longueurs de coupe :
celles-ci se calculeront au dessin, après avoir fixé le modèle de profilé, les équerres et mesuré ce qui se loge dedans
(alimentation, cartes, arrêt d'urgence).
