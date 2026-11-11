"""Reconnaissance des visages de Câlin (OpenCV : détecteur YuNet + reconnaissance SFace, sur le PC).

Données biométriques : un visage n'est appris QUE si la personne le demande elle-même, et
« oublie mon visage » l'efface. Chaque visage appris = un fichier calin_donnees/visages/<nom>.npy
(des nombres, pas de photo), hors du projet. Supprimer le dossier efface tout."""
import re, urllib.request
from pathlib import Path
import cv2
import numpy as np

MODELES = {
    'detection': ('face_detection_yunet_2023mar.onnx',
                  'https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx'),
    'reconnaissance': ('face_recognition_sface_2021dec.onnx',
                       'https://huggingface.co/opencv/face_recognition_sface/resolve/main/face_recognition_sface_2021dec.onnx'),
}
SEUIL = 0.40          # ressemblance minimale (cosinus) ; OpenCV conseille 0,363 — un peu plus prudent ici
TAILLE_MIN = 60       # en pixels : un visage plus petit (trop loin) n'est ni appris ni reconnu

def modele(nom, dossier):
    fichier, url = MODELES[nom]
    chemin = Path(dossier) / fichier
    if not chemin.is_file():
        chemin.parent.mkdir(parents=True, exist_ok=True)
        print(f'Téléchargement du modèle de visages « {fichier} »...')
        urllib.request.urlretrieve(url, chemin)
    return str(chemin)

def nom_de_fichier(nom):
    return re.sub(r'[^\w-]+', '_', nom.strip().lower()).strip('_') or 'inconnu'

class Visages:
    def __init__(self, dossier_visages, dossier_modeles):
        self.dossier = Path(dossier_visages); self.dossier.mkdir(parents=True, exist_ok=True)
        self.detecteur = cv2.FaceDetectorYN.create(modele('detection', dossier_modeles), '', (320, 320), 0.8)
        self.reconnaisseur = cv2.FaceRecognizerSF.create(modele('reconnaissance', dossier_modeles), '')
        self.connus = {}                                          # nom affiché -> tableau d'empreintes
        for f in self.dossier.glob('*.npy'):
            donnees = np.load(f, allow_pickle=False)
            nom_txt = f.with_suffix('.txt')
            self.connus[nom_txt.read_text(encoding='utf-8').strip() if nom_txt.is_file() else f.stem] = donnees

    def detecter(self, image):
        h, w = image.shape[:2]
        self.detecteur.setInputSize((w, h))
        _, visages = self.detecteur.detect(image)
        return [] if visages is None else [v for v in visages if min(v[2], v[3]) >= TAILLE_MIN]

    def empreinte(self, image, visage):
        aligne = self.reconnaisseur.alignCrop(image, visage)
        e = self.reconnaisseur.feature(aligne).flatten()
        return e / np.linalg.norm(e)

    def qui(self, empreinte):
        """Nom de la personne la plus ressemblante, ou None ; et la ressemblance."""
        meilleur, score = None, -1.0
        for nom, empreintes in self.connus.items():
            s = float(np.max(empreintes @ empreinte))
            if s > score:
                meilleur, score = nom, s
        return (meilleur, score) if score >= SEUIL else (None, score)

    def reconnaitre(self, image):
        """Liste de (cadre x,y,l,h, nom ou None, ressemblance) pour chaque visage de l'image."""
        res = []
        for v in self.detecter(image):
            nom, score = self.qui(self.empreinte(image, v))
            res.append((tuple(int(x) for x in v[:4]), nom, score))
        return res

    def apprendre(self, nom, empreintes):
        """Ajoute des empreintes à une personne (crée la personne si besoin)."""
        e = np.vstack([self.connus[nom]] + list(empreintes)) if nom in self.connus else np.vstack(empreintes)
        f = self.dossier / nom_de_fichier(nom)
        np.save(f.with_suffix('.npy'), e); f.with_suffix('.txt').write_text(nom, encoding='utf-8')
        self.connus[nom] = e

    def oublier(self, nom):
        cible = next((n for n in self.connus if n.lower() == nom.strip().lower()), None)
        if cible is None:
            return False
        f = self.dossier / nom_de_fichier(cible)
        for suffixe in ('.npy', '.txt'):
            f.with_suffix(suffixe).unlink(missing_ok=True)
        del self.connus[cible]
        return True
