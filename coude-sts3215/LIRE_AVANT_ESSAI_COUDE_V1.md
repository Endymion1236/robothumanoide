# Coude STS3215 — V1 : fourche d'avant-bras en deux moitiés

Unités : mm. **Prototype : aucune validation physique.** Le script Fusion `CoudeV1/CoudeV1.py`
n'a pas encore été exécuté ; les STL de `outputs/coude_v1/` ont été construits hors de Fusion
(`verify_coude.py`, mêmes paramètres).

## Principe

Le servo est pris en sandwich : la **moitié haute** se visse sur le palonnier, la **moitié basse**
sur le disque libre monté sur le cylindre du dessous. Les deux moitiés se serrent l'une sur l'autre
par deux entretoises vissées. L'écart entre les deux plaques vaut 3 + 32,9 + 4,3 = **40,2**
(disque bas + boîtier + palonnier). Les demi-entretoises laissent **0,4 mm** entre elles : ce jeu
se ferme au serrage et absorbe les petites erreurs d'impression.

| | Valeur |
|---|---|
| Longueur de l'avant-bras (axe → bout) | 120 (paramètre `avant_bras_L`) |
| Plaques | 24 de large, 4 d'épaisseur, bout arrondi R12 autour de l'axe |
| Trous des disques | 4 × Ø2,9 (M2,5) sur cercle Ø13,45, à 45°, lamés Ø5,2 × 1,5 côté extérieur ; Ø7 au centre |
| Entretoise A | de 50 à 62 depuis l'axe (le coin du servo le plus éloigné tourne à 39,1) |
| Entretoise B | les 15 derniers mm, futur support de la pince |
| Pièces | 2 × environ 24 cm³ (≈ 30 g de PETG chacune) |

## Contrôles faits (hors Fusion)

- Chaque moitié : fermée, d'un seul volume ; 132 × 24 × 23,9 posée à plat.
- Aucune collision au montage entre les deux moitiés, le servo et les disques.
- **Rotation : le servo a été tourné de −180° à +180° par pas de 2° : aucune collision.**
  Seule la future pièce « bras » (qui tiendra le servo) limitera la course.
- Marges : 1 mm entre le bossage et la plaque basse, 3 mm entre le boîtier et la plaque basse,
  4,3 mm entre le boîtier et la plaque haute.

Non vérifié : rigidité, tenue des vis M2,5 dans les disques, précision d'impression, passage réel
du câble (il doit rester **couché dans sa rainure** et sortir par le côté du servo).

## Impression

- Les deux STL de `outputs/coude_v1/` sont **déjà posés plaque sur le plateau** : ne pas les retourner.
  (Les STL exportés par Fusion sont en position de montage : la moitié haute devra être retournée.)
- PETG, **4 périmètres** au moins, remplissage 30 à 40 %. Pas de support nécessaire.

## Visserie

| Quoi | Combien | Où |
|---|---|---|
| Vis M2,5 × 6 (celles fournies avec le servo si leur longueur convient) | 8 | 4 par plaque, dans les disques |
| Inserts M3 à chaud | 4 | moitié basse, en haut des demi-entretoises (Ø4, profondeur 7) |
| Vis M3 × 30 | 4 | de la moitié haute vers les inserts de la moitié basse |

Vérifier que les vis M2,5 ne touchent pas le fond des trous des disques : 4 mm de plaque − 1,5 de
lamage = 2,5 mm traversés, une vis de 6 mm entre donc de 3,5 mm dans le disque.

## Montage

1. Poser les 4 inserts M3 dans la moitié basse (fer à souder, 220-240 °C pour le PETG).
2. Monter le disque libre sur le cylindre du dessous, puis visser la moitié basse dessus (4 × M2,5).
3. Visser la moitié haute sur le palonnier (4 × M2,5). Le palonnier a des cannelures : choisir sa
   position pour que l'avant-bras soit dans l'axe quand le servo est au milieu de sa course
   (position ≈ 2048 dans FD).
4. Serrer les deux moitiés par les 4 vis M3 × 30, **doucement et en croix** : s'arrêter dès que les
   demi-entretoises se touchent.
5. Servo hors tension : tourner l'avant-bras à la main sur toute la course. Il doit tourner sans
   point dur ; un frottement indique un écart d'impression.

## Pour l'essai

Il n'y a pas encore de pièce « bras » pour tenir le servo : pour ce premier essai, tenir le servo à
la main ou le serrer **doucement** dans un étau garni de tissu, par ses deux grandes faces, puis le
faire bouger lentement dans FD (vitesse 300). Le berceau V4 ne convient pas : la moitié basse passe
sous le servo, là où le berceau a son socle.
