# Tête du robot

Construite par étapes, d'abord **sur l'ordinateur** (sans moteur, sans risque), puis dans le robot.

| Étape | Ce que fait la tête | État |
|---|---|---|
| 1 | **Voir** : la webcam encadre les objets et les nomme en français | essayé sur le PC le 11/11/2026 : marche, mais 80 objets seulement → ajout de **sa propre liste** (`objets.txt`) et de la **webcam externe** |
| 2 | **Entendre** : comprendre ce qu'on lui dit (reconnaissance vocale) | **validé sur le PC le 11/11/2026** : il comprend bien (modèle « small ») |
| 3 | **Répondre** : une IA qui répond (Claude), et une voix (ElevenLabs) | **validé sur le PC le 11/11/2026** (un peu lent → accéléré le même jour) |
| 4 | **Tout relier** : voir + entendre + répondre | `robot.py` / `lancer_robot.bat`, testé ici sans clés, à essayer sur le PC |
| 5 | **Se souvenir et reconnaître les visages** | `robot.py`, testé ici sans clés, à essayer sur le PC |
| 6 | **Bouger** : 2 servos (tourner, hocher) pour regarder vers ce qu'on lui montre | à faire |

## Étape 1 : voir

Deux façons de reconnaître les objets :

| Lanceur | Modèle | Ce qu'il reconnaît | Vitesse |
|---|---|---|---|
| `lancer_vision.bat` | YOLO11n (6 Mo) | **80 objets fixes** (personne, chat, cheval, bouteille, tasse, ballon, téléphone, livre…). Un objet hors liste est confondu avec le plus proche : un rouleau de scotch devient un « frisbee », un tube de colle un « téléphone ». | rapide |
| `lancer_objets.bat` | YOLO-World (environ 360 Mo au premier lancement) | **la liste qu'on lui donne** dans `objets.txt` : rouleau de scotch, tube de colle, tournevis, plot, cheval… | plus lent, moins sûr de lui (seuil 0,15 par défaut) |

**`objets.txt`** : une ligne par objet, `nom français = nom anglais` (le modèle comprend l'anglais).
L'ouvrir avec le Bloc-notes pour ajouter ou enlever des objets, puis relancer. Plus le nom anglais
est précis, mieux c'est : « roll of adhesive tape » plutôt que « tape ».

Plus tard, pour **reconnaître à coup sûr** les objets du club (poney, licol, plot de Pony Games…),
on pourra entraîner un modèle avec quelques dizaines de photos de chaque objet.

## Brancher une webcam externe (USB)

1. Brancher la webcam sur un port USB de l'ordinateur ; attendre quelques secondes.
2. **Double-cliquer `lister_cameras.bat`** : il affiche les webcams trouvées (en général 0 = celle
   du portable, 1 = la webcam USB).
3. Les lanceurs utilisent **`--camera 1`** (webcam USB) depuis le 11/11/2026. Pour une autre webcam :
   ouvrir le lanceur avec le **Bloc-notes** (clic droit → Modifier), changer le numéro, enregistrer.

## Étape 2 : entendre

Reconnaissance vocale **Whisper** (faster-whisper), en français, **sur l'ordinateur** : gratuite et
sans internet une fois le modèle téléchargé (environ 480 Mo au premier lancement).

**Double-cliquer `lancer_ecoute.bat`.** Il mesure d'abord 2 secondes de bruit de fond (**rester
silencieux**), puis écoute en continu : dès qu'on parle et qu'on se tait, il écrit
« Tu as dit : … ». **Ctrl + C** pour arrêter.

- Autre micro (micro USB, casque) : `lister_micros.bat` donne les numéros, puis ajouter
  `--micro N` dans `lancer_ecoute.bat` (comme pour la webcam).
- Trop lent : `--modele base` (plus rapide, moins précis). Pas assez précis : `--modele medium`.
- Il se déclenche tout seul sur des bruits : `--seuil 0.03` (plus haut = il faut parler plus fort).

Testé ici sur un enregistrement de voix de synthèse française : phrase comprise mot pour mot
(« Bonjour robot, prends le rouleau de scotch et pose-le dans la boîte bleue. »), et deux phrases
séparées par un silence bien découpées en deux. Pas encore essayé avec un vrai micro.

**Clés d'API** (ElevenLabs pour la voix à l'étape 3, Anthropic pour l'IA) : elles iront dans un fichier
`cles.txt` **sur le PC seulement**, jamais dans une conversation ni sur GitHub (le fichier est exclu).

## Étape 3 : répondre — parler avec Câlin

Le robot s'appelle **Câlin**, comme la borne d'accueil du club : même caractère (chaleureux, phrases
courtes, adapté aux enfants, uniquement en français). Il sait qu'il est un robot en construction au
club, qu'il ne peut encore rien attraper, et renvoie vers l'accueil pour les tarifs et le planning.
On réunira la borne et le robot plus tard.

**Double-cliquer `lancer_conversation.bat`.** Il charge l'écoute, mesure le bruit de fond (rester
silencieux 2 secondes), dit bonjour, puis : **tu parles → il écrit ta phrase → Claude répond → la voix
la dit**. Pendant qu'il parle, il n'écoute pas (sinon il s'entendrait). **« Au revoir »** ou
**Ctrl + C** pour arrêter.

- **Clés** : le programme cherche, dans l'ordre, `C:\projet robot\cles_robot.txt`,
  `C:\projet robot\cles.txt`, `C:\projet robot\cles.env`, `C:\projet robot\.env`, puis
  `C:\Users\nicol\cles_robot.txt`. Il écrit au démarrage lequel il a trouvé. Format : voir
  `cles_exemple.txt` (une clé seule sur une ligne est aussi reconnue).
- **Voix** : ElevenLabs si la clé est là, sinon la voix gratuite de Windows. Pour forcer la voix de
  Windows : ajouter `--voix-pc`. Pour une autre voix ElevenLabs : ajouter une ligne
  `ELEVENLABS_VOICE_ID=...` dans le fichier des clés (l'identifiant se copie dans la bibliothèque de
  voix du site ElevenLabs).
- **Sans micro** : `--clavier` pour taper ses phrases.
- **IA** : Claude Sonnet 5.5 par défaut (comme la borne), réflexion courte (`EFFORT = 'low'`), réglages en
  tête de `parler.py` ; `--ia opus` pour Claude Opus 5.5, plus puissant mais plus lent. Si une demande est refusée par le modèle, l'API passe la main à un autre modèle dans le
  même appel (« fallbacks »).

Testé ici sans les clés : lecture du fichier des clés, filtre des phrases fantômes de Whisper,
message clair si la clé est fausse. **Pas encore testé** : une vraie réponse de Claude et la voix
ElevenLabs.

## Étape 4 : tout relier — `lancer_robot.bat`

**Câlin complet** : la caméra tourne en continu (fenêtre « Oeil de Calin » avec les cadres), le micro
écoute, la voix répond.

- À **chaque phrase**, Câlin reçoit la liste de ce que la détection automatique repère
  (« bus, personne ×4 »), affichée aussi dans la fenêtre noire.
- Si la phrase parle de **ce qu'il voit** (« qu'est-ce que tu vois ? », « c'est quoi ça ? »,
  « regarde ce que je tiens », « combien… », « quelle couleur… »), il envoie aussi **la photo** à
  Claude, qui reconnaît presque n'importe quel objet : bien plus juste que le petit modèle de
  détection (le rouleau de scotch ne sera plus un frisbee). La fenêtre noire indique « + photo envoyée ».
- **Webcam USB (n° 1) par défaut** dans tous les lanceurs et programmes ; celle du portable : `--camera 0`.
  Sa propre liste d'objets : `--objets objets.txt`.

### Plus rapide (11/11/2026)

- La réponse est **dite phrase par phrase pendant que Claude écrit la suite** : la première phrase
  arrive bien plus tôt.
- Voix ElevenLabs (11/11/2026, la voix rapide sonnait mal et hachée) : modèle **ElevenLabs v4**
  (`eleven_v4`, choix de Nicolas), `--voix-rapide` pour **v4 turbo** (`eleven_v4_turbo`, faite pour la
  conversation). Si le modèle refuse le contexte d'intonation ou la langue, le programme le dit une fois
  et continue sans (non vérifié dans la documentation d'ElevenLabs, inaccessible d'ici). Autres modèles
  possibles dans `parler.py` : `eleven_multilingual_v2`, `eleven_flash_v2_5` ; le son commence après
  **0,8 s de réserve** (plus de trous si internet ralentit) ; la 1re phrase part seule, **les suivantes
  sont regroupées** et le texte déjà dit sert de contexte (intonation continue) ; **la caméra suspend
  ses calculs pendant que Câlin parle**. Autre voix : ligne `ELEVENLABS_VOICE_ID=...` dans le fichier
  des clés (identifiant copié dans la bibliothèque de voix du site ElevenLabs).
- Fin de phrase détectée après **0,6 s** de silence au lieu de 0,8 s.
- **Transcription (11/11/2026, trop longue entre la fin de la phrase et le texte)** : par défaut
  **ElevenLabs Scribe v2**, dans le nuage, avec la même clé que la voix ; le son est envoyé brut
  (16 bits, 16 kHz), le format le plus rapide d'après ElevenLabs, et le processeur du PC reste libre.
  `--ecoute whisper` pour revenir à Whisper sur le PC (gratuit, hors ligne), désormais plus rapide
  (recherche simple au lieu de 5 pistes : 2,2 s → 1,7 s ici, même phrase comprise) et avec la caméra
  en pause pendant qu'il transcrit. Anthropic ne propose pas de transcription de la voix, à ma
  connaissance ; OpenAI en propose une, mais il faudrait un compte de plus. `lancer_ecoute.bat` (étape 2)
  reste sur Whisper.
- **IA par défaut : Claude Sonnet 5.5** (choix de Nicolas, 11/11/2026), celle de la borne : plus rapide et
  moins chère. `--ia opus` pour Claude Opus 5.5, plus puissant mais plus lent.
- Après chaque réponse, une ligne donne les temps : *compris en … s · 1er mot de l'IA … s ·
  1re phrase dite à … s · réponse complète … s*. Elle dit où le temps se perd.

**Historique** : la conversation garde le texte des 20 derniers messages, sans la réflexion interne
du modèle ni les photos (remplacées par « [photo de la caméra] »). Raccourcir un historique qui
contient la réflexion du modèle peut être refusé par l'API sur les comptes récents ; c'est pour ça
qu'elle n'est pas gardée.

Testé ici sans les clés, avec une photo à la place de la webcam et un faux Claude : la photo part
seulement sur une question visuelle, les phrases sont dites une à une, l'historique reste borné
(20 messages après 32 tours) et sans photo. **Pas encore testé** : avec la vraie webcam, la vraie IA
et la vraie voix.

## Étape 5 : mémoire et visages (dans `lancer_robot.bat`)

Claude a maintenant 4 **outils** qu'il déclenche lui-même pendant la conversation :

| Ce qu'on lui dit | Ce qu'il fait |
|---|---|
| « Je m'appelle Paul, j'adore les Pony Games » | **retenir** : garde « (Paul) aime les Pony Games » pour les prochaines fois |
| « Oublie tout ce que tu sais sur moi » | **oublier_souvenirs** : efface les souvenirs de la personne |
| « Retiens mon visage, je m'appelle Paul » | **apprendre_visage** : prend 5 images du plus grand visage en 2,5 s (rester face à la caméra, de près) |
| « Oublie mon visage » | **oublier_visage** : efface le visage appris |

Ensuite, la fenêtre de la caméra encadre les visages en **vert avec le prénom** (gris : inconnu), et
Câlin appelle les gens par leur prénom. Au démarrage, il relit ses souvenirs.

**Données personnelles (RGPD) — règles écrites dans la personnalité de Câlin :**
- un visage est une donnée **biométrique** : Câlin ne l'apprend **que si la personne le demande
  elle-même**, jamais pour quelqu'un d'autre, jamais de sa propre initiative, **jamais pour un enfant** ;
- il ne retient **ni santé, ni adresse, ni téléphone, ni argent, ni secret** ;
- tout est rangé **sur le PC, hors du projet** : `C:\projet robot\calin_donnees\` (souvenirs dans
  `memoire.json`, visages dans `visages\` — des nombres, pas de photo). Jamais sur GitHub.
  **Supprimer ce dossier efface tout.**
- **Au club**, avant de mettre Câlin devant le public : couper la reconnaissance des visages
  (`--sans-visages`) et revoir la mémoire avec un conseil juridique.

Modèles de visages (OpenCV YuNet + SFace, environ 38 Mo) téléchargés au premier lancement dans
`tete\modeles\`. Testé ici avec une fausse IA et des photos : visage appris puis reconnu (l'autre
visage reste inconnu), fait retenu puis relu au démarrage suivant, visage oublié et fichier effacé.
**Pas encore testé** : avec la vraie webcam (lumière, distance) et la vraie IA, qui doit décider
seule d'utiliser ses outils.

### Installation sur le PC (une seule fois)

1. **Python** : télécharger Python 3.12 sur python.org, lancer l'installation et **cocher
   « Add python.exe to PATH »** en bas de la première fenêtre.
2. **Récupérer le projet** : sur la page GitHub du dépôt, bouton vert **Code → Download ZIP**,
   puis clic droit sur le fichier → **Extraire tout**.
3. Dans le dossier `tete`, **double-cliquer `installer.bat`**. Il télécharge ce qu'il faut
   (environ 10 minutes et 1 à 2 Go). Attendre « Installation terminée ». **À relancer après chaque
   mise à jour du dossier** (il n'ajoute que ce qui manque).

### Lancer

**Double-cliquer `lancer_vision.bat`** (ou `lancer_objets.bat`). Une fenêtre montre la webcam avec des cadres et des noms ;
la fenêtre noire écrit « Je vois : … » chaque fois que ça change. **Touche Q** pour quitter.

- Plus ou moins prudent : `--seuil 0.3` (voit plus de choses, se trompe plus) à `--seuil 0.7`
- Analyser une photo : `lancer_vision.bat --image chemin\de\la\photo.jpg`

### Si ça ne marche pas

| Message | Quoi faire |
|---|---|
| `'py' n'est pas reconnu` | Python n'est pas installé, ou la case « Add to PATH » n'était pas cochée : réinstaller Python |
| `Webcam 0 introuvable` | fermer Teams, Zoom ou l'appareil photo de Windows ; essayer `--camera 1` ; Paramètres Windows → Confidentialité → Caméra : autoriser les applications de bureau |
| Image très lente (moins de 5 images/s) | normal sur un vieux portable ; ça reste utilisable |
