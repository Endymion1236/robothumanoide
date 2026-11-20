# Robot humanoïde — projet de Nicolas

Premier objectif : **un petit bras de table** avec un coude en servo Feetech STS3215-C018 et une
**pince** au bout. La main robotique (ESP32, servos MG90S, gestes préenregistrés, puis gant à
capteurs et voix) viendra ensuite.

**Règle de conception (19/11/2026)** : avant de modéliser, demander à Nicolas la mesure de tout élément dont la cote n'est pas
déjà notée (vis, inserts, roulements, planches, câbles). Détail dans `CLAUDE.md`.

## Vision d'ensemble (09/11/2026)

À terme : **deux bras à 6 axes et une tête**, avec **reconnaissance vocale**, une **IA qui répond**
et **reconnaissance d'objets** (« prends la balle rouge »).

| Partie | Matériel | Difficulté |
|---|---|---|
| 2 bras à 6 axes | 12 STS3215 | ⭐⭐ (le même bras, en double, symétrique) |
| Tête qui bouge | 2 servos (tourner, hocher), caméra, micro, haut-parleur | ⭐⭐ |
| Voix + IA qui répond | micro, IA de conversation, voix de synthèse (expérience de la borne du club) | ⭐⭐ |
| Reconnaissance d'objets | caméra + logiciel de détection | ⭐⭐ |
| Attraper l'objet vu | position de l'objet → pince ; piste : **LeRobot** (Hugging Face), fait pour les bras SO-100/SO-101 à servos Feetech : on montre le geste, le robot apprend à le refaire | ⭐⭐⭐⭐ |

**Cerveau** : l'ESP32 ne suffit pas pour la vision et la voix → d'abord l'**ordinateur**, puis un
mini-ordinateur embarqué (**Raspberry Pi 5**, ou **NVIDIA Jetson** pour la vision dans le robot) ;
l'ESP32 reste pour les petites tâches (LED, capteurs, boutons).
**Électricité** : 14 servos → alimentation 12 V de 10 à 15 A, probablement une carte servos par bras.

Ordre prévu :
1. Finir **un bras complet** (en cours).
2. **La tête en parallèle**, sur l'ordinateur : vision et voix, sans moteur, donc sans risque.
3. **Le 2e bras**, copie symétrique du premier.
4. **Tout relier** : la tête trouve l'objet, le bras va le chercher.
5. **Tout embarquer** dans le robot (Raspberry Pi ou Jetson).

## La tête (commencée le 11/11/2026)

**Corps de la tête (16/11/2026) : une tête de poney palomino**, crâne imprimé habillé de tissu, yeux lumineux, oreilles mobiles, cou à 2 STS3215 : voir `tete-poney/LISEZ-MOI.md`.

Dossier `tete/`, voir `tete/LISEZ-MOI.md`. Étape 1 **voir** : `vision.py`, essayé sur le PC (80 objets
fixes, ou sa propre liste avec YOLO-World). Étape 2 **entendre** : `ecouter.py` (Whisper, en français,
sur le PC), **validé le 11/11/2026**. Étape 3 **répondre** : `parler.py`, conversation
à voix haute avec **Câlin** (même personnage que la borne d'accueil, fusion prévue), Claude + voix ElevenLabs,
**validé le 11/11/2026** (puis accéléré). Étape 4 **tout relier** : `robot.py` (caméra en continu, photo envoyée
à Claude sur une question visuelle), à essayer. Étape 5 **mémoire et visages** (outils de Claude, données
biométriques apprises seulement à la demande de la personne, jamais pour un enfant, rangées hors du projet), à essayer.
Puis bouger (2 servos).

## Objectif : Câlin sert le café (11/11/2026)

**But** : « Câlin, un café s'il te plaît » → il reconnaît la personne → prend un gobelet → lance la machine
→ **pose le gobelet couvert devant la personne, sur la table** → « Voilà ton café ! ».

**Sécurité (café brûlant, enfants au club) — conditions pour servir une boisson chaude :**
- gobelets **avec couvercle** ; petits gobelets (expresso, environ 100 g : le bras porte 200 à 300 g au mieux) ;
- **posé sur la table devant la personne, jamais tendu dans les mains, jamais au-dessus de quelqu'un** ;
- trajet **lent, bas et à plat** quand il porte ; **force limitée** dans les servos ;
- la caméra surveille la zone : **une main trop près → arrêt** ; **interrupteur d'arrêt d'urgence** à portée ;
- plus tard, **lidar 2D** autour du bras (voir « Se repérer ») : quelqu'un à moins de 60 cm → ralentit, à moins de 30 cm → arrêt ;
- au club : **boissons froides pour les enfants**, service chaud réservé aux adultes.

**Étapes :**
1. Bras complet (socle, épaule, coude, pince) et gestes enregistrés en montrant le bras à la main.
2. **Station café** : pile de gobelets, machine **déclenchée par l'ESP32 avec un relais** (pas par le bras), zone de service.
3. Premiers essais avec des **gobelets vides**, puis d'eau froide, puis seulement le café.
4. Outil `servir_cafe` pour Câlin (enchaîne les gestes, vérifie que la zone est libre).
5. Plus tard, peut-être : une **base à roulettes** pour servir plus loin que la portée du bras.

## Objectif : trier des objets posés n'importe où (12/11/2026)

« Câlin, range les fruits dans le bac bleu et le reste dans le rouge. » Faisable avec le bras de table
(pas besoin du bras de taille humaine), une fois le bras complet à 6 axes.
- **Caméra fixe au-dessus de la table**, regardant vers le bas (bien plus simple que la caméra de la tête),
  **4 marqueurs ArUco** aux coins : la table étant plate, un pixel donne directement une position X, Y en mm,
  sans caméra de profondeur.
- Détection : YOLO-World (objets nommés) ; la règle de tri dite à voix haute est comprise par Claude, qui
  peut aussi classer un objet sur photo (« ça, c'est un fruit ? »).
- Le bras : cinématique inverse → au-dessus de l'objet, poignet tourné dans le sens de l'objet, descente,
  serrage (l'effort du servo confirme la prise), bac, lâcher ; la caméra vérifie, et il recommence s'il a raté.
- Niveaux : 1) cubes de couleur ; 2) objets nommés ; 3) tri « intelligent » par Claude.
- Limites : objets de 14 à 110 mm de large (pince V2), pas d'objets plats ni collés les uns aux autres au début.
- Variante plus tard : apprentissage par démonstration (**LeRobot**, bras « maître » piloté à la main).

## Se repérer dans l'espace (12/11/2026)

| Besoin | Outil | Quand |
|---|---|---|
| Où est son bras | angles des servos + cinématique (repère : X avant, Y gauche, Z haut, origine au pied du bras) | avec le bras complet |
| Où est la station café, la table | gestes appris à la main, puis **marqueurs ArUco** (webcam actuelle) | station café, tri |
| Objets posés n'importe où | caméra fixe + marqueurs (table plate), plus tard **caméra de profondeur** dans la tête | tri |
| **Quelqu'un s'approche du bras** | **lidar 2D** (LD06 / LD19 ou RPLIDAR C1, quelques dizaines d'euros, sans danger pour les yeux) | **plus tard, avant les essais au club** |
| Le gobelet est-il dans la pince | capteur de distance à un point (VL53L1X) dans la pince | station café |
| Se déplacer dans le club | lidar 2D + base à roulettes (carte des lieux) | bien plus tard |

## Bras de taille humaine (12/11/2026, pour plus tard)

Couple continu à tenir (bras de 60 cm tendu, 300 g dans la pince) : épaule ≈ 65 kg·cm, coude ≈ 25, poignet ≈ 5.
Le chiffre des fiches est le couple **de blocage** ; le couple **continu** est environ 3 fois plus faible.
Choix : poignet et pince en STS3215 ; coude **STS3095-C002 (12 V !** la C001 est en 7,4 V) + réducteur 2:1 ;
épaule STS3095-C002 + réducteur 3:1 à 4:1 + ressort de compensation. Alimentation 12 V ≈ 20 A.
Pour la station café sur un comptoir, un bras de 45 cm suffit (beaucoup moins de couple). Commander un seul
STS3095 d'abord, pour le tester et le mesurer.

## Objectif : le buste humanoïde (15/11/2026, après le 2e bras)

Les deux bras et la tête réunis sur un **buste**, posé sur la banque d'accueil du club : à terme, Câlin.
Taille : bras de 35 cm (celui de table) → buste aux proportions d'un enfant de 8 à 10 ans (moins impressionnant,
plus léger, plus sûr).

**Ce qui est repris** : avant-bras, pince, coude, haut du bras, berceaux des servos, programmes (`bras/`), tête (`tete/`).
**Ce qui change** : le bâti d'essai de l'épaule est remplacé par le torse ; au repos le bras **pend** le long du corps
(le ressort est replacé en conséquence) ; une vraie épaule a 2 ou 3 mouvements (lever devant, écarter, tourner).

**Fabrication : pas tout en impression 3D.**
- **Ossature en profilés aluminium 20 × 20** (rainure de 6, coupés à longueur, écrous en T) : rigide, légère,
  démontable, on y ajoute ou déplace des éléments sans rien réimprimer. Ou contreplaqué de 10 à 15 mm si plus simple
  à l'atelier du club.
- **Impression 3D seulement pour les pièces de liaison** : supports des épaules et du cou sur les profilés, boîtiers.
- **Habillage à la fin**, au choix : coque imprimée en panneaux, mousse et tissu (costume de Câlin), ou plaques
  thermoformées. L'habillage ne porte rien.

**Ossature en profilés (estimation du 16/11/2026, à confirmer quand le buste sera dessiné : ne pas commander avant)** :
boîte de 20 × 15 × 40 cm (largeur, profondeur, hauteur), épaules sur les côtés en haut (≈ 31 cm de large au total),
cou au centre du dessus, pied large en croix.

| Rôle | Nombre | Longueur |
|---|---|---|
| Montants (4 coins) | 4 | 400 mm |
| Traverses largeur (haut, bas, devant, derrière) | 4 | 160 mm |
| Traverses profondeur (haut, bas, côtés) | 4 | 110 mm |
| Traverses du milieu (électronique) | 2 | 160 mm |
| Support du cou / montant du cou | 1 / 1 | 110 / 120 mm |
| Pied en croix | 2 | 350 mm |

≈ 4 m de profilé 20 × 20 (≈ 1,9 kg), coupé à longueur par le vendeur. **Choix du 16/11/2026 : item, ligne 5**
(rainure de 5, système fermé : ne pas mélanger avec des accessoires génériques « rainure 6 / type B ») :
- profilé **5 20x20, naturel, 0.0.370.03** (coupe sur mesure, jusqu'à 6000 mm ; 0,48 kg/m ; 4 rainures ouvertes) ;
  barres entières : 0.0.448.04 (3000 mm), 0.0.611.45 (6000 mm) ;
- **kit équerre 5 20x20, 0.0.425.02** (≈ 30) : équerre Zn + cache + 2 vis M5 × 8 + 2 écrous 5 St M5 ;
- **embout 5 20x20, noir, 0.0.370.09** pour les bouts de profilés ;
- écrous 5 St M5 en plus pour visser les pièces imprimées (supports d'épaule, cou, boîtiers) ;
- le kit raccord 5 20x20x20 (0.0.437.96) demande de tarauder les profilés : pas retenu.

**Dedans** : 2 épaules symétriques, cou (2 servos) et tête (caméra, micro, haut-parleur), carte(s) servos,
alimentation 12 V et interrupteur d'arrêt d'urgence accessible, plus tard l'ordinateur embarqué (Raspberry Pi 5 / Jetson).
Pied lesté ou vissé : bras tendus, il ne doit jamais basculer.

**Ordre** : 1) un bras complet sur le bâti (épaule, socle, poignet) ; 2) le 2e bras en symétrique ; 3) dessin du buste
(ossature + liaisons) ; 4) tête installée et reliée aux bras ; 5) habillage.

## Plus tard : une vraie main à doigts (17/11/2026)

À la place de la pince, sur le bras à servos plus forts (pas sur le bras actuel : l'épaule est déjà à la limite avec la
pince de 205 g, voir `epaule/calcul_poignet.py`).
- Main à 5 doigts : environ 15 phalanges (3 par doigt), une paume en 2 pièces, une quinzaine de petits axes.
- **Mécanisme retenu le 18/11/2026 : deux fils par doigt (« tirer-tirer »), sans élastique ni ressort de rappel.**
  Un fil côté paume ferme le doigt, un fil côté dos l'ouvre ; les deux s'enroulent en sens inverse sur la même poulie
  du servo, qui commande donc le doigt dans les deux sens. Fil de pêche tressé, guides arrondis, un petit tendeur par
  fil ; différence de longueur des deux fils compensée par le diamètre de la poulie (ou un petit ressort sur le fil du dos).
  Écartés : élastiques (vieillissent, se détendent). En réserve : biellettes rigides (plus robustes, moins adaptables).
- À faire d'abord : **un doigt d'essai** avec un seul servo, avant de dessiner la main entière.
- 5 petits servos (un par doigt), dans la paume ou dans l'avant-bras ; 250 à 350 g au bout du bras.
- Reprend le premier projet de main de Nicolas (ESP32, MG90S, gestes).
- Servos des doigts envisagés : **Feetech SCS0009** (bus série comme les STS, 2,3 kg·cm, 23 × 12 × 25 mm, retour de
  position ; **6 V : jamais sur le bus 12 V**, il leur faut leur propre carte alimentée en 6 V). Moins cher mais sans
  retour : MG90S. Bras qui porte la main : STS3095-C002 à l'épaule (et au coude si besoin).
- Avant : poignet (rotation, puis flexion), STS3095-C002 à l'épaule, 2e bras, buste.

## Projet lointain : un petit chien robot autonome (18/11/2026)

Après Câlin. Pas un Spot (30 kg, moteurs spéciaux) : un quadrupède de 2 à 3 kg, taille d'un chat.
- 12 STS3215 (3 par patte : écarter, avancer, genou), même bus et mêmes programmes de base que le bras ; batterie
  embarquée (15 à 30 min) ; centrale inertielle pour l'équilibre. Modèles libres à étudier : SpotMicro, Stanford Pupper,
  Mini Pupper, Petoi Bittle.
- **Autonomie en trois étages** : 1) la marche et l'équilibre, programme rapide embarqué (réflexes, sans IA de conversation) ;
  2) se repérer et éviter les obstacles : lidar 2D et caméra, carte des lieux ; 3) l'IA (Claude) pour comprendre la voix
  et décider où aller (« va à l'accueil », « suis-moi »), pas pour commander chaque pas (trop lente).
- Difficultés : équilibre, marche, chocs sur les servos et les pièces imprimées, terrain (sol dur et plat seulement au début).
- **Chevaux** : un engin à quatre pattes qui marche seul peut effrayer un poney ; accueil et club-house seulement, loin des
  écuries et des carrières, ou habituation très progressive.
- Pour un chien qui se promène vraiment au club, un modèle du commerce (Unitree Go2…) serait plus raisonnable que le fabriquer.

## Feuille de route du premier bras

| # | Étape | État |
|---|---|---|
| 1 | Berceau de banc V4 imprimé, essai à sec (entrée, stabilité, reliefs libres, câbles) | **fait le 07/11/2026** : entre sans forcer, stable, câbles OK (hauteur côté bossage non mesurée) |
| 2 | Berceau V4.1 + bride (inserts M3, vis M3 × 10, patin 1 mm) — `berceau-sts3215/` | abandonné au profit du bras V1 |
| 3 | Premier mouvement : carte Waveshare Bus Servo Adapter (A), cavaliers B, alim 12 V, logiciel FD 1.9.8.2 (COM3, 1000000) | **fait le 07/11/2026** : servo trouvé, 12,3 V, 35 °C, mouvement de 17° à vitesse 300 |
| 4 | Essai sous charge sur le banc : facultatif pour un bras de table (le servo a une grande marge) | reporté |
| 5 | Coude : fourche en deux moitiés tenant l'avant-bras des deux côtés (palonnier + disque libre du dessous) — `coude-sts3215/` | V1 imprimée : écart faux (40,2 calculé, 36,4 mesuré) ; V1.1 aurait frotté sur la partie haute → **V1.2 à imprimer** ; **bras V1** imprimé et monté ; le servo basculait vers l'axe → **bride V1.2 avec cale de 1,4 mm** (serrage 0,5) à imprimer ; rotation de l'avant-bras ± 109° vérifiée hors Fusion |
| 6 | Pince au bout de l'avant-bras — `pince/` | **V3 dessinée (14/11/2026)** : la V2, essayée le 14/11/2026, avait un point mort (un doigt s'est retourné pince fermée, les dents ont sauté à la réouverture). V3 : pivots des bras libres déplacés en diagonale sur deux poteaux de la base, dents des engrenages refaites, 7 vérifications (`pince/tout_verifier.py`) dont une qui retrouve le défaut de la V2 ; 153 g ; **à imprimer** : base, bride, 2 engrenages, 2 bras libres, doigts en deux pièces (plaque à plat + mâchoire couchée, depuis le 15/11/2026) **Décision du 19/11/2026 : pince V4, sans engrenages** (une mâchoire fixe, une mâchoire mobile vissée directement sur le servo, comme le SO-101). Raisons : les deux engrenages de la V3 se décalent en hauteur et sautent, B bascule sur son roulement, les bras libres sortent ; la V4 est aussi plus légère (épaule à la limite avec le poignet). Contrepartie : l'objet n'est pas centré tout seul, le bras amène la mâchoire fixe contre l'objet. **V4 dessinée le 19/11/2026** (`pince/generer_pince_v4.py`) : 2 plaques à imprimer, la base, la bride et les mâchoires de la V3 sont gardées ; parallèle à 72 mm, de la pincette à 90 mm ; programme adapté (`tester_pince`, étalonnage « 4 ») ; à imprimer et essayer |
| 7 | Piloter depuis le PC : `bras/servos.py` (sécurités : butées obligatoires, lent, chaleur, effort, blocage → force coupée) et `bras/test_coude.py` | écrit et testé sur un servo simulé (11/11/2026) ; **essai réel réussi le 12/11/2026** (carte neuve, ancien servo intact : c, ± 30°, à 0,2° près, charge ± 2 %, 31 °C) ; ± 90° avec la fourche complète réussi le même jour (charge ≤ 3 %, 30 °C, 3,6 s par quart de tour) : **coude validé** |
| 8 | Valider la pince sur le support de table (pince montée seule → `bras/tester_pince.bat` → sur l'avant-bras → coude + pince sur le même bus, n° 1 et 4). Sur ce support le coude est couché : la pince saisit de côté (gobelet présenté à la main) | en cours : servo de la pince réglé (butées 1663–2433). Essai de la V2 le 14/11/2026 : défaut de conception (voir ligne 6) → reprendre avec la **V3** ; le programme coupe maintenant la force en 1 s si la pince est coincée. **15/11/2026 : V3 montée (inserts au trou arrière des doigts) et essayée en vrai** : 110 mm à vide, fermeture complète, objets de 38 et 40 mm tenus à 20 % de force, 35 °C ; une lecture de température fausse (75 °C isolé) ne coupe plus le mouvement. Gobelet conique (70 mm en haut) saisi à 51 mm : largeur affichée juste ; serré à 35 % (S) sans se déformer, mâchoires parallèles : **pince validée**. Sur l'avant-bras : coude ± 90° pince montée, charge ≤ 4 %. **15/11/2026 : premier geste réel réussi** (`bras/geste_prendre_poser.bat`) : gobelet saisi à 47 mm (35 %), avant-bras à +89° en le tenant (charge 11 %), lâché, retour au centre ; 29–31 °C. **Étape 8 validée.** |
| 9 | Épaule (servo n° 2) + socle tournant (n° 1, roulements 6807 à mesurer) ; le coude passe au n° 3 | **V1 dessinée le 14/11/2026 dans `epaule/`** (bâti de table, berceau à inserts, haut du bras en fourche avec platine pour le coude, ressort 70 × 10 × 1,2 sur 12 trous au choix ; calcul : servo à 5,6 kg·cm pince vide, 14 avec un gobelet plein, contre 8,3 et 18,8 sans ressort ; à imprimer ; programme d'essai : `bras/tester_epaule.bat`, essayé sur un faux servo). Socle tournant : roulements 6807 **mesurés le 16/11/2026 : Ø ext. 47, Ø int. 35, épaisseur 6,8** (7 annoncé) ; principe retenu : base fixe serrée sur la table avec le servo n° 1 palonnier en haut, 2 × 6807 empilés qui portent le poids, plateau tournant relié au palonnier, bâti vissé dessus par les 4 trous de son pied, câbles par le centre (Ø 35), rotation ± 90°. **Socle monté et essayé en vrai le 20/11/2026 : il tourne** (plateau tenu par la vis centrale du palonnier + 1 vis M2,5, voir `socle/LISEZ-MOI.md`). **V1 dessinée le 17/11/2026 dans `socle/`** (base, palier, entretoise, plateau à moyeu creux ; axe de l'épaule à 179 mm de la table ; contrôles par le calcul, rien d'imprimé). Le socle rehausse le bras de 78 mm : **plan de travail surélevé de 78 mm** pour les objets à saisir (choix du 17/11/2026). **Choix du 13/11/2026 : épaule = un STS3215 + ressort de traction réglable** (plusieurs trous d'accroche, tension réglée à l'essai en regardant la charge). Calcul : bras de 35 cm tendu ≈ 10 kg·cm (objet léger), 15 kg·cm (gobelet plein), pour ≈ 10 kg·cm continus du STS3215. Bras supérieur ≈ 12 cm. Vérin à gaz écarté pour ce bras (force fixe, frottement), à revoir pour le bras de taille humaine  **Premier essai réel de l'épaule le 18/11/2026, sans ressort, bras complet** : étalonnage et mouvements de −20° à +90° réussis, effort maxi 17–18 %, 31 °C au plus (détail dans `epaule/LISEZ-MOI.md`). Reste : levée avec une charge, puis ressort |
| 10 | Poignet : rotation de la pince sur elle-même (servo n° 5), puis flexion (n° 6) | **principe retenu le 17/11/2026** (comme le SO-101) : un STS3215 au bout de l'avant-bras, dans l'axe du bras, la pince vissée sur son palonnier. Nouvelle pièce : support du servo de poignet (s'enfile sur l'avant-bras à la place de la pince, même manchon, 2 vis M3 × 30). À réimprimer : la **base de la pince** seulement (manchon remplacé par une platine sur le palonnier). Avant-bras + 5 cm et + 70 g au bout ; rotation ± 90° (câble de la pince). À dessiner après l'essai de l'épaule (effort réel mesuré avec la commande m) **Rotation dessinée le 19/11/2026 dans `poignet/`** (support où le servo glisse par le haut, barre, base de pince à moyeu ; + 48,7 mm et + 90 g ; ± 90° sans contact par le calcul ; rien d'imprimé) |
| 11 | Aller à un point de la table : calcul des angles (socle, épaule, coude), sans caméra | à faire après le socle tournant ; tenir compte du décalage de 53,5 mm entre l'axe du socle et le plan de la pince, et du plan de travail surélevé de 78 mm |
| 12 | **Caméra fixe au-dessus du plan de travail** (18/11/2026) : webcam regardant vers le bas (C270 ou une deuxième), 4 marqueurs ArUco aux coins du plan de travail, vision de `tete/` reliée au bras | dès le socle tournant pour la détection ; **correction du 20/11/2026** : sans flexion du poignet, la pince n'est à plat (gobelet debout) que pour UNE distance, environ 34 cm de l'épaule (épaule à −25°, avant-bras horizontal) : le bras ne prend donc un gobelet debout que sur un ARC de cercle autour du socle, pas « où qu'il soit ». Prendre n'importe où sur le plan de travail demande la **flexion du poignet** (elle garde la pince à plat quand la distance change) ; rotation du poignet → objets allongés pris dans le bon sens ; flexion → prise par le dessus et tri. Plus tard : caméra de la tête de Câlin, éventuellement caméra au poignet |

## Incident du 08/11/2026 et règles de sécurité

Premier branchement avec la fourche du coude montée : **odeur de brûlé**, puis plus rien. La carte
Waveshare n'apparaît plus du tout sur l'ordinateur (ni COM, ni périphérique inconnu, deux câbles USB
essayés) : sa partie USB est morte. Câble du servo intact, aucune trace visible sur la carte.
Cause **non établie** ; hypothèse la plus probable : servo bloqué contre une colonne (butées pas
encore réglées), forçant en continu. Servo d'origine **suspect** : ne le rebrancher qu'en dernier.

Reprise : carte neuve testée seule (port COM) → avec un servo neuf seul, sans rien dessus → enfin
l'ancien servo, seul, sans fourche, prêt à tout débrancher.

Règles désormais :
1. **Butées réglées dans le servo (Min/Max Angle Limit) AVANT de monter quoi que ce soit dessus.**
2. **Protection de couple et de courant** réglée dans FD.
3. **Interrupteur sur le 12 V** pour tout couper d'un geste.
4. **Jamais brancher ou débrancher un servo sous tension.**

## Matériel (décisions du 07/11/2026)

- **Servos** : 8 STS3215-12V (C018, 30 kg·cm, 1/345) de plus, chez Feetech (Shenzhen Feite Model, Alibaba) →
  9 en tout : bras de table complet à 6 axes + rechanges. Vérifier que disques, vis et câble sont inclus.
  **Reçus le 18/11/2026 : 6 servos de plus (9 en tout).** Numéros : socle 1, épaule 2, coude 3 (encore au n° 1 tant que le
  socle n'est pas monté), pince 4, rotation du poignet 5, flexion du poignet 6, cou 7 (tourner) et 8 (hocher) ; 1 de rechange.
  Chaque servo neuf est testé seul dans FD, numéroté et étiqueté avant montage ; butées réglées au moment du montage.
- **Carte** : la Waveshare Bus Servo Adapter (A) suffit pour tous les servos (en chaîne, un ID par servo).
  **À racheter** (USB de la première carte mort le 08/11/2026).
- **Alimentation** : prévoir 12 V, 5 A minimum (6 à 10 A conseillé) pour 6 servos.
- **Socle tournant** : roulements **6807-2RS** (35 × 47 × 7) ; **deux roulements empilés et
  espacés** dans le socle pour que le bras ne bascule pas, le servo ne fait que tourner.
- **Roulements commandés le 10/11/2026** (123roulement, commande C 81156268, 75,84 € TTC) :
  **6807-2RS × 8** (35 × 47 × 7) = 2 par socle de bras × 2 bras + 2 pour la rotation de la tête
  + 2 de rechange ; **623ZZ × 10** (3 × 10 × 4, axe = vis M3) pour les petits pivots (doigts de
  pince, tête). À réception : mesurer un roulement de chaque au pied à coulisse avant de dessiner
  les logements.
  Coude, épaule et poignet n'en ont pas besoin : chaque servo est tenu des deux côtés par ses deux disques.

## Repères sur le servo (STS3215-C018)

- Boîtier mesuré : 45,2 × 24,4. **Hauteur variable** (08/11/2026) : **28,8** côté palonnier, **33** à partir de 15,6 mm
  du bout côté palonnier (partie haute, plaque de l'étiquette).
- Dessous : cylindre Ø5,5 (centre à 8,1 mm du petit côté X−) et bossage 11,9 × 18,3 côté X+,
  reliefs de 2 mm ; connecteurs entre les deux.
- Étiquette : **STS3215-12V** (alimentation 12 V confirmée).
- Palonnier : **disque aluminium Ø19,7 mm**, dépasse de **4,3 mm** au-dessus du boîtier, centre à **8,1 mm** du petit côté, **aligné avec le cylindre du dessous** (remesuré le 07/11/2026 ; une première mesure à 10,5 était fausse).
  4 trous taraudés sur un cercle de **≈ 13,45 mm** de diamètre (bords intérieurs 10,3, extérieurs 16,6), petites vis fournies (taille à confirmer, probablement M3), vis centrale.
  Vis fournies : **≈ 2,5 mm de diamètre → M2,5** (trou de passage à prévoir ≈ 2,9 mm dans les pièces imprimées).
  **Second disque** fourni (palonnier libre du dessous) : 4 trous taraudés, alésage central avec collerette côté servo ; monté sur le cylindre, il **tourne librement** (pas de cannelures) et dépasse de **3 mm** sous le boîtier.
  Entre les faces extérieures des deux disques : **36,4 mm mesurés** le 08/11/2026 = 3,3 (disque bas) + 28,8 (boîtier) + 4,3 (palonnier).
  Leçon : une cote de hauteur se prend **à l'endroit précis** où la pièce appuie.
- **Axe de sortie au-dessus du cylindre** (côté X−) : le cylindre est **coaxial** à la sortie
  (confirmé) et sert de second pivot au coude.
- Servo « bus série » : jamais branché directement sur une broche de l'ESP32 ; carte d'interface
  et alimentation dédiée obligatoires.

## Référence utile

Les bras de table open source SO-100 / SO-101 utilisent ce même servo (6 par bras) : bonne source
d'inspiration pour le coude, le poignet et la pince.
