# Robot humanoïde de Nicolas — consignes pour toute session

Nicolas gère un centre équestre et débute en électronique : réponses en français, simples, pas à pas.
La feuille de route et l'état du projet sont dans `README.md` ; chaque dossier a son `LISEZ-MOI.md`.

## Règle de conception (demande de Nicolas, 19/11/2026)

**Avant de modéliser une pièce, demander les mesures de tout élément dont la cote n'est pas déjà mesurée et notée** :
longueur des vis (sous tête), diamètre et longueur des inserts, roulements, épaisseur d'une planche, longueur des câbles,
servo ou composant jamais mesuré. Ne pas supposer qu'une vis « fournie » a la bonne longueur.
Exemples de ce que cette règle aurait évité : vis M2,5 du servo trop courtes pour l'engrenage A puis pour le moyeu du
socle (elles font 5,3 mm sous tête), inserts trop longs pour les doigts, câble de la pince trop court.

Mesures déjà connues : voir « Repères sur le servo » et « Matériel » dans `README.md` ; vis M2,5 fournies avec les
servos : 5,3 mm sous tête ; roulements 6807 : 47 × 35 × 6,8 ; 623 : 10 × 3 × 4 (cotes standard, non mesurées).
Mesuré le 19/11/2026 : **inserts M3 de Nicolas : Ø 4,7 × 3,8 mm de haut** (pas d'inserts longs : ne pas compter sur plus de
3,8 mm de filet) ; **câble de servo : 152 mm** d'une fiche à l'autre ; vis M3 : coffret jusqu'à M3 × 30 et M3 × 35 à vérifier,
Nicolas dit n'avoir que des **M3 × 30** au plus long ; tapis antidérapant pour les mâchoires : **2 mm**.
Objets à saisir (pour la pince V4) : gobelet de **70 mm en haut, 53 mm en bas** ; téléphone de **80 × 157 mm** (épaisseur à demander).

## Autres habitudes du projet

- Toute pièce est vérifiée par le calcul avant d'être proposée (collisions sur toute la course, visserie comprise) et
  annoncée comme « prototype » tant qu'elle n'a pas été montée ; tout programme est essayé sur un servo simulé et
  annoncé comme tel.
- Sécurité des servos : butées réglées avant de monter quoi que ce soit, jamais brancher ou débrancher sous tension,
  un bras qui porte du poids est RETENU, jamais lâché, par les sécurités.
- Les clés d'API et les données personnelles (visages, souvenirs) restent sur le PC de Nicolas, jamais dans le dépôt.
- Un commit par sujet, en français : le problème tel que Nicolas l'a vu, puis ce qui change.

Dit par Nicolas le 20/11/2026 : il a **9 câbles de servo de 90 cm** (confirmé ; les câbles fournis avec les servos font 152 mm)
et un tournevis fin. Ses mâchoires de pince V3 sont **d'un seul bloc** avec leur plaque (pas la version à inserts).

**21/11/2026 : Nicolas a commandé 2 servos « 3095 » en version 12 V** (pour l'épaule et le coude, qui limitent le bras avec le
poignet complet). Rien n'est mesuré : à réception, demander boîtier (L × l × h), position de l'axe, palonnier (diamètre,
hauteur, cercle et taille des trous), second disque, vis fournies (longueur sous tête), AVANT de dire qu'ils entrent dans
les berceaux actuels. Vérifier aussi sur l'étiquette que c'est bien du 12 V avant de les brancher sur le bus.
