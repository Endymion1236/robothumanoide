# Bras V1 — support du servo pour le coude

Repris du berceau V4.1, validé à sec le 07/11/2026 (le servo entre sans forcer, il est stable,
les câbles passent). Unités : mm. **Prototype : aucune validation physique du bras lui-même.**
Le script Fusion `BrasV1/BrasV1.py` n'a pas encore été exécuté ; les STL de `outputs/bras_v1/`
ont été construits hors de Fusion (`verify_bras.py`, mêmes paramètres).

## Ce qui change par rapport au berceau V4.1

| | Berceau V4.1 | Bras V1 |
|---|---|---|
| Côté de l'axe (X local 0 à 27) | parois, appuis, butée | **tout dégagé** jusqu'à la fin de la fenêtre des câbles : la fourche tourne autour |
| Hauteur des appuis | 7 | **9** : la moitié basse de la fourche passe sous le servo, **2 mm** au-dessus du socle |
| Parois | 17 | 19 (toujours 10 mm de guidage le long du servo) |
| Butée côté axe | paroi | **nervure devant le bossage** (1,2 × 14, 0,5 mm de jeu, sommet 0,5 mm sous le servo : elle bloque, elle ne porte pas) |
| Surface d'appui | 140,8 mm² | 72,8 mm² (bandes de X local 27 à 45,2) |
| Hauteur totale | 45,9 (49,9 avec bride) | 47,9 (51,9 avec bride) |

Inchangé : socle 80 × 60 × 5, logement 45,6 × 24,8 (jeu 0,2), bandes d'appui de 2, bride côté
bossage avec inserts M3 et vis M3 × 10, 1 mm de jeu pour le patin, 4 trous de fixation Ø4,5.

## Contrôles faits (hors Fusion)

- Bras et bride : fermés, d'un seul volume, aucune collision avec le servo ni les fiches estimées.
- **Coude V1 monté sur le bras : l'avant-bras tourne de −109° à +109°** (pas de 1°), 0° = avant-bras
  dans le prolongement du servo. Au-delà, la plaque basse de la fourche touche le coin d'une colonne
  de la bride et des parois. (J'avais annoncé environ ± 145° avant le calcul : c'était trop optimiste.)
- `outputs/bras_v1/verification_rotation_coude_bras_V1.json` et `apercu_coude_sur_bras_V1.png`.

**Dans FD, ne jamais commander l'avant-bras au-delà de ± 100°** autour de sa position dans l'axe
(environ ± 1140 pas de part et d'autre) tant que des butées logicielles ne sont pas réglées.

## Impression et montage

1. Imprimer `bras_V1_TEST.stl` (socle sur le plateau) et `bride_bras_V1_TEST.stl` (à plat), PETG,
   4 périmètres.
2. Poser les 2 inserts M3 en haut des colonnes.
3. Glisser le servo dans le bras, bossage derrière la nervure, câble couché dans sa rainure et sorti
   par la fenêtre.
4. Monter la fourche du coude (voir `LIRE_AVANT_ESSAI_COUDE_V1.md`).
5. Patin caoutchouc de 1 à 1,5 mm sur le servo, bride, vis M3 × 10 serrées doucement.
6. Hors tension : tourner l'avant-bras à la main de butée à butée, sans forcer.
