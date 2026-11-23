# La caméra au-dessus de la table (commencée le 23/11/2026)

**Essayé sur une vue simulée seulement, pas encore avec la vraie caméra.**

But : que Câlin sache OÙ se trouve un objet sur la table, en millimètres par rapport à son socle. Le bras ne bouge pas encore :
cette première étape ne fait que regarder et mesurer.

## Le principe

La webcam (Logitech C270) regarde la table d'en haut ou en biais. Quatre marqueurs imprimés, collés aux coins de la zone de
travail, lui servent de repères : dès qu'elle voit les quatre, elle sait convertir n'importe quel point de l'image en position
sur la table, même si elle est penchée.

Repère : origine sur l'axe du socle, **X vers la droite du robot** (vu de derrière le bras), **Y vers l'avant**.

## Étapes

1. **Imprimer** `sortie/marqueurs_table.pdf` sur une feuille A4, **à 100 %** (taille réelle). Le trait de contrôle en bas de page
   doit mesurer 100 mm. Découper les 4 carrés en gardant leur marge blanche.
2. **Coller** les 4 marqueurs à plat sur la table, en rectangle, vus de derrière le bras :
   0 près à gauche, 1 près à droite, 2 au fond à droite, 3 au fond à gauche. Ils doivent rester visibles quand le bras est au repos.
3. **Mesurer** à la règle, de centre à centre : la largeur (0 → 1), la profondeur (0 → 3), et la position du marqueur 0 par
   rapport à l'axe du socle (combien à gauche, combien en avant). Lancer `regler_table.bat` et taper ces 4 nombres.
4. **Lancer** `voir_table.bat` : les marqueurs vus sont entourés en vert. Cliquer sur un point de l'image affiche sa position,
   l'angle du socle et la distance pour l'atteindre. Touche Q pour quitter.

Ces programmes utilisent l'installation de la tête (`tete\installer.bat`, déjà faite). Caméra : `--camera 1` dans le lanceur
(0 = webcam du portable, voir `tete\lister_cameras.bat`).

## Ce que le calcul a vérifié (vue simulée, caméra penchée)

- les 4 marqueurs sont reconnus ; un point connu de la table est retrouvé à moins de 1 mm ;
- s'il manque un marqueur, le programme le dit et ne mesure rien.

## Limites connues

- Un point se mesure **au niveau de la table**. Le haut d'un objet haut, vu en biais, paraît décalé : cliquer sur le pied de l'objet.
- Le bras est décalé de 53,5 mm par rapport à l'axe du socle (côté à confirmer) : l'angle du socle affiché n'en tient pas encore compte.
- Pas encore de reconnaissance automatique des objets, ni de mouvement du bras : étapes suivantes.

## Fichiers

`table.py` (calculs), `generer_marqueurs.py`, `regler_table.py`, `voir_table.py`. `table.json` (tes mesures) reste sur ton PC.
