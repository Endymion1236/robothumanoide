# Coude STS3215 — V1.1 (remplace la V1)

**Pourquoi :** la V1 calculait l'écart entre les deux disques (3 + 32,9 + 4,3 = 40,2). Mesuré sur le
servo monté le 08/11/2026 : **36,4**. Les plaques de la V1 se retrouvaient pincées en V (44,3 au
palonnier, 48,3 au bout). La V1.1 prend l'écart **mesuré** (`ecart_mesure`).

| | V1 | V1.1 |
|---|---|---|
| Écart entre les plaques | 40,2 (calculé) | **36,4 (mesuré)** |
| Épaisseur totale de la fourche | 48,2 | **44,4** |
| Hauteur de chaque moitié posée à plat | 23,9 | 22,0 |
| Trous des inserts M3 | Ø4 × 7 | **Ø4 × 9** : une vis M3 × 30 entre de 7,6 mm dans le bloc du bas sans toucher le fond |

Tout le reste est identique à la V1 (voir `LIRE_AVANT_ESSAI_COUDE_V1.md` : impression, visserie,
montage). Contrôles hors Fusion refaits : pièces fermées, aucune collision au montage, tour complet
libre autour du servo ; sur le bras V1, l'avant-bras va toujours de −109° à +109°.

## Ce qui reste à éclaircir : la hauteur du boîtier

L'erreur de 3,8 mm vient d'une des trois cotes. Le modèle en **déduit** un boîtier de 29,1
(36,4 − 4,3 − 3) au lieu de 32,9 : **à mesurer**, servo sans disques, du dessous plat au dessus.
Cette cote compte pour la **bride du bras V1**, réglée sur 32,9 : si le boîtier fait vraiment 29,1,
la bride passera environ 4,8 mm au-dessus du servo au lieu de 1 mm. Il faudra alors une cale
(ou un patin plus épais) sous la bride, ou une bride corrigée.
