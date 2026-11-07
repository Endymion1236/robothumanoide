# Robot humanoïde — projet de Nicolas

Premier objectif : **un petit bras de table** avec un coude en servo Feetech STS3215-C018 et une
**pince** au bout. La main robotique (ESP32, servos MG90S, gestes préenregistrés, puis gant à
capteurs et voix) viendra ensuite.

## Feuille de route

| # | Étape | État |
|---|---|---|
| 1 | Berceau de banc V4 imprimé, essai à sec (entrée, stabilité, reliefs libres, câbles) | **fait le 07/11/2026** : entre sans forcer, stable, câbles OK (hauteur côté bossage non mesurée) |
| 2 | Berceau V4.1 + bride (inserts M3, vis M3 × 10, patin 1 mm) — `berceau-sts3215/` | modèle prêt, non imprimé |
| 3 | Premier mouvement : carte Waveshare Bus Servo Adapter (A), cavaliers B, alim 12 V, logiciel FD 1.9.8.2 (COM3, 1000000) | **fait le 07/11/2026** : servo trouvé, 12,3 V, 35 °C, mouvement de 17° à vitesse 300 |
| 4 | Essai sous charge sur le banc : facultatif pour un bras de table (le servo a une grande marge) | reporté |
| 5 | Coude : fourche en deux moitiés tenant l'avant-bras des deux côtés (palonnier + disque libre du dessous) — `coude-sts3215/` | **V1 dessinée** (avant-bras 120 mm, rotation complète vérifiée hors Fusion), non imprimée ; **bras V1** (support du servo, repris du berceau V4 validé à sec) dessiné : rotation de l'avant-bras ± 109° vérifiée hors Fusion, non imprimé |
| 6 | Pince au bout de l'avant-bras | à concevoir |

## Matériel (décisions du 07/11/2026)

- **Servos** : 8 STS3215-12V (C018, 30 kg·cm, 1/345) de plus, chez Feetech (Shenzhen Feite Model, Alibaba) →
  9 en tout : bras de table complet à 6 axes + rechanges. Vérifier que disques, vis et câble sont inclus.
- **Carte** : la Waveshare Bus Servo Adapter (A) suffit pour tous les servos (en chaîne, un ID par servo).
- **Alimentation** : prévoir 12 V, 5 A minimum (6 à 10 A conseillé) pour 6 servos.
- **Socle tournant** : roulements **6807-2RS** (35 × 47 × 7), lot de 4 ; **deux roulements empilés et
  espacés** dans le socle pour que le bras ne bascule pas, le servo ne fait que tourner.

## Repères sur le servo (STS3215-C018)

- Boîtier mesuré : 45,2 × 24,4 × 32,9 mm (hauteur à recontrôler côté bossage).
- Dessous : cylindre Ø5,5 (centre à 8,1 mm du petit côté X−) et bossage 11,9 × 18,3 côté X+,
  reliefs de 2 mm ; connecteurs entre les deux.
- Étiquette : **STS3215-12V** (alimentation 12 V confirmée).
- Palonnier : **disque aluminium Ø19,7 mm**, dépasse de **4,3 mm** au-dessus du boîtier, centre à **8,1 mm** du petit côté, **aligné avec le cylindre du dessous** (remesuré le 07/11/2026 ; une première mesure à 10,5 était fausse).
  4 trous taraudés sur un cercle de **≈ 13,45 mm** de diamètre (bords intérieurs 10,3, extérieurs 16,6), petites vis fournies (taille à confirmer, probablement M3), vis centrale.
  Vis fournies : **≈ 2,5 mm de diamètre → M2,5** (trou de passage à prévoir ≈ 2,9 mm dans les pièces imprimées).
  **Second disque** fourni (palonnier libre du dessous) : 4 trous taraudés, alésage central avec collerette côté servo ; monté sur le cylindre, il **tourne librement** (pas de cannelures) et dépasse de **3 mm** sous le boîtier.
  Entre les faces extérieures des deux disques : 3 + 32,9 + 4,3 = **40,2 mm** (écart intérieur de la fourche du coude).
- **Axe de sortie au-dessus du cylindre** (côté X−) : le cylindre est **coaxial** à la sortie
  (confirmé) et sert de second pivot au coude.
- Servo « bus série » : jamais branché directement sur une broche de l'ESP32 ; carte d'interface
  et alimentation dédiée obligatoires.

## Référence utile

Les bras de table open source SO-100 / SO-101 utilisent ce même servo (6 par bras) : bonne source
d'inspiration pour le coude, le poignet et la pince.
