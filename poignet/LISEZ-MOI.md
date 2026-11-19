# Poignet : rotation de la pince (servo n° 5)

**Prototype dessiné le 19/11/2026 : vérifié par le calcul, rien n'est imprimé ni monté.**

Un STS3215 au bout de l'avant-bras, dans l'axe du bras ; la pince est vissée sur son palonnier et tourne sur
elle-même de −90° à +90°. Le bras s'allonge de **48,7 mm** et s'alourdit de **90 g** au bout (servo compris).

## Pièces à imprimer (`sortie/`)

| Fichier | Rôle | Pose |
|---|---|---|
| `poignet_support.stl` (42 g) | s'enfile sur le bout de l'avant-bras à la place de la pince ; le servo y glisse par le haut | telle quelle, sans support |
| `poignet_barre.stl` (3 g) | ferme le haut du support, au-dessus du servo | à plat |
| `poignet_base_pince.stl` (71 g) | remplace la base de la pince : plus de manchon, un moyeu rond vissé sur le palonnier | à plat sur sa plaque |

Tout le reste de la pince V4 est gardé (bride, servo, 2 plaques, 2 mâchoires).

## Visserie

- 2 vis M3 × 30 : celles qui tenaient la pince sur l'avant-bras ;
- 2 vis M3 × 10 et 2 inserts M3 (Ø 4,7 × 3,8) pour la barre ;
- les 4 vis M2,5 du servo n° 5 (5,3 mm sous tête) : elles prennent 2,5 mm dans le palonnier.

## Ce que le calcul a vérifié (`generer_poignet.py`)

- le servo glisse dans le support sans rien toucher, et aucune pièce ne le touche une fois en place ;
- la pince tourne de −90° à +90° sans toucher le support, pince ouverte, au milieu ou fermée ;
- le tournevis atteint les 4 vis du palonnier par l'avant de la pince (servo de la pince retiré, plaque mobile non montée).

## Ce qui reste à vérifier en vrai

- **Tournevis** : 2 des 4 vis du palonnier sont au fond d'un passage de 5,4 mm de large et d'environ 55 mm de long
  (elles tombent à côté du logement du servo de la pince). Il faut un tournevis fin à tige longue.
- **Câble coude → poignet** : 152 mm. Le servo du poignet est plus près du coude que ne l'était celui de la pince,
  mais la longueur n'a pas été mesurée sur le bras monté.
- **Câble poignet → pince** : il doit garder une boucle pour laisser tourner la pince de ± 90°.
- La pince ne tient que par les 4 vis du palonnier (comme sur le SO-101), pas des deux côtés du servo.
- Programme d'essai du servo n° 5 : à écrire.
