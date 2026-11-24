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

**21/11/2026 : les trous du manchon du support de rotation étaient décalés de 1,1 mm de côté** (Nicolas : trou à 5,9 mm du
bord sur l'avant-bras, à 4,8 mm sur le support). Cause : ce manchon n'avait que 3 faces et glissait de côté. Leçon : un manchon
sur l'avant-bras se fait FERMÉ sur 4 faces, comme celui de la pince, qui tombait juste. La distance des vis au bout de
l'avant-bras n'a toujours pas été mesurée (7,5 mm au dessin).

**Alimentation : bloc 12 V de 5 A** (dit par Nicolas le 21/11/2026). Creux de tension à 11,4 V déjà relevés avec 5 servos STS3215 :
juste pour le bras complet, insuffisant à prévoir avec les deux servos 3095 (courant à lire sur leur fiche à réception).

**21/11/2026 : 5 petits servos Feetech SCS0009 commandés pour la main** (un par doigt). Ils sont en **6 V** : jamais sur le bus
12 V ; prévoir la deuxième carte Waveshare et une alimentation 6 V à part. Rien n'est mesuré : à réception, demander boîtier,
axe, palonnier, vis, câble et connecteur AVANT de dessiner poulie et support. Leur langage de commande (série SCS) n'est pas
celui des STS3215 : `bras/servos.py` ne les pilotera pas tel quel, à vérifier sur leur fiche.

**24/11/2026 : Nicolas a commandé un Hobbywing UBEC 10A (2-6S, sorties 6 / 7,4 / 8,4 V, avec interrupteur)** pour faire le 6 V de
la main à partir du 12 V (le Pololu était trop cher). À réception, AVANT tout servo : lire la notice et la position du cavalier
(6 V attendu sans cavalier, non vérifié sur sa version), mesurer la sortie au multimètre, regarder ce qu'il y a au bout des fils.
Il tire sur le bloc 12 V : avec le bras, il faudra le bloc de 10 A. Deuxième carte Waveshare et bornier de partage du 12 V :
Nicolas n'a pas dit s'il les a.
