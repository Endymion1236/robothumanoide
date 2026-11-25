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

**24/11/2026 : contrôle au niveau, articulation par articulation** (idée de Nicolas ; téléphone posé contre le flanc de chaque
pièce, bras au repos, vu de derrière). Après le nouveau berceau du coude : socle −1,4°, épaule +0,4°, coude +0,8°, flexion +1,2°,
pince +2,4°. Les écarts qui comptent : **épaule 1,8°** (encore l'ancien berceau à parois basses, à remplacer), coude 0,4° et
flexion 0,4° (bons), **rotation du poignet 1,2°** (le servo n° 5 ne bouge pas dans son support, barre serrée : Nicolas soupçonne
le manchon désaxé sur la fourche). **Décision de Nicolas : pour le deuxième bras, contrôle au niveau à chaque étape du montage.**

**25/11/2026 : les 2 servos Feetech STS3095 sont arrivés** (photos de Nicolas). Vu sur les photos, rien de mesuré : boîtier en
métal noir et rouge, nettement plus gros que le STS3215 ; un palonnier en aluminium de CHAQUE côté, avec 8 trous taraudés sur un
cercle et une vis centrale cruciforme ; une prise 3 broches marquée « SVG » sur chacun des deux petits côtés ; 4 vis à tête creuse
aux coins du couvercle. Ils n'entrent sûrement pas dans les berceaux actuels : épaule et coude seront à redessiner.
Avant tout dessin, demander : boîtier (L × l × h), position de l'axe, palonniers (diamètre, épaisseur, dépassement, cercle et
filetage des 8 trous), distance entre les deux faces de palonnier, vis fournies, tension sur l'étiquette ou la boîte.
Avant tout branchement : vérifier le 12 V, et les brancher SEULS pour changer leur numéro (neufs, ils portent sans doute le n° 1,
celui du socle).
Étiquette de la boîte (photo du 25/11/2026) : **STS3095, code ST-3095-C002, taille 30 × 65 × 48 mm, 95 kg·cm et 0,322 s/60° à 12 V**
→ c'est bien la version 12 V ; trois fois le couple d'un STS3215 (30 kg·cm), un peu plus lent. Ces trois cotes sont celles de la
boîte, pas des mesures : le détail (axe, palonniers, trous) reste à mesurer, ainsi que la masse (le servo du coude est porté par
l'épaule). Attention à la force : limiter le couple dans le programme et régler les butées AVANT de monter quoi que ce soit.
Fiches des revendeurs pour le STS3095-C002 (lues le 25/11/2026, PAS des mesures) : **masse 194,5 g** (un STS3215 : 55 g),
**courant de blocage 9,8 A à 12 V**, couple nominal 22,5 kg·cm, 31 tr/min à vide, cannelure 15 dents Ø 7,6. Conséquences à garder
en tête : au coude, 140 g de plus portés par l'épaule ; le bloc 12 V de 5 A ne suffit plus, et même 10 A ne couvre pas deux
servos bloqués à fond → limiter le couple dans le programme. Cotes des palonniers et des trous : toujours inconnues (le lien du
QR code de la boîte n'est pas joignable depuis la session).

**25/11/2026 : les SCS0009 sont arrivés** (photo d'un sachet). Vu, rien de mesuré : le servo a UN SEUL câble, fixe, à 3 fils
(noir, rouge, blanc) terminé par une fiche blanche à 3 broches ; chaque sachet contient aussi une **petite carte de dérivation à
3 prises** (pour chaîner des servos qui n'ont qu'une prise), un câble à deux fiches, des palonniers en plastique blanc (bras
simple, double, croix) et des vis. À vérifier avec Nicolas avant tout branchement : la fiche entre-t-elle dans la carte Waveshare
(même pas que les STS3215 ?), a-t-il la deuxième carte, tension d'entrée admise par cette carte (à lire dessus ou sur sa notice).
Mesures à demander avant de dessiner poulie et support : boîtier, axe, palonniers, vis, longueur du câble.
Nicolas a bien une **deuxième carte Waveshare** (dit le 25/11/2026) : elle sera la carte 6 V de la main.

**Décision du 25/11/2026 (Nicolas n'a que 2 STS3095) : un STS3095 à l'ÉPAULE de chaque bras, les coudes gardent leur STS3215.**
Seul le berceau de l'épaule est à redessiner. Calcul (masses des pièces, non mesuré) : coude à environ 35 % du couple de blocage
avant-bras à l'horizontale et à vide, 40 % avec un objet léger, près de 80 % avec une canette de 350 g → pour les canettes,
prévoir plus tard un ressort au coude, ou deux STS3095 de plus. Le ressort d'épaule deviendra sans doute inutile (à vérifier à
l'essai) ; il imposait le repos à 80°.
**Mesures du STS3095 par Nicolas (25/11/2026, en cours)** : boîtier **65 de long**, face du logo **30 de large**, **47,8 entre les
deux faces des palonniers** (mesuré au milieu de la face ; **45,8 du côté des vis**, étendue de ce décrochement à préciser). Les palonniers sont donc sur les deux faces de 30 × 65. Suite à mesurer : B à E.
Suite des mesures du STS3095 (Nicolas, 25/11/2026) : axe à **47,1 du bout opposé** → à 17,9 du bout côté palonnier (interprétation,
à confirmer) ; axe **centré en largeur** (14,3 et 14,4 aux bords, mesure difficile) ; palonnier **Ø 29,6 × 3,8**, dessus du disque à
**7,3 de la face du boîtier** ; **68,3 au total par-dessus les têtes des vis centrales** ; moyeu central **Ø 13,8**, qui dépasse du
disque de **1 mm côté logo, 0,5 de l'autre** ; trous du palonnier : bords extérieurs de deux trous opposés à 26,6, trou Ø 2,7
→ **cercle des 8 trous ≈ Ø 23,9** (calcul) ; filetage des trous non vérifié. Vis fournies : **8 de Ø 2,6 × 9 sous tête** et
**6 de Ø 2,1 × 4,3 sous tête**. Restent : épaisseur par-dessus les deux disques (sans les têtes de vis), filetage et profondeur
des trous du palonnier, étendue du décrochement à 45,8, trous de fixation du boîtier, poids, câble.
Encore (Nicolas, 25/11/2026) : le décrochement à 45,8 n'est **qu'aux 4 coins, sur des carrés de 6,6 × 6,6** (logements des têtes de
vis du couvercle) ; **câble fourni : 15 cm** ; **prises SVG sur les deux faces à bande rouge**, vers le bas, au milieu, à **22 mm du
bout côté palonnier et 29,8 du bout opposé** (donc environ 13 mm de long, par différence) : le berceau doit laisser ces deux
zones libres pour les fiches. Manquent encore : épaisseur par-dessus les disques, filetage et profondeur des trous du palonnier,
trous de fixation du boîtier, poids, confirmation du 47,1 (bout opposé au palonnier ?).
**65 mm par-dessus les deux disques** (Nicolas, 25/11/2026). Ne colle pas avec 47,8 + 2 × 7,3 = 62,4 : chaque disque dépasserait
en moyenne de 8,6 et non de 7,3. Dépassement à remesurer de CHAQUE côté avant de dessiner.
**Retenu pour le dessin : 61,4 mm entre les faces extérieures des deux disques** (Nicolas, sans compter le moyeu central), soit
6,8 de dépassement par côté en moyenne (7,3 mesuré d'un côté : écart de mesure ou disques un peu dissymétriques, ±0,5). Le 65
mesuré avant comptait le moyeu. Au dessin : une fourche qui serre les deux disques a 61,4 + jeu à l'intérieur ; creux de Ø 16 au
moins et 3,5 mm de profondeur au moins en face du moyeu et de la tête de vis (68,3 hors tout par-dessus les vis).
**Trous du palonnier : filetés sur toute l'épaisseur du disque (3,8 mm), traversants ; les vis fournies Ø 2,6 × 9 s'y vissent**
(Nicolas, 25/11/2026). Conséquence pour le dessin : une vis de 9 mm vissée à fond dépasse SOUS le disque ; entre le dessous du
disque et le boîtier il ne reste qu'environ 3 mm (6,8 − 3,8, par le calcul) → il faut au moins 3 mm de plastique sous la tête
(et au plus 5,2 pour garder tout le filetage) : viser 4 mm, pointe à 1,2 sous le disque. À vérifier : M2,5 du coffret de Nicolas
dans ces trous ? Jamais faire tourner le palonnier avec une vis de 9 mm vissée seule.
Fixations du boîtier (Nicolas, 25/11/2026) : **3 trous côté logo, 4 sur la face d'en face, les vis fournies Ø 2,1 × 4,3 s'y vissent**
(M2 probablement). Côté logo, vu sur la photo : 2 trous sous l'étiquette, à gauche et à droite, et 1 au milieu de la languette du
bout opposé au palonnier, entre les deux vis de coin ; Nicolas : « les 3 à 10,7 du centre des vis de coin » (sens exact à préciser).
La photo confirme que l'axe est à **17,9 du bout côté palonnier** (47,1 jusqu'au bout à languette). Position précise de chaque trou
de fixation, poids et côté des prises SVG : encore à demander.
Lecture des photos avec réglet (25/11/2026), à prendre avec prudence (perspective) : sur la face du logo, les 2 trous sous
l'étiquette sont dans l'alignement des vis de coin, à environ 3,3 mm des bords (écartement ≈ 23,4, comme les vis de coin) et à
10,7 au-dessus d'elles → **à ≈ 14 mm du bout à languette, ≈ 33 mm de l'axe** ; 3,3 + 10,7 + 33,1 = 47,1 : cohérent avec la mesure
axe → bout. Trou de la languette : centré, près du bout (position exacte inconnue ; le « 10,7 des deux vis » est impossible
géométriquement). Au dessin : trous OBLONGS dans le plastique, servo tenu d'abord par la forme du boîtier.
Contrôle demandé : distance du bord du disque au bout du boîtier côté palonnier (≈ 3,1 attendu si l'axe est bien à 17,9).
Photos du côté à bande rouge et du bout (25/11/2026) : elles **confirment l'axe à ≈ 17,5-18 du bout côté palonnier** et le bord du
disque à ≈ 3 mm du bout (le disque ne dépasse pas) ; la **prise SVG est collée contre la face OPPOSÉE au logo** (≈ 3 mm de son
bord), de ≈ 22 à 35 mm du bout côté palonnier ; les décrochements des coins (têtes de vis) sont du côté du LOGO. Restent : photo
de la face à 4 trous avec réglet, et poids.
**Poids mesuré : 199 g** (Nicolas, 25/11/2026 ; fiches : 194,5). Face opposée au logo (photo avec réglet, perspective forte) :
je vois **6 petits trous**, par paires à ≈ 2,3 mm des bords (écartement ≈ 25) : une paire aux coins côté palonnier, une juste
sous le disque, une près du bout à languette ; Nicolas en avait compté 4. Distances au bout à languette demandées.
Photo de face avec réglet (25/11/2026, nette) : face opposée au logo, **6 trous par paires à ≈ 2,5 des bords : ≈ 3, ≈ 39 et ≈ 62,5 mm
du bout côté palonnier** (± 1 mm) ; la paire à 3 mm est sous le disque. Plan coté de synthèse à faire valider par Nicolas :
`epaule/sts3095/sortie/plan_sts3095.png` (`plan_sts3095.py`). Prochaine étape après validation : berceau d'épaule pour le STS3095.
**Validé par Nicolas (25/11/2026)** : 3 trous côté logo, 6 face opposée, coins à vis côté logo (prise SVG : à confirmer).
**Correction de la décision « seul le berceau change »** : la fourche du haut du bras doit passer de ≈ 45 à 61,4 mm entre disques
→ berceau ET haut du bras (deux moitiés, vissés par les 8 trous M2,6 de chaque disque) sont à refaire, et le **mât du ressort
du bâti gêne** (face intérieure à Y = 72 dans `generer_epaule.py`, la fourche élargie y arriverait). Choix demandé à Nicolas :
scier le mât (conseillé, ressort sans doute inutile) ou réimprimer le bâti. Le plan du bras se décalera d'environ 1 cm de côté :
mettre à jour `DECALAGE_BRAS` (bras/geometrie.py) et refaire la correction de visée.
**SCS0009, lecture des photos avec réglet (25/11/2026, ± 1 mm, photos de biais : À CONFIRMER au pied à coulisse)** : boîtier ≈ 23 ×
12,5, hauteur ≈ 19 sans le bossage rond (≈ 23 avec, ≈ 26 avec la cannelure dorée de ≈ 3 mm) ; pattes ≈ 32 de bout en bout, dessus
des pattes ≈ 4 sous le dessus du boîtier ; axe ≈ 6 du bout le plus proche ; entraxe des trous des pattes entre 27 et 29 (photo trop
de biais). Sachet : palonnier rond, en croix, à un bras, 2 vis. La fiche du câble paraît PLUS PETITE que celle des STS3215 :
vérifier qu'elle entre dans la carte Waveshare avant tout.
Palonniers du SCS0009 (photos sous le réglet, 25/11/2026, ± 0,5 mm) : bras double ≈ 31 de bout en bout, bras simple ≈ 16 du centre au
bout, en croix ≈ 2 × 16 ; trous Ø ≈ 1 sur chaque bras à ≈ 6,5 / 9,3 / 11,7 / 13,8 mm du centre (pas ≈ 2,4). Piste retenue pour la
poulie d'un doigt : se visser sur le PALONNIER ROND du sachet (pas d'impression d'une cannelure aussi fine) → mesurer ce palonnier.
**SCS0009 au pied à coulisse (Nicolas, 25/11/2026)** : boîtier **23,1 × 12,1** ; **20,6** du dessous au dessus de la partie ronde
(interprétation, sans la cannelure, à confirmer) ; partie ronde autour de l'axe : **Ø 11,7**, dépassant de **3,7** (interprétation) →
dessus du boîtier ≈ 16,9 du dessous ; **palonnier rond Ø 17,5** ; 2 vis **Ø 1,3 × 6,1** dans le sachet. **La fiche est de la même
taille que celle des STS3215** : elle entre dans la carte Waveshare. Manquent : pattes (longueur, épaisseur, hauteur, trous),
axe → bout, cannelure (Ø, dépassement), palonnier rond (épaisseur, moyeu, trous).
SCS0009, suite (Nicolas, 25/11/2026) : **pattes 32,4 de bout en bout**, **trous des pattes Ø 2,1**, entraxe ≈ 28 (photo) ; axe ≈ 5 mm du
bout le plus proche (photo) ; deux mesures à faire préciser : « 13 » et « 10,8 ». Carte de dérivation **SCS-Y4-2012** : 3 prises en
parallèle (S, C+, C−), plus 2 pastilles C+ / C− pour souder une arrivée de courant (ne pas s'en servir).
