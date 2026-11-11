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
import cv2
import parler
from parler import Cerveau, Bouche, creer_voix, options_communes, cles_ou_quitter, afficher_durees, MODELES_IA, MOTS_FIN

PERSONNALITE_ROBOT = parler.PERSONNALITE + """

Ta caméra : avant chaque phrase du visiteur, une ligne entre crochets te dit ce que ta détection automatique \
repère en ce moment (elle se trompe souvent et ne connaît que des objets courants). Quand une photo est jointe, \
c'est ce que ta caméra voit à l'instant : fie-toi à la photo plutôt qu'à la liste. Parle de ce que tu vois \
simplement, comme un robot curieux, sans décrire tout le décor. Ne commente pas la caméra si on ne t'en parle pas."""

# Mots qui déclenchent l'envoi de la photo à l'IA
QUESTION_VISUELLE = re.compile(
    r"\b(vois|voir|voit|regarde|regarder|montre|caméra|photo|devant toi|reconnais|c'est quoi|qu'est-ce que c'est|"
    r"qu'est ce que c'est|combien|couleur|tiens|je tiens|dans ma main|comment je suis|qui est là)\b", re.I)

class Oeil(threading.Thread):
    """Caméra en tâche de fond : affiche la fenêtre, détecte les objets ~3 fois par seconde."""
    def __init__(self, camera=0, objets=None, image=None, fenetre=True):
        super().__init__(daemon=True)
        self.camera, self.objets, self.image, self.fenetre = camera, objets, image, fenetre
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
            resultat, t_detection = None, 0.0
            while not self.arret:
                ok, image = lire()
                if not ok:
                    raise RuntimeError('la webcam ne renvoie plus d\'image')
                if time.time() - t_detection > 0.33:      # ~3 détections par seconde : laisse du calcul à l'écoute
                    resultat, t_detection = modele(image, verbose=False)[0], time.time()
                annotee, vus = vision.annoter(image, resultat, seuil, fonte, noms)
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

    def resume(self):
        with self.verrou:
            vus = list(self.noms_vus)
        if not vus:
            return '[Caméra, détection automatique : rien de reconnu en ce moment]'
        compte = {n: vus.count(n) for n in dict.fromkeys(vus)}
        liste = ', '.join(f'{n} ×{k}' if k > 1 else n for n, k in compte.items())
        return f'[Caméra, détection automatique (peut se tromper) : {liste}]'

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
    ap.add_argument('--camera', type=int, default=0, help='numéro de la webcam (voir lister_cameras.bat)')
    ap.add_argument('--objets', help='détecter sa propre liste d\'objets (objets.txt)')
    ap.add_argument('--image', help='une photo fixe à la place de la webcam (pour essayer)')
    ap.add_argument('--sans-fenetre', action='store_true', help='ne pas afficher la fenêtre de la caméra')
    a = ap.parse_args()

    cles = cles_ou_quitter()
    print('Démarrage de l\'oeil (caméra et détection)...')
    oeil = Oeil(a.camera, a.objets, a.image, fenetre=not a.sans_fenetre); oeil.start(); oeil.pret.wait(120)
    if oeil.erreur:
        print(f'Caméra indisponible ({oeil.erreur}) : Câlin parlera sans voir.'); oeil = None
    cerveau = Cerveau(cles['ANTHROPIC_API_KEY'], MODELES_IA[a.ia], PERSONNALITE_ROBOT)
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
