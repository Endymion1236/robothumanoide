# La main à doigts — doigt d'essai (21/11/2026)

**Prototype : vérifié par le calcul, rien n'est imprimé.** Aperçu : `sortie/apercu_doigt.png`.

Mécanisme retenu le 18/11/2026 : **deux fils par doigt**, un qui ferme, un qui ouvre, sans élastique ni ressort.
Première étape, comme prévu dans la feuille de route : **un seul doigt, essayé à la main, sans servo**. Il sert à valider
les charnières, les butées et le passage des fils. La poulie et le support du petit servo ne sont PAS dessinés : le servo
n'est pas encore reçu ni mesuré.

## Les pièces (`sortie/`)

| Fichier | Rôle |
|---|---|
| `doigt_base.stl` | base du doigt, 2 pattes pour la visser sur une planchette |
| `doigt_phalange_1.stl`, `_2`, `_3` | les trois phalanges (30, 22 et 18 mm d'axe en axe) |

Doigt de 73 mm, 14 × 14 mm de section, 23 g. Les phalanges s'impriment couchées sur le flanc, sans support.

## Ce qu'il faut en plus

- 3 morceaux de **filament de 1,75 mm**, de 17 mm de long : ce sont les axes. Ils entrent sans forcer ; on les retient en
  écrasant leurs deux bouts avec la panne chaude du fer à souder (une petite tête de chaque côté) ;
- environ 40 cm de **fil de pêche tressé** (un seul brin : il descend par le canal du dessous, se noue au bout du doigt
  dans le puits vertical, et revient par le canal du dessus) ;
- 2 vis pour fixer la base sur une planchette.

## Plan de montage du doigt (26/11/2026)

`sortie/plan_montage_phalanges.pdf` (`plan_montage_phalanges.py`), 7 étapes illustrées : reconnaître les 4 pièces, le sens de
chacune (languette vers la base, pont de la fourche côté DOS, le doigt plie vers la PAUME), emboîter et vérifier une
articulation sans axe, poser les axes en filament (17 mm, une tête écrasée au fer de chaque côté), passer les fils.
**Les fils : deux brins de 30 cm**, un par canal, entrés par l'arrière de la base ; ils ressortent par le puits de la phalange 3,
côté paume, où on les noue ensemble ; le nœud rentre dans le puits et y est collé (une goutte de cyano). Sans colle, le nœud
aurait 7 mm de jeu dans le puits. Fil du dessous = ferme, fil du dessus = ouvre. Prototype : jamais monté.

## Ce que le calcul a vérifié (`generer_doigt.py`)

- chaque charnière bute doigt tendu (à −2° près) et plie jusqu'à 90° ;
- plié à 85° par charnière, aucune pièce ne touche une pièce non voisine ;
- il faut tirer **16 mm** de fil pour plier le doigt à fond (bras de levier du fil : 3,6 mm).

## Ce que l'essai à la main doit dire

- les charnières tournent-elles librement, sans jeu excessif ? (trous de 2,15 et 2,5 mm depuis le 22/11/2026 : à 1,9 et 2,3 le filament n'entrait presque pas) ;
- le fil coulisse-t-il sans accrocher aux sorties des canaux ?
- le doigt se ferme-t-il en entier, et dans quel ordre plient les phalanges ?
- faut-il beaucoup de force sur le fil ?

## Ensuite

Poulie et support du petit servo (après mesure du servo : boîtier, axe, palonnier, vis), puis la paume et les 5 doigts.
**5 Feetech SCS0009 commandés le 21/11/2026** (un par doigt). Ils sont en **6 V** : jamais sur le bus 12 V des autres servos ;
il leur faut leur propre carte (la deuxième Waveshare) et une alimentation 6 V. Leur programme sera différent de `bras/servos.py`.

## Banc d'essai du doigt motorisé (25/11/2026)

**Prototype : vérifié par le calcul, rien n'est imprimé ni monté.** `generer_banc_doigt.py`, aperçu `sortie/apercu_banc_doigt.png`.
Un SCS0009 tire le doigt d'essai par ses deux fils. Le servo est couché, axe horizontal ; sa poulie à deux gorges (fond Ø 8) tombe
juste dans le plan des deux canaux du doigt : le fil du dessous (paume) ferme, celui du dessus ouvre, enroulés en sens inverse.

| Fichier (`sortie/`) | Pièce | Environ |
|---|---|---|
| `banc_doigt_platine.stl` | platine, montant, cloison à fenêtre pour le servo | 25 g |
| `banc_doigt_console.stl` | console qui porte la base du doigt au-dessus du vide | 7 g |
| `banc_doigt_etrier.stl` | étrier qui plaque le servo contre la cloison | 3 g |
| `banc_doigt_poulie.stl` | poulie, coiffe le palonnier ROND | 2,5 g |
| `banc_doigt_rondelles.stl` | 2 rondelles de 2 mm | |

Impression : PETG, 4 périmètres, 40 %, sans supports, pièces déjà posées (poulie creux en dessous : le plafond du creux se fait en pont).

Visserie : 6 vis M3 × 10 et 6 inserts M3 (base du doigt sur la console, console sur le montant, étrier par l'avant de la cloison) ;
1 vis fournie Ø 1,3 × 6,1 pour la poulie ; la vis centrale du palonnier, posée AVANT la poulie.

**Le banc se pose au bord de la table, la console et le doigt dans le vide** (serre-joint sur la platine) : plié à fond, le doigt
s'enroule et repasse 13 mm sous ses axes, jusqu'à 40 mm en arrière de sa charnière.

Ce que le calcul a vérifié : la poulie tourne sur 360° sans rien toucher ; le servo entre dans la fenêtre, ses pattes s'appuient sur
la cloison ; le doigt, sur 54 positions de tendu à plié à fond, ne touche ni le banc ni les vis de sa base ; les fils vont droit dans
leurs canaux (2,3° d'écart). Il faut tourner le servo de **221°** pour plier le doigt à fond (il en fait environ 300). Force dans le fil :
environ 18 N en usage, 54 N au blocage (couple de la fiche revendeur, 2,3 kg·cm à 6 V).

**Poulie corrigée le 26/11/2026** : les deux petits trous d'ancrage des fils (Ø 1,2, fermés) ne se formaient pas à l'impression.
Ils sont remplacés par deux **fentes ouvertes** de 1,4 mm, une par gorge, de part et d'autre du tambour : le fil s'y glisse par le
côté et se noue sur le dessus du tambour. Réimprimer `banc_doigt_poulie.stl`.

**À vérifier par Nicolas AVANT d'imprimer** :
1. une vis fournie (Ø 1,3) se visse-t-elle dans un des deux trous les plus écartés du palonnier rond (trous de 0,7) ? Sinon, les
   agrandir avec une aiguille chauffée ou un foret de 1 mm ;
2. palonnier rond posé sur le servo : est-ce bien sa face PLATE en haut, au ras du bout de l'axe doré (moyeu côté servo) ?

Supposés au dessin (non mesurés) : dessus du boîtier à 19,0 du dessous ; moyeu du palonnier côté servo.
Montage des fils et programme d'essai : à venir (le servo parle le protocole SCS, pas celui du bras).

### Plan de montage et programme (25/11/2026)

- **Plan de montage** : `sortie/plan_montage_doigt.pdf` (une page des pièces + 7 étapes : servo préparé seul, inserts, console et
  doigt, servo et étrier, palonnier et poulie, les deux fils, essai).
- **Programme** : `tester_doigt.bat` (utilise l'installation du bras, `bras\installer.bat`). **Essayé sur un servo simulé seulement.**
  `doigt_servo.py` parle le protocole SCS (0 à 1023 pour 300°) ; il **refuse toute carte dont les servos reçoivent plus de 8 V** (la
  carte du bras est donc écartée d'office) et relâche un servo qui annonce plus de 8 V. Pendant un mouvement, un doigt bloqué
  s'arrête et tient sa place.
  Commandes : `i` état · `n 22` changer le numéro · `v` ± 20° à vide · `m` milieu (pour monter les fils) · `c` apprendre la course
  (le servo cherche lui-même les deux butées du doigt, doucement) · `t` / `p` tendu / plié · `a 50` · `+` / `-` · `r` relâcher · `q`.
  Course apprise gardée dans `main/doigts.json` (sur le PC, pas dans le dépôt).
- **Numéros des servos de la main** : pouce 21, index 22, majeur 23, annulaire 24, auriculaire 25 (le doigt d'essai = 22).

### Alimentation de la carte de la main

La deuxième carte Waveshare reçoit le **6 V de l'UBEC** (cavalier enlevé, mesuré au multimètre avant tout servo) ; pour un premier
essai d'un seul doigt, le petit boîtier 12 V → 5 V 3 A convient (servo moins fort à 5 V). Le servo est alimenté PAR la carte, par son
câble. **À vérifier** : la tension d'entrée minimale imprimée sur la carte Waveshare (si elle demande 9 V ou plus, il faudra un autre
montage) et la prise au bout du câble de sortie du boîtier 5 V.
