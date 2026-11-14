# Pince à mâchoires parallèles (V3)

**V3 (14/11/2026) : sans point mort.** Essai réel de la V2 le 14/11/2026 : en se refermant à vide, un doigt s'est
retourné d'un quart de tour ; à la réouverture la pince s'est coincée et les dents des engrenages ont sauté
(« clac clac »). Cause : en V2, le pivot du bras libre était juste **derrière** celui du bras de l'engrenage.
Vers 20 mm d'écart entre les mâchoires, les deux bras s'alignaient avec le doigt : à ce **point mort**, plus rien
ne tenait le doigt droit. Le contrôle de collision ne pouvait pas le voir : il supposait les doigts toujours parallèles.

Ce qui change :

| | V2 | **V3** |
|---|---|---|
| Pivot du bras libre | 24 mm derrière le pivot de l'engrenage, sur la bride d'un côté | **en diagonale** : 38 mm derrière et 19 mm vers l'extérieur, sur **deux grands poteaux de la base**, appuyés contre le manchon |
| Point mort | à 20 mm d'écart : **dans la course** | à un angle que la pince ne peut pas atteindre (les mâchoires se touchent 20° avant) |
| Bras de levier qui tient le doigt droit | 0 à 21,6 mm (8,4 mm sur un gobelet de 55) | **16,7 à 42,5 mm** (31 mm sur un gobelet de 55) |
| Fond des dents des engrenages | en V : la tête de la dent d'en face passait à **0,03 mm** | plat : **0,33 mm** de place |
| Poteau de l'engrenage B | Ø 12 | **Ø 16**, appuyé contre le mur du servo |
| Bride | portait un pivot | simple barre |
| Programme (`bras/`) | pince coincée : le servo poussait 8 s | **force coupée en 1 s** |

Inchangé : bras de 50 mm, ouverture 14 à 110 mm, mâchoires creusées, butées du servo **1663–2433**, étalonnage à
**81 mm** entre les vis du bout des bras (71 mm au creux des mâchoires), toute la visserie.
Les **bouchons** sont les mêmes pièces qu'en V2. Les **bras libres** sont élargis à 15 mm (14/11/2026) : à 12 mm il ne
restait que 0,95 mm de paroi autour des roulements, et le roulement l'a fendue en entrant. Il y a maintenant 2,45 mm,
et `generer_pince.py` refuse toute paroi de moins de 1,8 mm autour d'un roulement.

À savoir :
- La pince est **plus large** : les bras libres dépassent sur les côtés. Largeur hors tout : 77 mm fermée, 143 mm sur un
  gobelet de 80, 173 mm grande ouverte (la V2 faisait environ 134 mm grande ouverte).
- Masse : environ 98 g de pièces + 55 g de servo = **153 g** (10 g de plus que la V2).
- Le doigt de l'engrenage B a un petit jeu (environ 1 mm de chaque côté au bout du bras) : c'est la place entre les
  dents. Il disparaît dès que la pince serre.
- **Prototype : aucune validation physique de la V3.**

## Vérifications (toutes relancées le 14/11/2026)

**Une seule commande : `python tout_verifier.py`** (il faut `pip install numpy trimesh manifold3d python-fcl pyserial`).

| Programme | Ce qu'il vérifie | Résultat |
|---|---|---|
| `generer_pince.py` | pièces fermées, d'un seul bloc ; aucune collision en 24 positions ; chaque pièce posée à plat pour l'impression ; tournevis des vis du manchon et sortie du câble libres | bon |
| `verifier_cinematique.py` | **le doigt ne peut pas se retourner** : calcule les deux positions possibles du doigt (droit, retourné) et la distance au point mort, butées dépassées de 15° comprises. Refait le calcul sur la V2 : il **trouve bien le défaut** (point mort à 0°, doigt retourné de 89° pince ouverte, comme sur la photo) | V3 bonne, V2 en défaut |
| `verifier_engrenages.py` | place entre les dents sur un pas complet, et avec l'engrenage B décalé de 0,5° | 0,33 mm / 0,21 mm |
| `verifier_jeux.py` | distance la plus courte entre toutes les pièces sur toute la course (39 paires, 14 positions) | rien d'imprévu à moins de 1,5 mm |
| `verifier_visserie.py` | vis, écrous et rondelles ne touchent rien sur toute la course | bon |
| `test_gobelets.py` | gobelets de 55, 80 et 90 mm : ils ne touchent que les mâchoires (marge derrière : 29,8 / 10,5 / 1,2 mm) | bon |
| `../bras/test_securites.py` | les sécurités du programme sur un faux servo : butées, chaleur, **pince coincée → force coupée en 1 s**, serrage | bon |

Ce que les calculs ne disent pas : la tenue réelle des poteaux (hauts de 52 mm) quand la pince serre, et le
frottement des pièces imprimées. C'est l'essai à la main de l'étape 9 du plan de montage qui le dira.

## Principe

Le servo tourne l'**engrenage A** ; l'**engrenage B**, identique, tourne en sens inverse. Chaque engrenage
porte un **bras moteur**, doublé d'un **bras libre** parallèle et de même longueur : chaque **doigt** reste parallèle
à l'autre et ils se rapprochent ensemble, gobelet au centre. Les doigts descendent pour prendre un gobelet debout.

En se fermant, les doigts **avancent un peu** (environ 28 mm entre grand ouvert et fermé), comme une main qui
glisse le long du gobelet. Fermée au maximum : 14 mm au creux, 4,6 mm entre les bouts des mâchoires (butée du
servo). Objets plus fins que 5 mm : pas pour cette pince.

## À imprimer (PLA ou PETG, 4 périmètres, remplissage 40 %)

| Pièce | Fichier |
|---|---|
| Base (logement du servo + manchon sur l'avant-bras + 3 poteaux) — **nouvelle en V3** | `pince_base.stl` |
| Bride (simple barre) — **nouvelle en V3** | `pince_bride.stl` |
| Engrenage A (sur le palonnier) — **dents refaites en V3** | `pince_engrenage_A.stl` pour des vis M2,5 × 8 ; avec les vis courtes fournies avec le servo : `pince_engrenage_A_vis4mm.stl`, `_vis5mm` ou `_vis6mm` selon leur longueur sous tête (logement des têtes plus profond : la vis entre de 2 à 2,5 mm dans le palonnier) |
| Engrenage B — **dents refaites en V3** | `pince_engrenage_B.stl` |
| Bras libres (élargis à 15 mm le 14/11/2026, les deux fichiers sont identiques) | `pince_bras_libre_+Y.stl`, `pince_bras_libre_-Y.stl` |
| Doigts (trou arrière déplacé) — **nouveaux en V3** | `pince_doigt_+Y.stl`, `pince_doigt_-Y.stl` |
| Bouchons du trou arrière des doigts (× 2, inchangés) | `pince_bouchon_doigt.stl` |
| Variantes à insert (inserts M3 × 5 × 4 : Ø ext. 5, 4 mm de long, trou de 4,3) | `pince_bouchon_doigt_insert.stl` (× 2, insert posé au fer dans le bouchon, puis bouchon dans le doigt actuel), ou doigts `pince_doigt_+Y_insert.stl` / `_-Y_insert.stl` (insert directement dans le trou arrière) : filetage en laiton au lieu du plastique |

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
| Roulements 623ZZ (commandés) | 7 | engrenage B (1), bras libres (2 chacun, un à chaque bout), doigts (1 chacun, trou avant) |
| Inserts M3 à chaud | 5 | tous dans la base : piliers de la bride (2), poteau de l'engrenage B, poteaux des 2 bras libres |
| Vis M3 × 10 | 5 | bride (2), engrenage B (1), pivots des bras libres (2) |
| Vis M3 × 8 | 2 | bout des bras libres : à travers le roulement du bras, vissées dans le bouchon du doigt (pas de M3 × 10 : elle dépasserait) |
| Vis M3 × 16 (14 à 20 conviennent) + écrou frein | 2 | doigt sur le bras de l'engrenage |
| Rondelles M3 (DIN 125, 0,5 mm) | 4 | entre doigt et bras d'engrenage (2), entre bras libre et doigt (2) |
| Vis M2,5 × 8 (ou les vis fournies avec le servo, avec la variante d'engrenage A à leur longueur) | 4 | engrenage A sur le palonnier |
| Les 2 vis M3 × 30 de l'entretoise du bout de l'avant-bras | (déjà là) | traversent le manchon de la pince |

Correction du 11/11/2026 : au bout des bras libres, un écrou sous le doigt aurait tapé dans le bras de
l'engrenage pince presque fermée. Une vis M3 × 8 s'y visse maintenant directement dans le bras (trou de 2,8) ; une M3 × 10 seule arriverait au ras du bras
de l'engrenage. Vérifié par `verifier_visserie.py` (vis, écrous, rondelles sur toute la course : aucun contact, 2 mm de marge).
Les passages de tête au-dessus des roulements font 6,5 mm : la vis n'appuie que sur la bague intérieure, sans rondelle.
**Pièces à réimprimer si elles l'ont déjà été : les 2 bras libres et l'engrenage B.**

Correction du 13/11/2026 (essai réel) : au bout des bras libres, la vis vissée dans le bras n'entrait que de 2,5 mm
dans le roulement arrière du doigt ; en serrant un objet, le doigt basculait, soulevait le bras, la vis sortait et la
mâchoire tournait (la pince s'ouvrait). Maintenant le roulement est dans le **bras** (un à chaque bout) et la vis M3 × 8
le **serre** sur un **bouchon imprimé** placé dans le trou arrière du doigt : même principe que les pivots.
**À réimprimer : les 2 bras libres + 2 bouchons** (les doigts restent bons).

## Montage

**Plan illustré, une page par étape : `sortie/plan_montage.pdf`** (aussi en images `sortie/plan_montage_00.png` à `_09.png`),
refait par `python plan_montage.py` après `generer_pince.py`. Il remplace l'ancienne liste d'étapes.
Pour vérifier le montage : `sortie/vue_dessus_montee.png` (vue de dessus, quel bras va dans quel trou du doigt ; `vue_dessus.py`).

**Premier essai motorisé** : `bras/tester_pince.bat` (voir `bras/LISEZ-MOI.md`) : ouvrir, fermer, serrer avec une force limitée.

## Limites à connaître

- **Poids au bout du bras** : pince 143 g + un gobelet moyen plein (300 g environ) = plus de 400 g à
  25 cm de l'épaule. C'est beaucoup pour un STS3215 en continu : servir d'abord des **gobelets vides ou
  petits**, et prévoir peut-être un servo plus fort pour l'épaule.
- **Force de serrage** : le servo peut écraser un gobelet en carton. Il faudra limiter son couple
  (réglage dans le servo) avant les essais avec de vrais gobelets.
- Le sens « ouvrir » (vers la butée min ou max) se vérifie au premier essai.
