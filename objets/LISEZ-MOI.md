# Objets d'essai pour la reconnaissance et le tri (25/11/2026)

Cinq objets simples à imprimer, pour apprendre à la caméra à trouver les objets et au bras à les trier.
Ce ne sont pas des pièces du robot : aucune cote à respecter au dixième, aucun réglage d'impression exigeant.

| Fichier (`sortie/`) | Forme vue de dessus | Taille | Ce qu'il permet de tester |
|---|---|---|---|
| `objet_rond_grand.stl` | rond | Ø 40 × 60 | la prise la plus facile ; le tri par taille (avec le petit) |
| `objet_rond_petit.stl` | rond | Ø 28 × 60 | le tri par taille : la pince mesure la largeur en serrant |
| `objet_carre.stl` | carré | 36 × 36 × 60 | reconnaître une forme ; prise sur deux faces plates |
| `objet_hexagone.stl` | hexagone | 38 entre plats × 60 | une forme proche du rond : est-ce que la caméra fait la différence ? |
| `objet_allonge.stl` | rectangle | 64 × 26 × 60 | l'orientation : il faudra tourner le poignet pour le prendre en travers |

**Impression** : debout, sans support, 2 périmètres, 10 % de remplissage, PLA ou PETG. De 14 à 37 g pièce, environ 135 g le jeu.

**Couleurs** : c'est ce qui aidera le plus la caméra. Sur la table en bois, prendre des couleurs franches qui tranchent :
blanc, bleu, vert vif, rouge. Éviter le marron, le beige, le jaune pâle et le noir (les marqueurs sont noirs).
Pour un premier tri par couleur : imprimer le même objet (le rond de 40) en deux couleurs, 2 ou 3 exemplaires de chaque.

**Pourquoi 60 mm de haut** : la pince saisit bas (bas des mâchoires à 2 cm de la table) ; il lui faut de la matière à serrer,
surtout quand elle est inclinée. **Pourquoi 26 à 40 mm de large** : le milieu de la plage de la pince V4 (14 à 110 mm au dessin).

Rien n'a encore été saisi ni reconnu : ce sont des objets pour commencer les essais.
`generer_objets.py` les refait ; `sortie/apercu_objets.png` les montre.
