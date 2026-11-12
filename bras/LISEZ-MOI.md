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
2. Butées : il vérifie 1663–2433 (propose de les régler sinon). Si le servo est **hors** de ses butées,
   l'engrenage A est mal posé : il s'arrête et dit quoi faire.
3. **Premier lancement** : rien entre les doigts. La pince va au milieu puis bouge un peu ; répondre
   **o** si les mâchoires se sont **écartées**, **f** si elles se sont **rapprochées**. Retenu dans
   `sens_pince.json` (supprimer ce fichier pour redemander).
4. Commandes : **c** milieu (≈ 71 mm) · **o** ouvrir en grand (110 mm) · **s** serrer doucement (force 20 %)
   · **S** serrer plus fort (35 %) · **f** fermer à vide · **l** lâcher (libre) · **i** infos · **q** quitter.
   Plusieurs d'un coup : `o s`.
5. **Serrer** avance avec une force limitée et **s'arrête tout seul** sur l'objet (immobile + effort) ;
   il affiche la largeur estimée de l'objet. Ne pas laisser un objet serré plusieurs minutes.

Toutes les autres sécurités du coude restent (butées, chaleur, blocage ; force jamais au-delà de 50 % pour la pince).
Testé ici sur un servo simulé (sans objet, gobelet de 50 mm) ; **pas encore sur la vraie pince.**
