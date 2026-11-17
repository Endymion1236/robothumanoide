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

## À imprimer (PETG, 4 périmètres, gyroïde 40 %, sans support, déjà orientées)
| Pièce | Fichier (`sortie/`) | Environ |
|---|---|---|
| Base | `socle_base.stl` | 86 g, 110 × 104 × 40 mm |
| Palier | `socle_palier.stl` | 32 g |
| Entretoise des roulements | `socle_entretoise.stl` | 4 g |
| Plateau + moyeu (imprimé retourné, plaque sur le plateau de l'imprimante) | `socle_plateau.stl` | 124 g, 129 × 110 × 38 mm |

Le fond du moyeu (le voile vissé sur le palonnier) s'imprime en pont de 22 mm : normal s'il est un peu rugueux dessous.

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
