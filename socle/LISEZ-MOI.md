# Socle tournant du bras (servo n° 1) — V1, 17/11/2026

**Prototype : aucune validation physique.** Dessiné et contrôlé par le calcul (`generer_socle.py`), jamais imprimé.
Aperçu : `sortie/apercu_socle.png` (`apercu_socle.py`).

## Le principe
- **Base** serrée sur la table (serre-joint ou 4 vis à bois). Le servo n° 1 y est **debout, palonnier en haut**, câble sorti
  par une fenêtre sur le côté.
- **Palier** : une plaque vissée sur les 4 poteaux de la base (4 vis M3 × 10 dans des inserts). Elle appuie sur le servo
  comme une bride (0,5 mm de serrage) et porte un tube où logent les **2 roulements 6807** (47 × 35 × 6,8 mesurés),
  séparés par une **entretoise** : leurs milieux sont à 20 mm l'un de l'autre.
- **Plateau** : une plaque au contour du pied du bâti, avec un **moyeu creux** (Ø 34,9) qui descend dans les 2 roulements
  et se visse sur le palonnier (4 vis M2,5, tournevis par le creux du moyeu).
- Le **bâti** se visse sur le plateau par les 4 trous de son pied (4 vis M3 × 12 dans 4 inserts). Rien à réimprimer sur le bâti.
- Le poids (moins d'1 kg) descend par le servo ; les 2 roulements reprennent le basculement du bras tendu (≈ 1,7 N·m).
- Rotation prévue : **± 90°** (butées du servo 1024–3072), câbles de l'épaule passés par l'extérieur avec une boucle.
- L'axe de rotation passe **sous l'axe de l'épaule**, au milieu des 4 trous du pied. La pince travaille dans un plan
  décalé de 53,5 mm de cet axe : le programme en tiendra compte.
- Axe de l'épaule à **179 mm** au-dessus de la table (101 sans le socle).

## Plan de travail surélevé (choix du 17/11/2026)
Le socle rehausse le bras de **78 mm**. Épaule au plus bas (−30°), avant-bras à plat : le bas des mâchoires arrive à 6 mm de
la table sans socle, à **84 mm** avec. Les objets à saisir se posent donc sur un **plan de travail surélevé de 78 mm**
(planche sur cales, caisse, support de la station café) : on retrouve la géométrie d'origine. Autres pistes écartées pour
l'instant : base fixée 78 mm sous la table, socle plus bas (gain ≈ 1 cm seulement), flexion du poignet.

**Cales à imprimer** (`generer_cales.py`) : 4 cales par planche, une à chaque coin. C'est le DESSUS DE LA PLANCHE qui doit
être à 78 mm : la hauteur de la cale dépend donc de l'épaisseur de la planche.

| Planche | Cale | Fichier (`sortie/`) | Vis à bois Ø 4, longueur maxi |
|---|---|---|---|
| 5 mm | 73 mm | `cale_planche_5mm.stl` | 13 mm |
| 10 mm | 68 mm | `cale_planche_10mm.stl` | 18 mm |
| 12 mm | 66 mm | `cale_planche_12mm.stl` | 20 mm |
| 15 mm | 63 mm | `cale_planche_15mm.stl` | 23 mm |
| 18 mm | 60 mm | `cale_planche_18mm.stl` | 25 mm |

Pied carré de 40 mm, imprimé debout sans support, 15 % de remplissage et 3 périmètres suffisent (environ 45 g pièce).
La vis à bois entre par-dessous, dans un puits de 9 mm, et traverse les 10 derniers mm avant d'entrer dans la planche.

## À imprimer (PETG, 4 périmètres, gyroïde 40 %, sans support, déjà orientées)
| Pièce | Fichier (`sortie/`) | Environ |
|---|---|---|
| Base | `socle_base.stl` | 86 g, 110 × 104 × 40 mm |
| Palier | `socle_palier.stl` | 32 g |
| Entretoise des roulements | `socle_entretoise.stl` | 4 g |
| Plateau + moyeu (imprimé retourné, plaque sur le plateau de l'imprimante) | `socle_plateau.stl` | 124 g, 129 × 110 × 38 mm |

Le fond du moyeu s'imprime en pont de 19 mm **sans support** : une peau pleine de 0,4 mm ferme les 5 trous du côté du creux
(sans elle, le pont n'a rien où s'accrocher autour des trous : alerte de PrusaSlicer du 18/11/2026). Après l'impression,
percer cette peau en passant un foret de 2,5 à 3 mm par les 4 petits trous, depuis le bout du moyeu ; le trou du centre
peut rester fermé (il ne sert qu'à dégager la vis centrale du palonnier).

## Ordre d'impression conseillé (premier essai des ajustements)
1. `socle_essai_moyeu.stl` (bague de 12 mm de haut, 5 g) : elle doit entrer à la main dans un roulement 6807, sans jeu sensible.
2. `socle_palier.stl` : les 2 roulements doivent y entrer en appuyant, sans forcer ni flotter.
3. `socle_base.stl` : le servo doit s'y poser à plat, palonnier libre.
4. `socle_entretoise.stl`, puis `socle_plateau.stl` (le plus gros) seulement si 1 et 2 sont bons ; sinon donner l'écart
   constaté, les diamètres seront corrigés.
Avant le montage : le servo du socle porte le n° 1, donc le coude doit d'abord passer au n° 3.

**Plan de montage illustré : `sortie/plan_montage_socle.pdf`** (8 étapes, `plan_montage.py` ; outils de dessin partagés dans
`epaule/plan_montage_epaule_outils.py`). Servo du socle : n° 1, butées 1024–3072, monté à 2048. Le coude passe au n° 3 (étape 8).

## Visserie
8 inserts M3 (4 en haut des poteaux de la base, 4 dans le plateau), 4 vis M3 × 10 (palier), 4 vis M3 × 12 (pied du bâti),
4 vis M2,5 du palonnier (3,4 mm de plastique traversé, comme au coude), 2 roulements 6807.

## Contrôles faits
Pièces fermées, d'un seul bloc ; aucune pénétration entre base, servo, palier, roulements, entretoise ; plateau tourné de
−90° à +90° sans contact ; le palonnier (Ø 19,7) déborde du bout du servo de 1,75 mm : le mur de la base est abaissé dessous.

## Ce que le calcul ne dit pas
- Les ajustements : roulements dans le tube (47,1), moyeu dans les roulements (34,9 pour 35). Selon l'imprimante, un
  léger ponçage du moyeu peut être nécessaire ; il doit entrer à la main, sans jeu sensible.
- La rigidité réelle (jeu du bras en bout de course) et la tenue du serre-joint.
- Le passage des câbles pendant la rotation.
