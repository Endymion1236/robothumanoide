# Épaule du bras (V1, 14/11/2026)

**Prototype : aucune validation physique.** Dessinée et contrôlée par le calcul, jamais imprimée ni montée.

## Le principe : on reprend ce qui marche au coude

- Le servo d'épaule est couché dans un **berceau** identique à celui du coude, vissé sur le mur du **bâti**.
- Le **haut du bras** est une fourche comme l'avant-bras (deux moitiés vissées sur les deux disques du servo),
  prolongée par une **platine** où se visse le berceau du coude. Axe d'épaule → axe du coude : 120 mm.
- Un **ressort de traction** relie une vis du haut du bras à l'un des **12 trous du mât** du bâti. Il porte une
  bonne partie du poids du bras.
- Axe de l'épaule à 95 mm au-dessus du pied. Course prévue : de **−30°** (sous l'horizontale) à **+90°** (vertical).
- L'avant-bras et la pince sont décalés de 54 mm sur le côté du haut du bras : ils passent à côté, jamais dedans.

![aperçu](sortie/apercu_epaule.png)

## Le ressort

**Ressort de traction 70 × 10 × 1,2 mm** (longueur 70 crochets compris, diamètre extérieur 10, fil 1,2).
Le 60 × 10 × 1,2 convient aussi. Pas le 50 × 12 × 1,5 (trop raide).

Pesée du 14/11/2026 : coude + avant-bras + pince sans doigts ni bras libres = 281 g, soit environ **350 g**
pince complète, et 0,98 g/cm³ pour les pièces imprimées à 40 %. Avec le haut du bras : environ 435 g à lever.

| Effort demandé au servo d'épaule (il tient 10 kg·cm en continu, 30 en blocage) | sans ressort | avec le ressort |
|---|---|---|
| Pince vide, au pire | 8,3 kg·cm | **5,6 kg·cm** |
| Gobelet plein de 300 g, au pire | 18,8 kg·cm | **14 kg·cm** |

À savoir :
- Avec un gobelet **plein**, on reste au-dessus de ce que le servo tient en continu : il le lèvera, mais ne doit pas
  le garder en l'air longtemps. Avec 200 g, on est autour de 10. Un ressort seul ne fait pas mieux sur ce bras ;
  les solutions suivantes : un ressort tiré par un cordon (compensation presque parfaite), ou un deuxième servo.
- Le **coude** a la même limite : avant-bras horizontal avec un gobelet plein, il est à 10,5 kg·cm, sans ressort.
- Au-dessus de 65° environ, le ressort est **détendu** : il pend entre ses deux vis. C'est normal.
- Le calcul dépend du ressort reçu (raideur à ± 20 %) : c'est pour ça qu'il y a 12 trous.
  `python calcul_ressort.py --fil 1.2 --diametre 10 --longueur 70` donne le meilleur trou ; si tu as mesuré le
  ressort (une bouteille d'un litre l'allonge de X mm → raideur = 9,81 / X) :
  `python calcul_ressort.py --longueur 70 --raideur 0.66 --force-max 55`.

## À imprimer (PLA ou PETG, 4 périmètres, 40 %, couches de 0,2, sans support, déjà orientées)

| Pièce | Fichier (`sortie/`) | Nombre | Environ |
|---|---|---|---|
| Bâti (pied, mur, mur arrière, mât) | `epaule_bati.stl` | 1 | 250 g, 129 × 110 × 157 mm : la grosse impression |
| Berceau à inserts | `berceau_a_inserts.stl` | **2** (épaule et coude) | 33 g |
| Bride du berceau | `bride_berceau.stl` | 1 de plus (celle du coude resservira) | 2 g |
| Haut du bras, moitié haute (avec la platine) | `epaule_bras_haut.stl` | 1 | 57 g |
| Haut du bras, moitié basse | `epaule_bras_bas.stl` | 1 | 23 g |

**Pourquoi un nouveau berceau pour le coude aussi :** la fourche passe 2 mm au-dessus du socle du berceau. Avec
l'ancien berceau (trous de 4,5 mm), les têtes de vis seraient sur le socle, sous la fourche. Le berceau à inserts
a des trous de 4 mm pour des inserts M3 : les vis viennent par-derrière, rien ne dépasse. Tout le reste du berceau
est identique à celui que tu connais (servo, bride, câble).

## Visserie

| Quoi | Nombre | Où |
|---|---|---|
| Inserts M3 à chaud | 17 | 4 dans le socle de chaque berceau (au ras du dessous), 2 en haut des colonnes de chaque berceau, 4 dans la moitié basse du bras, 1 dans la moitié haute (vis du ressort) |
| Vis M3 × 10 | 12 | berceau de l'épaule sur le mur (4, par-derrière), berceau du coude sur la platine (4, par-dessous), brides (2 × 2) |
| Vis M3 × 30 | 4 | les deux entretoises du haut du bras (têtes noyées dans la face) |
| Vis M2,5 des disques du servo | 8 | 4 par disque, comme au coude |
| Vis M3 × 16 + rondelles | 2 | accroches du ressort : une dans l'insert du bras, une dans un trou du mât avec un écrou derrière |
| Écrou M3 | 1 | derrière le mât |
| Ressort 70 × 10 × 1,2 | 1 | |
| Vis à bois ou serre-joint | | pour tenir le pied sur la table : indispensable, le bras tendu fait basculer le bâti |

## Montage, dans l'ordre

1. Inserts. Dans le socle des berceaux : **au ras du dessous**, jamais au-dessus du socle.
2. Berceau de l'épaule sur le mur du bâti : 4 vis M3 × 10 par-derrière. Le servo ira vers l'arrière.
3. Berceau du coude sur la platine de la moitié haute : 4 vis M3 × 10 par-dessous. **À faire avant de monter le bras.**
4. Servo d'épaule, fourche, bride : exactement comme au coude (`coude-sts3215/LIRE_AVANT_ESSAI_COUDE_V1_2.md`).
   Les 4 vis M3 × 30 des entretoises entrent par la face extérieure, têtes noyées.
5. Servo du coude et avant-bras dans leur nouveau berceau, comme avant.
6. Servo **non alimenté** : lève et baisse le bras à la main, de −30° à 90°. Rien ne doit toucher.
7. **Le ressort en dernier**, bras tenu vers le haut (à 70°, il se pose sans tirer). Lunettes conseillées : il tire
   jusqu'à 4 kg. Ne lâche pas le bras tant que le servo n'est pas alimenté ou le bras posé.
8. Fixe le pied sur la table avant le premier essai motorisé.

Le programme d'essai de l'épaule (butées, étalonnage bras à l'horizontale) reste à écrire : `bras/test_epaule.py`.

## Vérifications

| Programme | Ce qu'il vérifie | Résultat |
|---|---|---|
| `calcul_ressort.py` | effort du servo sur toute la course, avec et sans ressort, pince vide ou gobelet plein ; meilleur trou | voir plus haut |
| `generer_epaule.py` | pièces fermées, d'un seul bloc, posées à plat pour l'impression | bon |
| `verifier_epaule.py` | haut du bras de −30° à 90° : rien ne touche le bâti ni le berceau (2 mm au plus près, comme au coude) ; avant-bras et pince grande ouverte, coude de −90° à +90° : ne touchent que la table ; le ressort passe partout depuis les 12 trous ; tous les trous sont en face ; longueurs de vis | bon |

Ce que les calculs ne disent pas : la tenue du mât et du mur quand le ressort tire, le frottement, et le vrai
ressort. La fourche autour du servo est celle du coude, validée à ± 90° ; la plaque haute fait 7 mm au lieu de 4.
