# Bras — piloter les servos depuis le PC

`servos.py` : la « moelle épinière » (parler aux servos STS3215 par la carte Waveshare en USB).
`test_coude.py` : premier essai motorisé du coude, pas à pas. Bibliothèque `scservo_sdk` de
Feetech/Waveshare (copiée depuis `driver-servo/STServo_Python.zip`).

## Les sécurités (leçons de l'incident du 08/11/2026)

| Règle | Ce que fait le programme |
|---|---|
| Butées réglées **dans le servo** avant tout mouvement | refuse de bouger tant qu'elles ne le sont pas ; propose de les régler (908 et 3188 pour le coude = ± 100°) |
| Jamais hors des butées | toute position demandée hors 908–3188 est refusée |
| Lentement | vitesse 300, accélération 20 (comme les essais dans FD) |
| Servo qui chauffe | refuse de partir à 55 °C ou plus ; coupe la force s'il y arrive pendant un mouvement |
| Servo qui force (bloqué contre quelque chose) | charge ≥ 70 % pendant plus de 0,5 s → **force coupée** |
| Servo qui n'avance plus (14/11/2026) | immobile 0,7 s loin de sa cible → **force coupée**. Pour la pince, dont la force est limitée à 50 %, le seuil « servo qui force » est baissé à 35 % : avant, il n'était jamais atteint et le servo a poussé jusqu'à faire sauter les dents |
| Servo qui n'arrive pas | pas arrivé en 8 s → **force coupée** |
| En quittant (q, Ctrl + C, erreur) | **force coupée** : le coude devient libre |

Testé ici sur un **servo simulé** (pas de matériel) : refus sans butées, butées écrites puis mémoire
du servo reverrouillée, mouvement normal, refus hors butées, obstacle sur la course → force coupée,
servo trop chaud → refus. **Essai réel le 12/11/2026 : centre et ± 30° réussis** (précision 0,2°, charge ± 2 %, 31 °C).
Plusieurs commandes d'un coup, séparées par des espaces (« c g d c ») ; si un mouvement est refusé, la suite est annulée.

## Avant l'essai

1. **Carte neuve** validée seule (port COM visible).
2. Servo du coude **seul** sur la carte, **sans fourche** pour le premier lancement.
3. **FD fermé** (un seul programme à la fois sur la carte), cavaliers sur **B**, 12 V puis USB.
4. Dans le dossier `bras`, double-cliquer **`installer.bat`** (une seule fois, une minute).

## L'essai

1. **Double-cliquer `tester_coude.bat`.** Il trouve la carte et le servo et affiche son état.
2. S'il propose de **régler les butées**, répondre **o**.
3. Essayer **c** (centre), **g** / **d** (± 30°), **i** (infos), **l** (libre).
4. **q** pour quitter (force coupée).
5. Puis : couper le 12 V, monter la fourche **avec l'avant-bras dans l'axe quand le servo est au
   centre**, tourner à la main d'une butée à l'autre, relancer, et refaire c, g, d, puis **G** / **D**
   (± 90°) en surveillant température et charge sur la ligne affichée après chaque mouvement.

Si le programme dit « Carte introuvable » : FD est peut-être encore ouvert, ou le port est un autre :
`tester_coude.bat --port COM4`. Plusieurs servos branchés : `--id 3`.

## Essai de la pince (`tester_pince.bat`)

Pince montée (plan de montage `pince/sortie/plan_montage.pdf`), son servo **seul** sur la carte, FD fermé.

1. Double-cliquer **`tester_pince.bat`**. Il cherche le servo n° 4 (il prévient si le numéro est autre).
2. Butées : il vérifie 1663–2433 (propose de les régler sinon).
3. **Étalonnage du milieu** (premier lancement, ou servo hors de ses butées, ou commande **e**) : la force
   est coupée, régler la pince **à la main** à mi-ouverture (71 mm au creux des mâchoires, ou 81 mm entre
   les trous du bout des bras si les doigts ne sont pas montés), taper **o** : le servo prend cette position
   comme milieu (2048 ; registre 40 = 128, table mémoire Feetech), gardé même éteint. Ainsi l'engrenage A se
   visse là où ses trous tombent sur le palonnier, sans chercher l'angle exact (13/11/2026).
4. Puis, rien entre les doigts. La pince va au milieu puis bouge un peu ; répondre
   **o** si les mâchoires se sont **écartées**, **f** si elles se sont **rapprochées**. Retenu dans
   `sens_pince.json` (supprimer ce fichier pour redemander).
5. Commandes : **c** milieu (≈ 71 mm) · **o** ouvrir en grand (110 mm) · **s** serrer doucement (force 20 %)
   · **S** serrer plus fort (35 %) · **f** fermer à vide · **l** lâcher (libre) · **i** infos · **e** refaire l'étalonnage · **q** quitter.
   Plusieurs d'un coup : `o s`.
6. **Serrer** avance avec une force limitée et **s'arrête tout seul** sur l'objet (immobile + effort) ;
   il affiche la largeur estimée de l'objet. Ne pas laisser un objet serré plusieurs minutes.

Toutes les autres sécurités du coude restent (butées, chaleur, blocage ; force jamais au-delà de 50 % pour la pince).
Essai réel de la V2 le 14/11/2026 : étalonnage, ouverture et fermeture réussis, puis défaut de la pince (doigt retourné, voir `pince/LISEZ-MOI.md`). **À refaire avec la pince V3.**

## Essai de l'épaule : `tester_epaule.bat`

Voir `epaule/LISEZ-MOI.md`. Différence importante avec le coude et la pince : l'épaule porte le bras, donc ce programme
ne coupe jamais la force sans demander de tenir le bras, et une sécurité qui se déclenche **retient le bras sur place**
(force réduite à 40 %) au lieu de le lâcher (`si_arret='retenir'` dans `servos.py`).

## Essayer les sécurités sans matériel

`python test_securites.py` : douze sécurités vérifiées sur un faux servo (`servo_simule.py`), en 6 secondes : refus sans butées, hors butées, servo trop chaud, **pince coincée → force coupée en 1 s**, serrage sur un objet, étalonnage. À relancer après chaque modification de `servos.py`.

**Force de maintien (19/11/2026)** : une fois l'objet saisi (20 % avec `s`, 35 % avec `S`), la pince ne garde que **12 %** pour
le tenir : le servo, qui pousse sans tourner, chauffe moins (42 °C relevés en tenant un verre à 20 %). Valable dans
`tester_pince`, `piloter_bras` et `geste_prendre_poser`. Pour essayer une autre valeur : `tester_pince.bat --maintien 15`
(0 = pas de baisse). Si un verre plein glisse, augmenter ; du caoutchouc sur les mâchoires permet de baisser.
**Essai réel du 19/11/2026** : gobelet à moitié plein tenu à 12 % pendant toute une série de montées et descentes
(mâchoires stables à 54 mm), pince à 33–34 °C au lieu de 42 ; épaule ≤ 18 %, coude ≤ 15 %. **Valeur par défaut portée à 20 % le 19/11/2026** (demande de Nicolas, pour le verre plein) : `s` tient donc à 20 %, `S` serre à 35 %
puis tient à 20 %. Pour un objet léger, `--maintien 12` chauffe moins. Essai du même jour, bras sans socle, coude au n° 3 :
verre saisi à 56 mm, monté à +60° et redescendu deux fois, épaule ≤ 24 %, 26 °C.

## Premier geste : prendre et poser (`geste_prendre_poser.bat`)

Coude (n° 1) et pince (n° 4) sur le même câble, pince sur l'avant-bras, FD fermé. Avant : `tester_coude.bat`
et `tester_pince.bat` au moins une fois (butées, étalonnage, sens de la pince) ; sinon le programme refuse
et dit lequel lancer.

1. **g** (poser d'un côté) ou **d** (de l'autre). Coude au centre, pince ouverte.
2. Présenter le gobelet entre les mâchoires, **Entrée** : la pince serre à 35 % et s'arrête sur l'objet
   (largeur affichée). Rien entre les doigts → elle se rouvre et le geste s'arrête.
3. L'avant-bras tourne de 90° en tenant le gobelet. Si le coude est arrêté par une sécurité, la pince
   tient toujours : Entrée pour qu'elle lâche (main dessous).
4. Main ou boîte sous le gobelet, **Entrée** : la pince le lâche ; retour au centre. **q** pour quitter
   (force coupée sur les deux servos).

Sur le support de table, le coude est couché : la pince saisit de côté. Simulé ici (geste complet, coude
bloqué en route, rien entre les doigts) ; **réussi en vrai le 15/11/2026** (gobelet tenu à 47 mm, avant-bras à +89°, 31 °C max).

## Piloter le bras entier (`piloter_bras.bat`) — épaule, coude et pince ensemble

Avant : `tester_epaule.bat --coude 1` (étalonnage), `tester_coude.bat --id 1` et `tester_pince.bat` au moins une fois ; sinon le
programme refuse et dit lequel lancer. Premier lancement : il apprend le **sens du coude à la main**, sans moteur (on tient
l'avant-bras, on le fait remonter d'environ 20°), retenu dans `sens_coude.json`.

Angles : **épaule** = haut du bras par rapport à l'horizontale (−30° à +90°) ; **coude** = avant-bras par rapport au haut
du bras (0° = dans le prolongement, + = il remonte, ± 90°).

| Commande | Effet |
|---|---|
| `e30` | épaule à +30° (le coude ne bouge pas) |
| `c-45` | coude à −45° |
| `plat` | avant-bras remis à l'horizontale |
| `n20` | épaule à +20° **en gardant l'avant-bras à l'horizontale** : les deux servos bougent ensemble (pour porter un gobelet) |
| `poser` | descend degré par degré, avant-bras à l'horizontale, jusqu'à **sentir la table** (variation de charge de 10 points à l'épaule ou au coude), remonte d'1°, ouvre la pince, remonte de 20°. S'il arrive en bas sans rien sentir, il n'ouvre pas |
| `o` · `s` · `S` | pince : ouvrir · serrer doucement · serrer fort |
| `repos` | bras à la verticale (il ne force presque plus) |
| `i` · `q` | infos · quitter (en tenant le bras) |

Plusieurs à la suite : `n0 o s n40`. Après chaque geste : angles, hauteur du bas de la pince au-dessus de la table, charges, températures.

Sécurités : butées de chaque servo, chaleur, blocage (les servos **retiennent** le bras au lieu de le lâcher) ; **refus d'un
geste qui enverrait la pince dans la table** ; pendant `n`, si un servo prend plus de 7° de retard sur l'autre, tout s'arrête
(sinon le coude continuerait seul et pencherait la pince). Avec le socle tournant : `piloter_bras.bat --hauteur 179`.

**Essai réel le 18/11/2026** : `e`, `n` et la pince fonctionnent (verre de 25 cl tenu, descente à plat de +20° à −10°, charges ≤ 14 %,
servo de la pince à 42 °C en tenant le verre). Corrigé : geste refusé quand l'épaule lit un peu plus de 90°. `poser` : simulé seulement.

## Socle tournant (19/11/2026) : numéros et programmes

Avec le socle : **socle n° 1, épaule n° 2, coude n° 3, pince n° 4**. Les programmes trouvent tout seuls le coude : n° 3 s'il
existe, sinon n° 1 (`numero_coude`, `numero_socle` dans `servos.py`). Rien à changer tant que le socle n'est pas monté.

- **`tester_socle.bat`** : au premier lancement, **étalonnage à la main** (plateau tourné parallèle à la base, cette position
  devient 2048 ; commande `e` pour le refaire) : les trous du palonnier ne tombent pas forcément « en face » à 2048. Butées 1024–3072, puis `c` en face, `g` / `d` = ± 30°, `G` / `D` = ± 90°.
  Refuse de démarrer si le n° 1 est encore le coude (pas de servo n° 3).
- **`piloter_bras.bat`** : commande **`t45`** = socle tourné à +45° (de −90 à +90), `t0` = en face. Hauteur de l'épaule prise
  à 179 mm quand le socle est là (101 sinon). `tester_epaule.bat --coude 3` pour retenir le coude à son nouveau numéro.

Simulé seulement (avec et sans socle) ; pas encore essayé en vrai.

## Fenêtre de commande (`controle_bras.bat`) — 19/11/2026

Une fenêtre Windows pour piloter le bras à la souris : curseurs **socle**, **épaule**, **coude** (le mouvement part quand on
lâche le curseur), case « garder l'avant-bras à l'horizontale », boutons de la **pince** (ouvrir, serrer doux, serrer fort),
**Repos**, **Poser sur la table**, gros bouton **ARRÊT** (le bras se fige, tenu). À côté de chaque curseur : angle réel,
charge, température. **Réglages** par curseurs, gardés dans `reglages_bras.json` : vitesse (80 à 800, 300 par défaut),
accélération, serrage doux, serrage fort, force de maintien.

Mêmes sécurités que `piloter_bras` (butées, chaleur, blocage, pince dans la table). Il faut avoir fait une fois les
étalonnages (`tester_epaule`, `tester_coude`, `tester_pince`, `piloter_bras`) : sinon un message dit lequel lancer.
En fermant la fenêtre : message « tiens le bras », puis force coupée.

La logique (mouvements, refus, arrêt, réglages) est essayée sur des servos simulés. **La fenêtre elle-même n'a pas pu être
ouverte ici** (pas d'affichage) : premier essai chez Nicolas.

## Pince V4 (19/11/2026)

`tester_pince.bat`, commande **e** : il demande quelle pince est montée (3 = engrenages, 4 = sans engrenages), gardé dans
`version_pince.json`. V4 : étalonnage à **58 mm** entre les mâchoires (54 avec les tapis), largeur affichée = écart entre les
tapis au milieu des mâchoires ; bouts qui se touchent = « rien de tenu ». Formule vérifiée contre le modèle ; pas encore essayé.

## Protocole d'essai des articulations — `protocole_bras.bat` (20/11/2026)

**Essayé sur 4 servos simulés seulement, pas encore sur le vrai bras.**

Toujours les mêmes mouvements, tout est mesuré et rangé dans `bras/rapports/protocole_DATE.txt` (à envoyer) :

| Étape | Mouvements | Ce qu'on regarde |
|---|---|---|
| 0 | état au départ | température, tension |
| 1. Coude | épaule à la verticale ; +45, 0, −45, 0, +90, −90, 0 ; 5 allers-retours | écart à l'arrivée, effort, retours au même endroit |
| 2. Épaule | bras tendu ; 60, 30, 0 ; **tenue 30 s à l'horizontale** ; 5 allers-retours 60 ↔ 30 | effort pour tenir, échauffement |
| 3. Socle | bras à la verticale ; ±45, ±90 ; 5 allers-retours ; question « revenu en face du repère ? » ; puis bras à 30° | glissement du plateau sur le palonnier |
| 4. Pince | ouvrir, serrer doux, serrer fort, à vide | fermeture complète |

Seuils du jugement BON / À VOIR (dans `SEUILS`, à ajuster) : écart 3° (6° pour l'épaule), retours étalés sur 1,5° au plus,
effort 60 % en mouvement et 40 % en tenue, 55 °C, + 8 °C pendant la tenue, 11 V au moins.

Options : `--rapide` (2 allers-retours), `--sans-pince`, `--sans-socle`, `--tenue 60`.
Un mouvement arrêté par une sécurité retient le bras ; Ctrl+C aussi, et le rapport déjà rempli est gardé.

### Premier protocole sur le vrai bras (20/11/2026, complet, pince V3 à vide)

Tout est BON : 26 à 28 °C partout à la fin, 12,1 V au plus bas.
- **Coude** : écart ≤ 0,2°, effort 10 à 16 %, retours identiques.
- **Épaule** (sans ressort) : écart ≤ 1,3°, effort 21 à 25 % en montant, 8 à 13 % pour tenir après une montée,
  3 % après une descente (les frottements du réducteur portent alors le bras) ; aucun échauffement en 30 s.
- **Socle** : effort 13 à 24 % ; s'arrête à +0,7° ou −0,7° de la cible selon le sens d'arrivée (jeu d'environ 1,4°) ;
  à +90° : −1,6° et 15 % pour tenir → quelque chose retient de ce côté (câble ?), à regarder.
- Une lecture de température isolée à 47 °C (fausse, déjà connue).
- La question « revenu en face du repère » a été posée socle à +65° : réponse sans valeur, protocole corrigé
  (le socle va à 0° avant le repère ; la tenue de l'épaule se fait après une montée).

**Sens vérifiés par Nicolas le 20/11/2026** (fenêtre de contrôle) : ouvrir/serrer, coude, épaule dans le bon sens ;
**socle : angle positif = à droite, vu de DERRIÈRE le bras** (la droite du robot ; vu de face, c'est à gauche). `tester_socle` : g et G vont à gauche, d et D à droite.

### Deuxième protocole sur le vrai bras (20/11/2026, 21 h 10, protocole corrigé)

Tout est bon ; le seul « À VOIR » (épaule 22 → 58 °C en 30 s) est une **fausse lecture de température** : la ligne suivante
relit 22 °C. Le protocole prend maintenant la médiane de 3 lectures.
- **Épaule, vrai effort bras tendu à l'horizontale (atteint en montant) : 14 %**, stable 30 s, sans échauffement (22 → 23 °C sur l'essai).
- **Plateau du socle : ne glisse pas** (bras revenu en face du repère après tous les mouvements).
- Socle à +90° : toujours −1,6° et 15 % pour tenir (rien de tel à −90°) ; ailleurs ±0,6° selon le sens d'arrivée.
- Coude : inchangé, écart ≤ 0,3°.

## Poignet — `tester_poignet.bat` (20/11/2026)

**Essayé sur un servo simulé seulement.** Servo n° 5, butées 1024–3072. Le programme ne parle qu'à ce servo : poser le
bras à plat avant. Étalonnage à la main (pince droite → milieu), puis `c` (droite), `g` / `d` (45° d'un côté / de
l'autre), `G` / `D` (90°), `e`, `i`, `q`. Force limitée à 50 % : un câble qui retient la pince arrête le mouvement.
Le sens (quel côté est +) est à noter au premier essai.

Pas encore fait : le poignet dans `piloter_bras`, `controle_bras` et `protocole_bras`.

## Flexion du poignet — `tester_flexion.bat` (20/11/2026)

**Essayé sur un servo simulé seulement.** Servo n° 6, butées 1024–3072. Ce poignet porte la pince : il est RETENU par les
sécurités, jamais lâché. Étalonnage à la main, pince soutenue : pince droite → milieu, puis on la lève pour apprendre le
sens « haut » (`sens_flexion.json`). Commandes : `c` (droit), `h` / `b` (30° haut / bas), `H` / `B` (60°), `e`, `i`, `q`.
En quittant, il demande de soutenir la pince avant de couper la force. Ctrl+C : le poignet reste tenu.

### Poignet (rotation) : premier essai réel et intégration (21/11/2026)

Essai réel de `tester_poignet` : ± 45° et ± 90° atteints, charge 0 à 3 %, 27–28 °C, 12,2 V.
**Sens : angle positif = le haut de la pince part à GAUCHE, vu de derrière le bras** (l'inverse du socle, où + = à droite).
Montage du jour : 3 vis sur 4 au palonnier (tournevis trop court pour la 4e), servo un peu libre dans son support.

Le poignet est pris en compte **dès que le servo n° 5 répond** (essayé en simulation seulement) :
- `piloter_bras`, `controle_bras` et `protocole_bras` comptent le bras plus long de 48,7 mm et le point bas de la pince à
  60 mm sous l'axe (pince tournée) : la sécurité « la pince irait dans la table » reste juste ;
- le poignet est tenu, force limitée à 50 % ; commande `p45` dans `piloter_bras`, curseur « Poignet » dans la fenêtre,
  étape « Poignet » dans le protocole ;
- il faut avoir lancé `tester_poignet.bat` une fois (étalonnage), sinon ces programmes le demandent.

### Protocole avec le poignet (rotation) et la pince V4 (21/11/2026, 15 h 51)

Tout est BON, 31 à 33 °C à la fin.
- **Épaule, bras tendu à l'horizontale : 20 % pour tenir** (14 % sans le poignet), stable 30 s sans échauffement ;
  29 à 32 % en montant (22 à 25 % avant) ; arrive 2,1° sous la cible (1,4° avant).
  Rapport 20 / 14 = 1,43 : **le calcul (`epaule/calcul_poignet.py`) annonçait 1,41**. Les efforts relatifs du calcul sont donc fiables ;
  ses valeurs en kg·cm restent environ deux fois trop fortes par rapport au pourcentage lu.
- Coude : 10 à 20 %, écart ≤ 0,3°. Socle : inchangé (toujours −1,6° et 15 % à +90°), plateau revenu en face du repère.
- **Poignet : écart ≤ 0,3°, effort 10 à 12 % en mouvement**, retours identiques.
- **Tension : creux à 11,9 V (épaule qui monte), 11,7 V et 11,4 V (lectures pendant l'étape du poignet)** : elle ne descendait pas
  sous 12,1 V avant. À surveiller avec les servos 3095 : connaître le courant du bloc 12 V.
- Projection pour le poignet complet (rotation + flexion), d'après le même calcul : ≈ 30 % pour tenir bras tendu à vide,
  ≈ 45 à 50 % en montant : tenable à vide et avec un objet léger avec le servo actuel.

### Flexion du poignet prise en compte par les programmes (21/11/2026, essayé sur 6 servos simulés seulement)

Dès que le servo n° 6 répond (et que `tester_flexion.bat` a été lancé une fois) :
- la flexion est **tenue** par `piloter_bras`, `controle_bras` et `protocole_bras`, jamais lâchée ;
- la longueur du bras et la sécurité « la pince irait dans la table » tiennent compte de l'angle du poignet
  (bras compté à 482 mm de l'épaule aux mâchoires avec les deux mouvements du poignet) ;
- `piloter_bras` : commande `f30` (pince relevée de 30°) ; fenêtre : curseur « Poignet (plier) » et case
  **« Garder la PINCE à l'horizontale avec le poignet »** : quand l'épaule ou le coude bougent, la flexion compense ;
- protocole : étape « Poignet : flexion ».

## Vérifier les butées de tous les servos — `verifier_butees.bat` (21/11/2026)

**Essayé en simulation seulement.** Ne fait rien bouger. Affiche pour chaque servo qui répond : numéro, rôle, butées lues,
butées attendues, position, verdict. Propose de régler celles qui manquent (réponse « o » exigée), sauf l'épaule
(étalonnage par `tester_epaule.bat`) et un servo qui se trouve en dehors des butées à poser.

### Protocole avec le poignet complet (flexion + rotation), pince V4 avec mâchoires, sans ressort (23/11/2026, 20 h 21)

Tout est BON, 32 à 39 °C à la fin (le socle est le plus chaud : 39 °C).
- **Flexion du poignet, premier essai réel : écart ≤ 0,4°, effort 10 à 19 %**, retours identiques.
- **Épaule : 45 à 52 % en montant** (29 à 32 % avec la rotation seule, 22 à 25 % sans poignet), soit 2 fois l'effort d'origine,
  comme le calcul l'annonçait (2,1). Pour tenir après une montée : 30 % à +30°, 18 à 19 % à +60°. Arrive 3,2° sous la cible à +30°.
  La tenue « à l'horizontale » (11 %) a été mesurée après une descente : chiffre trop flatteur, protocole corrigé
  (bras long : palier à +15° atteint en montant).
- Coude : 25 à 33 % pour remonter l'avant-bras à la verticale, écart ≤ 0,5°. Rotation du poignet : 11 à 14 %.
- Socle : inchangé (−1,4° et 14 % à +90°), plateau revenu en face du repère.
- Tension : un creux à 11,5 V, sinon 12,0 V au plus bas.
- Marge restante à l'épaule avant le seuil « À VOIR » (60 %) : faible. À vide c'est bon ; avec une charge, il faut le ressort
  puis le servo 3095.

### Protocole avec le poignet complet ET le ressort (23/11/2026, 20 h 50) — trou du mât : rangée du haut, colonne du milieu

| Épaule | sans ressort (20 h 21) | avec ressort |
|---|---|---|
| Effort en montant vers 30° | 52 % | 31 à 34 % |
| Effort en montant de 30° à 60° | 45 à 49 % | 26 % |
| Tenue à 30° après une montée | 30 % | 10 % |
| Tenue à 60° après une montée | 18 à 19 % | 5 à 6 % |
| Écart à 30° | −3,2° | −1,0° |
| Tenue 30 s à +15° | (non mesurée) | 12 %, sans échauffement |
| **À la verticale (+90°)** | écart +0,2°, **0 % en tenue** | **écart −3,3°, 30 à 32 % en tenue** |
| Température de l'épaule en fin d'essai | 35 °C | **43 °C** |

Le ressort divise presque par deux l'effort de l'épaule dans la zone de travail. **Mais bras à la verticale, il gêne** : le servo
n'atteint plus 90° et force à 30 % en permanence (d'où les 43 °C). Entre ses deux accroches il ne reste que 40 mm à 90°, pour
un ressort de 70 mm : il doit se plier de côté, et quelque chose l'en empêche (crochets bloqués par les écrous ? ressort qui
appuie sur le mât ou le bras ?). À inspecter. Le ressort reçu n'a pas été mesuré.

### Protocole avec le ressort (trou du haut) et le repos à 80° (23/11/2026, 21 h 14)

- **Au repos (80°) l'épaule ne force plus : 6 à 8 % en tenue**, écart 0,6° (au lieu de 30 % et 3,3° à 90°). Sa température reste à 39 °C.
- Zone de travail inchangée : 25 à 34 % en montant, 14 % pour tenir à +15°, 10 % à +30°, 6 % à +60°.
- Coude, socle, flexion et rotation du poignet : comme avant.
- Un « À VOIR » : **une lecture de tension à 10,9 V**, isolée, pendant un mouvement du poignet à 12 % d'effort, entourée de lectures à
  12,2 V. Déjà vu à 11,5 / 11,4 / 11,3 V les fois précédentes, toujours une seule ligne. Probablement une lecture fausse, sans
  certitude : le protocole retient désormais la deuxième plus basse lecture. À revoir avec l'alimentation de 10 A.

## Aller à un point de la table — `aller_point.bat` (23/11/2026)

**Essayé sur 6 servos simulés seulement.** Il faut le socle et le poignet complet.

Repère : origine sur l'axe du socle, X vers la droite du robot (vu de derrière), Y vers l'avant, en mm (le même que `camera/`).
Le plan du bras est **décalé de 53,5 mm à gauche** de l'axe du socle, vu de derrière (photo du 23/11/2026) : `geometrie.py` en tient compte.

- `v X Y` : calcule les angles (socle, épaule, coude, poignet) pour une pince À PLAT au-dessus du point, les affiche, demande
  confirmation, relève le bras s'il faut tourner, tourne le socle, puis place la pince au-dessus (épaule relevée de 25°) ;
- `d` descend sur le point (axe de la pince à 45 mm de la table : bas des mâchoires à 10 mm), `m` remonte ;
- `o` / `s` pince, `r` repos, `i` où est la pince, `q` quitter.

**Zone où la pince peut se poser à plat : de 356 à 450 mm de l'axe du socle** (par le calcul), sur un quart de tour de chaque côté.
Plus près, le coude dépasserait −90° ; plus loin, le bras est trop court.
La sécurité de la table compte maintenant la pince droite à 40 mm sous son axe (60 mm si elle est tournée de plus de 15°).

### Fenêtre de contrôle : « Déplacer la pince » (23/11/2026, essayé en simulation seulement)

Nicolas avait du mal à combiner épaule, coude et poignet pour aller chercher un objet. Nouveau cadre dans la fenêtre : on déplace
**la pince**, et le programme calcule les trois articulations (`geometrie.angles_plan`).
- deux ronds : **« Pince à plat »** (prendre par le côté ; départ à 400 mm devant l'épaule, 130 mm de haut) et **« Pince vers le
  bas »** (prendre par le dessus ; départ à 220 mm, milieu des mâchoires à 70 mm) ;
- quatre boutons : Reculer, Avancer, Descendre, Monter, par pas de 2 cm, en gardant l'inclinaison choisie ;
- une ligne dit où est la pince ; un geste impossible est refusé en rouge avec sa raison.
Le socle et la rotation du poignet gardent leurs curseurs. La sécurité de la table tient compte de l'inclinaison de la pince.

### Zone atteignable du bras complet, et ce qui l'agrandirait (calcul du 23/11/2026)

Premier essai réel de « Déplacer la pince » : « Monter » refusé à 389 mm de l'épaule, coude en butée à −90°.
La zone où la pince tient à plat est une colonne étroite : **380 à 460 mm devant l'épaule**, de 50 à 330 mm de haut.
Pince vers le bas : seulement 190 à 255 mm devant l'épaule, entre 50 et 90 mm de haut.

| Piste | Gain calculé |
|---|---|
| Essayer l'autre configuration du coude (coude en bas) | + 7 % de positions à plat, rien de plus près de la table |
| Coude de ± 100° au lieu de ± 90° (les butées du servo sont déjà à ± 100°) | + 17 % ; la bande de prise passe de 352–446 à 326–446 mm |
| Flexion du poignet de ± 110° au lieu de ± 90° | zone « pince vers le bas » multipliée par 2,3 |

Fait dans la fenêtre : un déplacement hors de portée **glisse** vers le point atteignable le plus proche (monter en avançant un
peu, par exemple) et le dit ; pas réglable (1, 2, 5 ou 10 cm). `geometrie.angles_plan` sait calculer les deux configurations du
coude, mais la fenêtre n'utilise que « coude en haut ». Essayé en simulation.

**Amplitudes vérifiées par le calcul le 23/11/2026** (pièces seules, sans les câbles) :
- **flexion du poignet : libre jusqu'à ± 96° seulement**, la fourche touche ensuite son support. Les ± 110° envisagés plus haut
  sont donc impossibles avec les pièces actuelles ; il faudrait une fourche plus longue.
- **coude : la fourche de l'avant-bras est libre jusqu'à ± 109°**, avec le berceau actuel comme avec le berceau à parois hautes ;
  de −90° à −100°, ni le poignet ni la pince ne touchent le berceau du coude. Passer la limite du programme de 90° à 97° est donc
  possible côté pièces ; reste à vérifier sur le vrai bras, à la main, que les câbles et le haut du bras ne gênent pas.

**Inclinaisons intermédiaires (23/11/2026).** Constat de Nicolas : pince vers le bas, on ne prend rien au-delà d'une petite zone
proche du socle. Calcul, bas de la pince à 10 mm de la table : à plat 356–450 mm devant l'épaule ; à −45° 342–420 ; à −60° 294–374 ;
à −75° 242–324 ; à −90° 190–260. Plus la pince pointe vers le bas, plus elle travaille près. La fenêtre propose maintenant quatre
inclinaisons (à plat, 45°, 70°, vers le bas), qui se recouvrent de 19 à 45 cm. Essayé en simulation.

### Incident du 23/11/2026 : la pince a forcé sur la table et s'est décrochée du poignet

En approchant un objet posé sur la table, la pince a appuyé sur la table ; l'ensemble pince + palonnier s'est détaché du servo
de rotation du poignet (n° 5). La pince ne tenait que par 3 vis M2,5 sur 4, avec 2,5 mm de prise.
Cause côté programme : la garde au-dessus de la table n'était que de 3 mm **par le calcul**, alors que le bras fléchit (épaule 2 à
3° sous sa cible, soit environ 2 cm au bout du bras, plus le jeu du poignet). **La garde passe à 20 mm** (`MARGE_TABLE`), et la
hauteur de prise de `aller_point` est relevée d'autant. La zone de prise à plat devient 368 à 458 mm du socle.
À faire avant de reporter du poids : remonter le palonnier (vis centrale), 4 vis M2,5 plus longues, refaire l'étalonnage du poignet.

**Descente qui sent le contact (23/11/2026, essayé en simulation).** Dans « Déplacer la pince », le bouton Descendre avance par marches
de 5 mm et relit l'effort de l'épaule, du coude et du poignet après chacune. Un saut de 10 points ou plus (`SEUIL_CONTACT`) = la
pince touche la table ou l'objet : elle remonte d'une marche et le dit en rouge, au lieu de forcer. Seuil à ajuster à l'essai.
Précision sur l'incident : c'est le **palonnier qui a quitté l'axe du servo n° 5** (dit par Nicolas), pas les vis de la pince.

## Aller à un point : premier essai réel, et inclinaison choisie toute seule (24/11/2026)

**Premier essai réel de `aller_point` (Nicolas)** : `v 13 435`, point lu à la caméra → socle +9°, épaule 0°, coude −46°, poignet +46° ;
socle arrivé en 0,5 s, pince au-dessus du point en 2,3 s. Pas encore de mesure à la règle de l'endroit où la pince arrive, ni de descente.
Un point à 339 mm a été refusé (coude à −103°, hors de ±90°) : à plat, le bras ne se pose qu'entre 368 et 458 mm.

**`v X Y` choisit maintenant l'inclinaison de la pince** (`geometrie.choisir_inclinaison`) : à plat si c'est possible, sinon −15°, −30°…
jusqu'à −90° (pointée vers le bas), la première qui marche. Hauteur de prise : celle qui laisse le point le plus bas de la pince à
22 mm de la table par le calcul, quelle que soit l'inclinaison (milieu des mâchoires à 62 mm à plat, 57 mm pointée vers le bas).
Approche : à plat, comme avant (épaule relevée de 25°) ; inclinée, à la verticale du point, 4 à 7 cm plus haut (tout près du socle,
avec une pince 5 à 15° moins raide, faute de course au poignet). `v X Y 45` impose une inclinaison.

**Zone atteinte droit devant, par le calcul : de 204 à 470 mm du socle**, sans trou (à plat de 368 à 458). Inclinaison choisie :
−90° de 205 à 235 mm, −75° jusqu'à 280, −60° jusqu'à 340, −45° vers 355, à plat de 370 à 445, −15° à 460.
Vérifié sur 919 points de la table : butées, table (22 mm au plus bas), approche au moins 3 cm au-dessus, descente sans frôler.
**Essayé sur 6 servos simulés seulement.** Limite connue : pince inclinée, les mâchoires serrent toujours de côté ; un objet de moins
de 2,5 cm de haut passe sous leur bout.

**Première descente réelle (`v 6 422` puis `d`, 24/11/2026) : deux problèmes.**
1. **Bras bloqué en bas** : `m` et `r` refusés (« la pince passerait trop près de la table »). Le bras fléchit : ses angles réels sont plus
   bas que ceux demandés, la pince se retrouvait sous la garde de 20 mm et tout trajet était refusé dès son départ. Corrigé :
   `aller_point` dégage d'abord la pince (épaule seule relevée de 15°), et `trajet_sur` accepte un trajet qui ne fait que monter.
   Essayé en simulation (épaule affaissée de 4°).
2. **Pince 7 cm trop loin** que la croix visée, alors que la croix est bien à 422 mm de l'axe du socle (mesuré par Nicolas) : la caméra
   a raison, c'est le bras qui dépasse. Cause non trouvée : longueurs du programme (120 / 161 / 200,7) jamais mesurées sur le bras
   réel, ou étalonnage d'un angle. En attente : ce qu'affiche `i` pince descendue, et les trois longueurs mesurées à la règle.

**Suite du 24/11/2026.** Après correction des mesures de la table (400 × 289, marqueur 0 à 198 et 190 mm), la pince arrive à la
bonne distance mais **4 à 5 cm trop à gauche** (l'objet se retrouve sous la branche droite). Le bras penche à gauche, mesuré au
niveau après le nouveau berceau du coude : épaule 1,8° de plus que le socle, coude +0,4°, flexion +0,4°, pince +1,2° ; cela
explique environ 2 cm. À faire : berceau à parois hautes à l'épaule, puis manchon du support de rotation, puis remesurer ;
s'il reste un écart, chercher du côté de l'alignement du zéro du socle avec le rectangle de marqueurs.

**Fin du 24/11/2026.** Berceaux à parois hautes montés au coude et à l'épaule. Nouvelles mesures au niveau : socle −1°, épaule 0°,
coude +2,4°, flexion +3°, pince −2,4° (douteuse : branches en V) — trop dispersées pour chercher au degré près. Décision : on
ÉTALONNE au lieu de redresser. Prochain essai : deux croix (vers Y 430 et Y 300), écart du milieu des mâchoires mesuré à la règle
(côté et profondeur), puis ajout d'un réglage de correction (angle du socle + décalage) dans `aller_point`.

## La caméra et le bras dans une seule fenêtre — `viser_camera.bat` (25/11/2026, demande de Nicolas)

`voir_table` et `aller_point` réunis : on **clique** sur un point de la table, le programme annonce le geste, **ENTRÉE** et le bras
se place au-dessus. Plus de X et Y à recopier. **Essayé sur 6 servos simulés et une image fabriquée, pas avec la vraie caméra.**

| Touche | Effet |
|---|---|
| clic | choisir un point (rien ne bouge) |
| ENTRÉE | y aller : pince au-dessus du point, inclinaison choisie toute seule |
| D / M | descendre sur le point / remonter |
| O / S | ouvrir / serrer |
| R, I | repos, où est la pince |
| ESPACE | ARRÊT : le geste s'arrête, le bras reste tenu |
| P, Q | photo de la table, quitter (le programme demande de tenir le bras avant de couper la force) |

- Le bras cache des marqueurs en passant au-dessus de la table : le programme garde le dernier repérage et le dit. La caméra ne
  doit pas bouger entre-temps.
- Le lanceur installe la vision (`opencv-python`) dans l'installation du bras au premier lancement : il faut Internet cette fois-là.
- `aller_point.bat` et `camera\voir_table.bat` restent utilisables séparément.

### Régler la visée sans règle (25/11/2026)

Premiers essais réels de `viser_camera` (Nicolas) : le clic, ENTRÉE et la descente fonctionnent. Lu sur ses captures, pince à plat
et descendue, en (149, 419) et (5, 420) : le milieu des mâchoires arrive **3 à 4,5 cm trop à gauche et 4 à 6 cm trop loin**
(lecture à 1,5 cm près : la pince est au-dessus de la table, la vue en biais la décale). Même écart aux deux points.

Plutôt que mesurer, on **apprend** l'écart (`correction.py`, `correction_point.json` sur le PC de Nicolas) :
pince descendue sur un repère, **flèches** (ou J gauche, L droite, U plus loin, N plus près, 5 mm par appui) jusqu'à ce qu'elle soit
pile dessus, puis **C**. La correction est gardée en « tourner le socle de tant, allonger de tant » et sert à tous les clics
suivants (moyenne des points appris voisins). 3 ou 4 points à des endroits différents ; **E deux fois** efface tout.
Essayé sur servos simulés. `aller_point.bat` (clavier seul) n'applique pas cette correction.

Piste pour la cause du « trop loin » : la longueur axe de flexion → milieu des mâchoires (200,7 mm au programme) n'a jamais été
mesurée avec la pince V4. **Mesurée par Nicolas le 25/11/2026 : 201 mm, c'est juste.** La cause du « trop loin » est donc ailleurs
(longueurs 120 et 161 non mesurées, ou zéro d'un angle) ; la correction apprise l'absorbe.
