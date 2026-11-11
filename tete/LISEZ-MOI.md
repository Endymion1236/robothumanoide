# Tête du robot

Construite par étapes, d'abord **sur l'ordinateur** (sans moteur, sans risque), puis dans le robot.

| Étape | Ce que fait la tête | État |
|---|---|---|
| 1 | **Voir** : la webcam encadre les objets et les nomme en français | essayé sur le PC le 11/11/2026 : marche, mais 80 objets seulement → ajout de **sa propre liste** (`objets.txt`) et de la **webcam externe** |
| 2 | **Entendre** : comprendre ce qu'on lui dit (reconnaissance vocale) | à faire |
| 3 | **Répondre** : une IA qui répond, et une voix | à faire |
| 4 | **Tout relier** : « qu'est-ce que tu vois ? » → réponse à voix haute | à faire |
| 5 | **Bouger** : 2 servos (tourner, hocher) pour regarder vers ce qu'on lui montre | à faire |

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
3. Ouvrir `lancer_vision.bat` ou `lancer_objets.bat` avec le **Bloc-notes** (clic droit → Modifier
   ou Ouvrir avec), remplacer **`--camera 0`** par **`--camera 1`**, enregistrer, relancer.

### Installation sur le PC (une seule fois)

1. **Python** : télécharger Python 3.12 sur python.org, lancer l'installation et **cocher
   « Add python.exe to PATH »** en bas de la première fenêtre.
2. **Récupérer le projet** : sur la page GitHub du dépôt, bouton vert **Code → Download ZIP**,
   puis clic droit sur le fichier → **Extraire tout**.
3. Dans le dossier `tete`, **double-cliquer `installer.bat`**. Il télécharge ce qu'il faut
   (environ 10 minutes et 1 à 2 Go). Attendre « Installation terminée ».

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
