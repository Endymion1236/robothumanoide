"""Tête du robot — étape 1 : VOIR.

Filme avec la webcam et encadre les objets reconnus, avec leur nom en français.
Modèle : YOLO11n (Ultralytics), 80 sortes d'objets courants, téléchargé tout seul au premier lancement.

Utilisation :  python vision.py              (webcam n° 0)
               python vision.py --camera 1   (autre webcam)
               python vision.py --image photo.jpg   (une photo au lieu de la webcam)
Touche Q (ou Échap) pour quitter.
"""
import argparse, sys, time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

# Les 80 objets du modèle, dans l'ordre du modèle, en français.
NOMS_FR = [
    'personne', 'vélo', 'voiture', 'moto', 'avion', 'bus', 'train', 'camion', 'bateau', 'feu tricolore',
    'bouche d\'incendie', 'panneau stop', 'parcmètre', 'banc', 'oiseau', 'chat', 'chien', 'cheval', 'mouton', 'vache',
    'éléphant', 'ours', 'zèbre', 'girafe', 'sac à dos', 'parapluie', 'sac à main', 'cravate', 'valise', 'frisbee',
    'skis', 'snowboard', 'ballon', 'cerf-volant', 'batte de baseball', 'gant de baseball', 'skateboard', 'planche de surf',
    'raquette de tennis', 'bouteille', 'verre à vin', 'tasse', 'fourchette', 'couteau', 'cuillère', 'bol', 'banane',
    'pomme', 'sandwich', 'orange', 'brocoli', 'carotte', 'hot-dog', 'pizza', 'donut', 'gâteau', 'chaise', 'canapé',
    'plante en pot', 'lit', 'table', 'toilettes', 'télévision', 'ordinateur portable', 'souris', 'télécommande',
    'clavier', 'téléphone', 'micro-ondes', 'four', 'grille-pain', 'évier', 'réfrigérateur', 'livre', 'horloge', 'vase',
    'ciseaux', 'ours en peluche', 'sèche-cheveux', 'brosse à dents',
]
COULEURS = [(231, 76, 60), (52, 152, 219), (46, 204, 113), (241, 196, 15), (155, 89, 182), (230, 126, 34), (26, 188, 156)]

def police(taille):
    """Police avec accents : Arial sous Windows, DejaVu sous Linux, sinon la police par défaut."""
    for nom in ('arial.ttf', 'DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(nom, taille)
        except OSError:
            pass
    return ImageFont.load_default()

def annoter(image_bgr, resultat, seuil, fonte):
    """Dessine les cadres et les noms ; renvoie l'image et la liste des objets vus."""
    img = Image.fromarray(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(img)
    vus = []
    for boite in resultat.boxes:
        conf = float(boite.conf)
        if conf < seuil:
            continue
        k = int(boite.cls)
        nom = NOMS_FR[k] if k < len(NOMS_FR) else resultat.names[k]
        x1, y1, x2, y2 = map(int, boite.xyxy[0])
        c = COULEURS[k % len(COULEURS)]
        d.rectangle([x1, y1, x2, y2], outline=c, width=3)
        texte = f'{nom} {conf:.0%}'
        l, t, r, b = d.textbbox((0, 0), texte, font=fonte)
        y0 = max(0, y1 - (b - t) - 8)
        d.rectangle([x1, y0, x1 + (r - l) + 10, y0 + (b - t) + 8], fill=c)
        d.text((x1 + 5, y0 + 2), texte, fill=(255, 255, 255), font=fonte)
        vus.append(nom)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR), vus

def main():
    ap = argparse.ArgumentParser(description='Tête du robot : reconnaissance d\'objets')
    ap.add_argument('--camera', type=int, default=0, help='numéro de la webcam (0 = celle du portable)')
    ap.add_argument('--image', help='analyser une photo au lieu de la webcam')
    ap.add_argument('--seuil', type=float, default=0.5, help='confiance minimale (0 à 1)')
    ap.add_argument('--sortie', help='avec --image : enregistrer le résultat dans ce fichier')
    a = ap.parse_args()

    print('Chargement du modèle (le premier lancement le télécharge, environ 6 Mo)...')
    modele = YOLO('yolo11n.pt')
    fonte = police(20)

    if a.image:
        image = cv2.imread(a.image)
        if image is None:
            sys.exit(f'Image introuvable : {a.image}')
        res = modele(image, verbose=False)[0]
        image, vus = annoter(image, res, a.seuil, fonte)
        print('Objets vus :', ', '.join(vus) if vus else 'aucun')
        if a.sortie:
            cv2.imwrite(a.sortie, image); print('Résultat enregistré :', a.sortie)
        else:
            cv2.imshow('Tete du robot', image); cv2.waitKey(0)
        return

    cam = cv2.VideoCapture(a.camera, cv2.CAP_DSHOW if sys.platform == 'win32' else cv2.CAP_ANY)
    if not cam.isOpened():
        sys.exit(f'Webcam {a.camera} introuvable. Essayer --camera 1, ou fermer les autres logiciels qui l\'utilisent.')
    print('Webcam ouverte. Touche Q pour quitter.')
    derniere_liste, t0 = None, time.time()
    while True:
        ok, image = cam.read()
        if not ok:
            print('La webcam ne renvoie plus d\'image.'); break
        res = modele(image, verbose=False)[0]
        image, vus = annoter(image, res, a.seuil, fonte)
        ips = 1 / max(time.time() - t0, 1e-6); t0 = time.time()
        cv2.putText(image, f'{ips:.0f} images/s', (10, 25), cv2.FONT_HERSHEY_SIMPLEX, .7, (255, 255, 255), 2)
        liste = sorted(set(vus))
        if liste != derniere_liste:             # n'écrit que quand ce qu'il voit change
            print('Je vois :', ', '.join(liste) if liste else 'rien de connu')
            derniere_liste = liste
        cv2.imshow('Tete du robot - Q pour quitter', image)
        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q'), 27):
            break
    cam.release(); cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
