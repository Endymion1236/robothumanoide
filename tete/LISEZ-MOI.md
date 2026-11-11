# Tête du robot

Construite par étapes, d'abord **sur l'ordinateur** (sans moteur, sans risque), puis dans le robot.

| Étape | Ce que fait la tête | État |
|---|---|---|
| 1 | **Voir** : la webcam encadre les objets et les nomme en français | programme prêt (`vision.py`), testé sur une photo, à essayer sur le PC |
| 2 | **Entendre** : comprendre ce qu'on lui dit (reconnaissance vocale) | à faire |
| 3 | **Répondre** : une IA qui répond, et une voix | à faire |
| 4 | **Tout relier** : « qu'est-ce que tu vois ? » → réponse à voix haute | à faire |
| 5 | **Bouger** : 2 servos (tourner, hocher) pour regarder vers ce qu'on lui montre | à faire |

## Étape 1 : voir

Modèle **YOLO11n** (Ultralytics) : il reconnaît 80 sortes d'objets courants (personne, chat, chien,
cheval, bouteille, tasse, ballon, téléphone, livre…), téléchargé tout seul au premier lancement
(environ 6 Mo). Il ne connaît pas encore les objets propres au club (poney, licol, plot de Pony
Games…) : on pourra lui apprendre plus tard avec des photos.

### Installation sur le PC (une seule fois)

1. **Python** : télécharger Python 3.12 sur python.org, lancer l'installation et **cocher
   « Add python.exe to PATH »** en bas de la première fenêtre.
2. **Récupérer le projet** : sur la page GitHub du dépôt, bouton vert **Code → Download ZIP**,
   puis clic droit sur le fichier → **Extraire tout**.
3. Dans le dossier `tete`, **double-cliquer `installer.bat`**. Il télécharge ce qu'il faut
   (environ 10 minutes et 1 à 2 Go). Attendre « Installation terminée ».

### Lancer

**Double-cliquer `lancer_vision.bat`.** Une fenêtre montre la webcam avec des cadres et des noms ;
la fenêtre noire écrit « Je vois : … » chaque fois que ça change. **Touche Q** pour quitter.

- Autre webcam (par exemple une webcam USB branchée en plus) : `lancer_vision.bat --camera 1`
- Plus ou moins prudent : `--seuil 0.3` (voit plus de choses, se trompe plus) à `--seuil 0.7`
- Analyser une photo : `lancer_vision.bat --image chemin\de\la\photo.jpg`

### Si ça ne marche pas

| Message | Quoi faire |
|---|---|
| `'py' n'est pas reconnu` | Python n'est pas installé, ou la case « Add to PATH » n'était pas cochée : réinstaller Python |
| `Webcam 0 introuvable` | fermer Teams, Zoom ou l'appareil photo de Windows ; essayer `--camera 1` ; Paramètres Windows → Confidentialité → Caméra : autoriser les applications de bureau |
| Image très lente (moins de 5 images/s) | normal sur un vieux portable ; ça reste utilisable |
