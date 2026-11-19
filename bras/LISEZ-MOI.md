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
