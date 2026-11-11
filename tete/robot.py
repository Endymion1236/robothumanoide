"""Tête du robot — tout câblé : VOIR + ENTENDRE + RÉPONDRE.

La caméra tourne en continu (fenêtre avec les cadres) et sait à tout moment ce qu'elle détecte.
À chaque phrase, Câlin reçoit cette liste ; si la question parle de ce qu'il voit (« qu'est-ce que
tu vois ? », « c'est quoi ça ? », « regarde »…), il reçoit aussi la PHOTO, et Claude la décrit :
bien plus juste que le petit modèle de détection.

Utilisation :  python robot.py                       (webcam 0, micro, voix)
               python robot.py --camera 1            (webcam USB)
               python robot.py --objets objets.txt   (détection de SA liste d'objets)
               python robot.py --clavier --muet      (essai sans micro ni voix)
               + toutes les options de parler.py (--ia sonnet, --voix-pc, --micro N…)
"""
import argparse, re, sys, threading, time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
import parler
from donnees_perso import dossier_perso
from memoire import Memoire
from parler import Cerveau, Bouche, creer_voix, options_communes, cles_ou_quitter, afficher_durees, MODELES_IA, MOTS_FIN

PERSONNALITE_ROBOT = parler.PERSONNALITE + """

Ta caméra : avant chaque phrase du visiteur, une ligne entre crochets te dit ce que ta détection automatique \
repère en ce moment (elle se trompe souvent et ne connaît que des objets courants). Quand une photo est jointe, \
c'est ce que ta caméra voit à l'instant : fie-toi à la photo plutôt qu'à la liste. Parle de ce que tu vois \
simplement, comme un robot curieux, sans décrire tout le décor. Ne commente pas la caméra si on ne t'en parle pas.

Visages : la ligne entre crochets dit aussi quels visages tu reconnais. Appelle les gens par leur prénom quand \
tu les reconnais. Pour apprendre un visage, utilise l'outil apprendre_visage UNIQUEMENT si la personne le \
demande elle-même, pour elle-même, et dit son prénom (« retiens mon visage, je m'appelle Paul »). Jamais pour \
quelqu'un d'autre, jamais de ta propre initiative, et jamais pour un enfant : dans ce cas, explique gentiment \
que c'est réservé aux adultes. Si quelqu'un demande d'oublier son visage, utilise oublier_visage.

Mémoire : utilise l'outil retenir pour garder un fait utile et durable qu'une personne te confie sur elle \
(prénom, âge, poney ou activité préférés, ce qu'elle construit, ce qu'elle aime) ou ce qu'on te demande de \
retenir. Jamais de santé, d'adresse, de téléphone, d'argent ni de secret. Si quelqu'un demande que tu oublies \
ce que tu sais sur lui, utilise oublier_souvenirs. Quand tu utilises un outil, dis aussi une courte phrase."""

OUTILS = [
    {'name': 'retenir', 'description': 'Garder en mémoire, pour les prochaines conversations, un fait court et durable.',
     'input_schema': {'type': 'object', 'properties': {
         'fait': {'type': 'string', 'description': 'le fait, en une phrase courte, ex. « aime les Pony Games »'},
         'personne': {'type': 'string', 'description': 'prénom de la personne concernée, ou chaîne vide'}},
         'required': ['fait', 'personne'], 'additionalProperties': False}},
    {'name': 'apprendre_visage', 'description': 'Apprendre le visage de la personne face à la caméra, qui l\'a demandé elle-même.',
     'input_schema': {'type': 'object', 'properties': {'nom': {'type': 'string', 'description': 'son prénom'}},
                      'required': ['nom'], 'additionalProperties': False}},
    {'name': 'oublier_visage', 'description': 'Effacer définitivement le visage appris d\'une personne, à sa demande.',
     'input_schema': {'type': 'object', 'properties': {'nom': {'type': 'string'}},
                      'required': ['nom'], 'additionalProperties': False}},
    {'name': 'oublier_souvenirs', 'description': 'Effacer tous les souvenirs gardés sur une personne, à sa demande.',
     'input_schema': {'type': 'object', 'properties': {'nom': {'type': 'string'}},
                      'required': ['nom'], 'additionalProperties': False}},
]
for o in OUTILS:                       # réponses en flux : entrées vérifiées par le programme (Cerveau)
    o['strict'] = True; o['eager_input_streaming'] = True

# Mots qui déclenchent l'envoi de la photo à l'IA
QUESTION_VISUELLE = re.compile(
    r"\b(vois|voir|voit|regarde|regarder|montre|caméra|photo|devant toi|reconnais|c'est quoi|qu'est-ce que c'est|"
    r"qu'est ce que c'est|combien|couleur|tiens|je tiens|dans ma main|comment je suis|qui est là)\b", re.I)

class Oeil(threading.Thread):
    """Caméra en tâche de fond : affiche la fenêtre, détecte les objets ~3 fois par seconde."""
    def __init__(self, camera=0, objets=None, image=None, fenetre=True, visages=None):
        super().__init__(daemon=True)
        self.camera, self.objets, self.image, self.fenetre, self.visages = camera, objets, image, fenetre, visages
        self.verrou_visages, self.visages_vus = threading.Lock(), []
        self.verrou, self.derniere_image, self.noms_vus = threading.Lock(), None, []
        self.pret, self.erreur, self.arret = threading.Event(), None, False

    def run(self):
        try:
            import vision
            if self.objets:
                from ultralytics import YOLOWorld
                noms, anglais = vision.lire_objets(self.objets)
                modele = YOLOWorld('yolov8s-worldv2.pt'); modele.set_classes(anglais); seuil = 0.15
            else:
                modele, noms, seuil = vision.YOLO('yolo11n.pt'), vision.NOMS_FR, 0.5
            fonte = vision.police(20)
            if self.image:
                fixe = cv2.imread(self.image)
                if fixe is None:
                    raise RuntimeError(f'image introuvable : {self.image}')
                lire = lambda: (True, fixe.copy())
            else:
                cam = cv2.VideoCapture(self.camera, cv2.CAP_DSHOW if sys.platform == 'win32' else cv2.CAP_ANY)
                if not cam.isOpened():
                    raise RuntimeError(f'webcam {self.camera} introuvable')
                lire = cam.read
            resultat, t_detection, t_visages = None, 0.0, 0.0
            while not self.arret:
                ok, image = lire()
                if not ok:
                    raise RuntimeError('la webcam ne renvoie plus d\'image')
                calculer = not parler.PAROLE.is_set()     # pendant que Câlin parle, le processeur va au son
                if calculer and time.time() - t_detection > 0.33:   # ~3 détections par seconde : laisse du calcul à l'écoute
                    resultat, t_detection = modele(image, verbose=False)[0], time.time()
                if calculer and self.visages and time.time() - t_visages > 0.5:   # visages 2 fois par seconde
                    with self.verrou_visages:
                        self.visages_vus = self.visages.reconnaitre(image)
                    t_visages = time.time()
                annotee, vus = vision.annoter(image, resultat, seuil, fonte, noms)
                annotee = self._dessiner_visages(annotee, fonte)
                with self.verrou:
                    self.derniere_image, self.noms_vus = image, vus
                self.pret.set()
                if self.fenetre:
                    cv2.imshow('Oeil de Calin', annotee)
                    cv2.waitKey(1)
                else:
                    time.sleep(0.03)
        except Exception as e:
            self.erreur = str(e); self.pret.set()

    def _dessiner_visages(self, image, fonte):
        with self.verrou_visages:
            vus = list(self.visages_vus)
        if not vus:
            return image
        img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(img)
        for (x, y, l, h), nom, _ in vus:
            c = (46, 204, 113) if nom else (149, 165, 166)
            d.rectangle([x, y, x + l, y + h], outline=c, width=3)
            d.text((x + 3, y + h + 3), nom or 'inconnu', fill=c, font=fonte)
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    def resume(self):
        with self.verrou:
            vus = list(self.noms_vus)
        if vus:
            compte = {n: vus.count(n) for n in dict.fromkeys(vus)}
            texte = 'détection automatique (peut se tromper) : ' + ', '.join(f'{n} ×{k}' if k > 1 else n for n, k in compte.items())
        else:
            texte = 'détection automatique : rien de reconnu'
        if self.visages:
            with self.verrou_visages:
                faces = list(self.visages_vus)
            connus = sorted({n for _, n, _ in faces if n})
            inconnus = sum(1 for _, n, _ in faces if not n)
            morceaux = connus + ([f'{inconnus} visage(s) inconnu(s)'] if inconnus else [])
            texte += ' ; visages : ' + (', '.join(morceaux) if morceaux else 'aucun')
        return f'[Caméra, {texte}]'

    def capturer_empreintes(self, nombre=5, duree=2.5):
        """Empreintes du plus grand visage, prises sur plusieurs images (la personne bouge un peu : plus fiable)."""
        empreintes, fin = [], time.time() + duree
        while len(empreintes) < nombre and time.time() < fin:
            with self.verrou:
                image = None if self.derniere_image is None else self.derniere_image.copy()
            if image is not None:
                with self.verrou_visages:
                    faces = self.visages.detecter(image)
                    if faces:
                        empreintes.append(self.visages.empreinte(image, max(faces, key=lambda v: v[2] * v[3])))
            time.sleep(duree / nombre)
        return empreintes

    def photo_jpeg(self, cote_max=1024):
        with self.verrou:
            image = None if self.derniere_image is None else self.derniere_image.copy()
        if image is None:
            return None
        h, w = image.shape[:2]
        if max(h, w) > cote_max:
            f = cote_max / max(h, w); image = cv2.resize(image, (int(w*f), int(h*f)))
        ok, jpeg = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return jpeg.tobytes() if ok else None

def main():
    ap = argparse.ArgumentParser(description='Tête du robot : voir, entendre, répondre')
    options_communes(ap)
    ap.add_argument('--camera', type=int, default=1, help='numéro de la webcam : 1 = webcam USB (défaut), 0 = celle du portable')
    ap.add_argument('--objets', help='détecter sa propre liste d\'objets (objets.txt)')
    ap.add_argument('--image', help='une photo fixe à la place de la webcam (pour essayer)')
    ap.add_argument('--sans-fenetre', action='store_true', help='ne pas afficher la fenêtre de la caméra')
    ap.add_argument('--sans-visages', action='store_true', help='ne pas reconnaître les visages')
    a = ap.parse_args()

    cles = cles_ou_quitter()
    donnees = dossier_perso()
    print('Souvenirs et visages rangés dans :', donnees)
    memoire = Memoire(donnees / 'memoire.json')
    visages = None
    if not a.sans_visages:
        try:
            from visages import Visages
            visages = Visages(donnees / 'visages', Path(__file__).resolve().parent / 'modeles')
            print('Visages connus :', ', '.join(visages.connus) or 'aucun')
        except Exception as e:
            print(f'Reconnaissance des visages indisponible ({e}).')
    print('Démarrage de l\'oeil (caméra et détection)...')
    oeil = Oeil(a.camera, a.objets, a.image, fenetre=not a.sans_fenetre, visages=visages); oeil.start(); oeil.pret.wait(120)
    if oeil.erreur:
        print(f'Caméra indisponible ({oeil.erreur}) : Câlin parlera sans voir.'); oeil = None

    def sur_outil(nom, entree):
        if nom == 'retenir':
            if memoire.retenir(entree.get('fait', ''), entree.get('personne', '')):
                print(f"   (retenu : {entree.get('personne') or '-'} : {entree.get('fait')})")
            return None
        if nom == 'oublier_souvenirs':
            n = memoire.oublier(entree.get('nom', '')); print(f'   ({n} souvenir(s) effacé(s))')
            return None
        if nom == 'apprendre_visage':
            if not (oeil and visages):
                return 'Je ne peux pas apprendre de visage : ma caméra ou ma reconnaissance des visages ne marche pas.'
            empreintes = oeil.capturer_empreintes()
            if len(empreintes) < 3:
                return 'Je ne vois pas assez bien votre visage. Mettez-vous bien en face de moi, plus près, et redemandez-moi.'
            visages.apprendre(entree['nom'].strip(), empreintes)
            print(f"   (visage appris : {entree['nom']}, {len(empreintes)} images)")
            return None
        if nom == 'oublier_visage':
            ok = visages.oublier(entree.get('nom', '')) if visages else False
            print(f"   (visage {'effacé' if ok else 'introuvable'} : {entree.get('nom')})")
            return None if ok else 'Je ne connaissais pas ce visage.'
        return None

    cerveau = Cerveau(cles['ANTHROPIC_API_KEY'], MODELES_IA[a.ia], PERSONNALITE_ROBOT + '\n\n' + memoire.texte(),
                      outils=OUTILS, sur_outil=sur_outil)
    bouche = Bouche(creer_voix(a, cles))
    oreille = None
    if not a.clavier:
        from ecouter import charger_modele, Oreille
        oreille = Oreille(charger_modele(a.modele), a.micro)

    bouche.dire('Bonjour, je suis Câlin. Je vous vois et je vous écoute !' if oeil else 'Bonjour, je suis Câlin. Je vous écoute !')
    bouche.finir()
    if oreille:
        oreille.vider()
    try:
        while True:
            d_ecoute = None
            if oreille:
                phrase = oreille.phrase(); d_ecoute = oreille.duree_comprehension; print(f'Vous : {phrase}')
            else:
                phrase = input('Vous : ').strip()
                if not phrase:
                    continue
            contexte, photo = None, None
            if oeil:
                contexte = oeil.resume()
                if QUESTION_VISUELLE.search(phrase):
                    photo = oeil.photo_jpeg()
                print(f'   {contexte}' + ('  + photo envoyée' if photo else ''))
            t = time.time(); bouche.debut_tour()
            cerveau.repondre(phrase, image_jpeg=photo, contexte=contexte, sur_phrase=bouche.dire)
            bouche.finir()
            afficher_durees(d_ecoute, cerveau, bouche, time.time() - t)
            if oreille:
                oreille.vider()
            if any(m in phrase.lower() for m in MOTS_FIN):
                break
    except (KeyboardInterrupt, EOFError):
        print('\nArrêt.')
    finally:
        if oreille:
            oreille.fermer()
        if oeil:
            oeil.arret = True

if __name__ == '__main__':
    main()
