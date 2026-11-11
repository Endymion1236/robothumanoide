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
servo trop chaud → refus. **Pas encore testé sur le vrai servo.**

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
