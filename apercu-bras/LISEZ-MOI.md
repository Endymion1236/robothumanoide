# Maquette du futur bras de table

**Maquette de principe, pas des pièces à imprimer.** Les servos sont aux vraies cotes ; les segments
sont des plaques simples pour montrer l'idée. Le bleu (avant-bras) reprend le principe du coude V1.

| Servo | Rôle | Axe |
|---|---|---|
| 1 | socle tournant | vertical |
| 2 | épaule | horizontal |
| 3 | coude (ton coude V1, couché à l'horizontale) | horizontal |
| 4 | pince | ouvre / ferme |

Bras et avant-bras de 120 mm, axe d'épaule à 95 mm de la table.

- `apercu_bras_complet.png` : trois positions (repos, penché pour attraper, levé et tourné).
- `animation_bras.gif` : prendre à droite, poser à gauche.
- `maquette_bras_complet.stl` : position « penché » ; dans Fusion : **Insérer → Insérer un maillage**,
  unités en **mm**, pour le tourner dans tous les sens.
- `apercu_bras.py` : le programme qui fabrique tout ça (longueurs en tête de fichier).
