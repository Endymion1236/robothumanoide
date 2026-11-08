# Coude STS3215 — V1.2 (remplace la V1 et la V1.1 : n'imprimer que celle-ci)

## Le dessus du servo n'a pas la même hauteur partout (mesures du 08/11/2026)

```
   palonnier
   ┌──────┐┌───────────── partie haute (plaque de l'étiquette) ─────────────┐
   │ 28,8 ││                         33                                      │
   └──────┘└─────────────────────────────────────────────────────────────────┘
   ← 15,6 →
```

- Côté palonnier : **28,8** du dessous plat au dessus ; le palonnier dépasse de 4,3.
- À partir de **15,6** du bout côté palonnier : **33** (aux deux bouts, côté étiquette et au-dessus des câbles).
- Entre les faces extérieures des deux disques : **36,4** = 3,3 + 28,8 + 4,3.

## Les versions

| | V1 | V1.1 | **V1.2** |
|---|---|---|---|
| Écart entre plaques au palonnier | 40,2 (calculé, faux) | 36,4 (mesuré) | **36,4** |
| Plaque haute au-dessus de la partie haute (33) | — | **0,1** : frotte | **1,0** |
| Comment | — | plaque à plat sur le palonnier | **patin Ø18 × 0,9** sous la plaque, seul en appui sur le palonnier ; le reste de la plaque est 0,9 plus haut |
| Épaisseur totale de la fourche | 48,2 | 44,4 | **45,3** |

## Contrôles faits (hors Fusion, `CoudeV1_2/verify_coude.py`)

- Moitiés fermées, d'un seul volume, 132 × 24 × 22,45 posées à plat (déjà orientées pour l'impression).
- Aucune collision au montage ; **tour complet libre** autour du servo, partie haute comprise
  (1 mm sous la plaque haute, 1,3 entre le bossage et la plaque basse).
- Sur le bras V1 : rotation de **−109° à +109°** ; 1,7 entre la plaque basse et le socle.
- Vis M3 × 30 : 7,15 dans le bloc du bas (trou d'insert de 9).
- Vis M2,5 dans les disques : 4 + 0,9 − 1,5 (lamage) = 3,4 traversés ; une M2,5 × 6 entre de 2,6 dans le disque.

**Supposé, à vérifier sur le servo :** autour du palonnier, la partie haute s'écarte du disque en
arc (rayon 10 pris dans le modèle). Le palonnier tourne déjà sans toucher la partie haute : le
patin, plus petit que le palonnier (Ø18 contre 19,7), ne la touche pas non plus.

Impression, visserie et montage : comme la V1 (`LIRE_AVANT_ESSAI_COUDE_V1.md`), avec les fichiers
`outputs/coude_v1_2/fourche_haute_V1_2.stl` et `fourche_basse_V1_2.stl`.
