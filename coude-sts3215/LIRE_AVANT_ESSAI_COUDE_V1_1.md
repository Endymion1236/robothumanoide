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

## D'où venait l'erreur

Boîtier mesuré le 08/11/2026 : **28,8** (les anciennes notes disaient 32,9). D'où
36,4 = 3,3 (disque du bas) + 28,8 + 4,3 (palonnier). Le modèle porte maintenant ces valeurs ; la
géométrie de la fourche V1.1 ne change pas (elle dépend seulement de l'écart mesuré). Marges :
1,3 entre le bossage et la plaque basse, 1,7 entre la plaque basse et le socle du bras V1.

La **bride du bras V1** était réglée sur 32,9 : voir `LIRE_AVANT_ESSAI_BRAS_V1.md` (bride V1.1).
