# Pince à mâchoires parallèles (V2)

**V2 (11/11/2026)** — Nicolas a demandé si la V1 n'était pas trop étroite : elle l'était. Un gobelet de 80 mm
tenu au milieu des mâchoires **butait contre la base et l'engrenage A**, la marge pour l'attraper n'était que
de 7,5 mm par côté, et des mâchoires plates tiennent mal un objet rond. V2 : bras de 50 mm, **ouverture
110 mm**, mâchoires de **40 mm**, placées plus en avant et **creusées en arrondi** (rayon 45) qui centrent
le gobelet. Les fichiers de la V1 sont remplacés.

Pour le bras de Câlin : prendre un **gobelet moyen** (jusqu'à 110 mm d'écart), avec un servo STS3215.
Fichiers à imprimer dans `sortie/` (déjà posés pour l'impression). Programme : `generer_pince.py`
(toutes les cotes en tête de fichier), images : `apercu_pince.py`. **Prototype : aucune validation physique.**

## Principe

Le servo tourne l'**engrenage A** ; l'**engrenage B**, identique, tourne en sens inverse. Chaque engrenage
porte un **bras moteur**, doublé d'un **bras libre** parallèle : chaque **doigt** reste parallèle à l'autre
et ils se rapprochent ensemble, gobelet au centre. Les doigts descendent pour prendre un gobelet debout.

À savoir : en se fermant, les doigts **avancent un peu** (environ 28 mm entre grand ouvert et fermé), comme
une main qui glisse le long du gobelet. C'est le prix d'une pince simple à bras pivotants.

## Contrôles faits (hors impression)

- Mouvement complet de **14 à 110 mm** d'écart (mesuré au creux des mâchoires), vérifié en **24 positions** :
  **aucune collision** entre les pièces mobiles, ni avec la base, la bride, le servo ou l'avant-bras.
- **Gobelets** (`test_gobelets.py`) : 55, 80 et 90 mm de diamètre, tenus au milieu des mâchoires ou par le
  haut : ils ne touchent **que les mâchoires**. Marge derrière le gobelet : 30 mm (55), 10,5 mm (80),
  1,2 mm (90 : juste). Marge pour l'attraper, mâchoires grandes ouvertes : 27,5 / 15 / 10 mm par côté.
- Engrenages : module 1,5, 20 dents, jeu entre dents de 0,35 mm (une impression n'est jamais parfaite).
- Fermée au maximum : 14 mm au creux, 4,6 mm entre les bouts des mâchoires (en dessous, elles se
  toucheraient) : c'est la butée du servo. Objets plus fins que 5 mm : pas pour cette pince.
- La pince passe **1 mm au-dessus de la partie haute** du servo (même leçon que le coude), bride à cale
  (0,5 mm de serrage) sur la partie haute.
- Masse : environ **88 g** de pièces imprimées + 55 g de servo = **143 g**.

## À imprimer (PLA ou PETG, 4 périmètres, remplissage 40 %)

| Pièce | Fichier |
|---|---|
| Base (logement du servo + manchon sur l'avant-bras + poteaux) | `pince_base.stl` |
| Bride (porte aussi un pivot) | `pince_bride.stl` |
| Engrenage A (sur le palonnier) | `pince_engrenage_A.stl` |
| Engrenage B | `pince_engrenage_B.stl` |
| Bras libres | `pince_bras_libre_+Y.stl`, `pince_bras_libre_-Y.stl` |
| Doigts | `pince_doigt_+Y.stl`, `pince_doigt_-Y.stl` |

**Toutes les pièces sont déjà orientées pour l'impression, sans support** (vérifié : chaque pièce repose à
plat sur le plateau). Corrigé le 11/11/2026 : les doigts, l'engrenage A et la bride étaient mal posés dans
la première version des fichiers. Les doigts s'impriment debout (plaque sur le plateau, mâchoire vers le
haut) ; la bride a maintenant un dessous plat : ses piliers s'arrêtent 0,5 mm sous le dessus du servo, et
c'est le vissage qui serre.

### Conseils pour les engrenages

- Couches fines : **0,12 à 0,16 mm** (dents plus régulières) ; buse 0,4 : très bien pour ce module 1,5.
- **4 périmètres** au moins, ou remplissage 100 % : les dents sont petites.
- Vitesse lente sur les parois extérieures ; pas de « ironing ».
- Si la première couche est écrasée (« pied d'éléphant »), les dents frottent : activer la compensation
  dans le trancheur, ou ébavurer au cutter.
- **Essai rapide** : imprimer d'abord les deux engrenages seuls et vérifier, posés sur une table l'un
  contre l'autre (entraxe 30 mm), qu'ils tournent sans accrocher.
- **Roulements** : logement de 10,1 mm pour des roulements de 10 mm. Ils doivent entrer en forçant un peu
  au doigt. Trop dur : passer un coup de foret de 10 à la main ; trop lâche : une goutte de colle.

## Visserie

| Quoi | Combien | Où |
|---|---|---|
| Roulements 623ZZ (commandés) | 7 | engrenage B (1), bras libres (2), doigts (4) |
| Inserts M3 à chaud | 5 | piliers de la bride (2), poteau de l'engrenage B, poteau du bras libre -Y, pivot sur la bride |
| Vis M3 × 10 | 5 | bride (2), engrenage B (1), pivots des bras libres (2) |
| Vis M3 × 8 | 2 | bout des bras libres, vissées dans le plastique (ou M3 × 10 + 2 rondelles sous la tête) |
| Vis M3 × 16 (14 à 20 conviennent) + écrou frein | 2 | doigt sur le bras de l'engrenage |
| Rondelles M3 (DIN 125, 0,5 mm) | 4 | entre doigt et bras d'engrenage (2), entre bras libre et doigt (2) |
| Vis M2,5 × 8 (fournies avec le servo) | 4 | engrenage A sur le palonnier |
| Les 2 vis M3 × 30 de l'entretoise du bout de l'avant-bras | (déjà là) | traversent le manchon de la pince |

Correction du 11/11/2026 : au bout des bras libres, un écrou sous le doigt aurait tapé dans le bras de
l'engrenage pince presque fermée. Une vis M3 × 8 s'y visse maintenant directement dans le bras (trou de 2,8) ; une M3 × 10 seule arriverait au ras du bras
de l'engrenage. Vérifié par `verifier_visserie.py` (vis, écrous, rondelles sur toute la course : aucun contact, 2 mm de marge).
Les passages de tête au-dessus des roulements font 6,5 mm : la vis n'appuie que sur la bague intérieure, sans rondelle.
**Pièces à réimprimer si elles l'ont déjà été : les 2 bras libres et l'engrenage B.**

## Montage

**Plan illustré, une page par étape : `sortie/plan_montage.pdf`** (aussi en images `sortie/plan_montage_00.png` à `_09.png`),
refait par `python plan_montage.py` après `generer_pince.py`. Il remplace l'ancienne liste d'étapes.

**Premier essai motorisé** : `bras/tester_pince.bat` (voir `bras/LISEZ-MOI.md`) : ouvrir, fermer, serrer avec une force limitée.

## Limites à connaître

- **Poids au bout du bras** : pince 143 g + un gobelet moyen plein (300 g environ) = plus de 400 g à
  25 cm de l'épaule. C'est beaucoup pour un STS3215 en continu : servir d'abord des **gobelets vides ou
  petits**, et prévoir peut-être un servo plus fort pour l'épaule.
- **Force de serrage** : le servo peut écraser un gobelet en carton. Il faudra limiter son couple
  (réglage dans le servo) avant les essais avec de vrais gobelets.
- Le sens « ouvrir » (vers la butée min ou max) se vérifie au premier essai.
