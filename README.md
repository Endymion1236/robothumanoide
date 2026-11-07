# Robot humanoïde — projet de Nicolas

Premier objectif : **un petit bras de table** avec un coude en servo Feetech STS3215-C018 et une
**pince** au bout. La main robotique (ESP32, servos MG90S, gestes préenregistrés, puis gant à
capteurs et voix) viendra ensuite.

## Feuille de route

| # | Étape | État |
|---|---|---|
| 1 | Berceau de banc V4 imprimé, essai à sec (entrée, stabilité, reliefs libres, câbles, hauteur côté bossage) | impression en cours (07/11/2026) |
| 2 | Berceau V4.1 + bride (inserts M3, vis M3 × 10, patin 1 mm) — `berceau-sts3215/` | modèle prêt, non imprimé |
| 3 | Premier mouvement : carte Waveshare Bus Servo Adapter (A), cavaliers B, alim 12 V, logiciel FD 1.9.8.2 (COM3, 1000000) | **fait le 07/11/2026** : servo trouvé, 12,3 V, 35 °C, mouvement de 17° à vitesse 300 |
| 4 | Essai sous charge sur le banc : barre ≈ 15 cm, 100-200 g au palonnier (position tenue, charge, température) | à faire |
| 5 | Coude : fourche tenant l'avant-bras des deux côtés (palonnier + cylindre Ø5,5 du dessous comme pivot) | à concevoir |
| 6 | Pince au bout de l'avant-bras | à concevoir |

## Repères sur le servo (STS3215-C018)

- Boîtier mesuré : 45,2 × 24,4 × 32,9 mm (hauteur à recontrôler côté bossage).
- Dessous : cylindre Ø5,5 (centre à 8,1 mm du petit côté X−) et bossage 11,9 × 18,3 côté X+,
  reliefs de 2 mm ; connecteurs entre les deux.
- Étiquette : **STS3215-12V** (alimentation 12 V confirmée).
- Palonnier : **disque aluminium Ø19,7 mm** (mesuré le 07/11/2026), 4 trous taraudés + vis centrale ; entraxe des trous, filetage et hauteur au-dessus du boîtier à mesurer.
- **Axe de sortie au-dessus du cylindre** (côté X−) : le cylindre est probablement coaxial à la
  sortie, à confirmer, et servirait de second pivot au coude.
- Servo « bus série » : jamais branché directement sur une broche de l'ESP32 ; carte d'interface
  et alimentation dédiée obligatoires.

## Référence utile

Les bras de table open source SO-100 / SO-101 utilisent ce même servo (6 par bras) : bonne source
d'inspiration pour le coude, le poignet et la pince.
