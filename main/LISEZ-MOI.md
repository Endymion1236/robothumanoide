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
