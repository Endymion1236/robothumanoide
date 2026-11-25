"""La caméra et le bras dans une seule fenêtre : on CLIQUE sur un point de la table, le bras y va.
C'est voir_table (camera) et aller_point (bras) réunis : plus besoin de recopier X et Y d'une fenêtre à l'autre.

Lancer : viser_camera.bat (FD et la fenêtre de contrôle fermés, 12 V allumé, caméra branchée, regler_table.bat déjà fait).
Dans la fenêtre :
  CLIC      choisir un point : le programme calcule le geste et l'annonce, le bras ne bouge PAS encore
  ENTRÉE    y aller : le bras se place AU-DESSUS du point (il choisit l'inclinaison de la pince)
  D / M     descendre sur le point / remonter          O / S   ouvrir / serrer la pince
  R         repos                                      I       où est la pince
  ESPACE    ARRÊT : le geste en cours s'arrête, le bras reste TENU
  P         photo de la table                          Q       quitter
Quand le bras passe au-dessus de la table il cache des marqueurs : le programme garde le dernier repérage (la caméra ne doit
pas bouger entre-temps). Chaque geste est vérifié avant d'être fait (butées, table), comme dans aller_point."""
import argparse, sys, threading, time, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'camera'))
import cv2
import table as T, voir_table as V
import aller_point as A
from servos import ErreurServo

AIDE = 'Clic = choisir un point | ENTREE = y aller | D descendre  M remonter | O ouvrir  S serrer | R repos | ESPACE = ARRET | Q quitter'
def sans_accents(texte):
    """Les lettres dessinées sur l'image n'ont pas d'accents : on les retire (é → e, ° → deg, → → ->)."""
    texte = texte.replace('°', ' deg').replace('→', '->').replace('«', '"').replace('»', '"').replace('·', '|').replace('≈', '~').replace('−', '-')
    return ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn').encode('ascii', 'replace').decode()

class Poste:
    """Toute la logique, sans fenêtre ni caméra (pour pouvoir l'essayer sur des servos simulés et une image fabriquée)."""
    def __init__(self, pointeur, reglage, attendre=False):
        self.p, self.reglage, self.attendre = pointeur, reglage, attendre
        self.h = None; self.vus = True; self.cible = None; self.plan = None; self.messages = []; self.occupe = None; self.fil = None
        pointeur.dire = self.dire
    def dire(self, texte):
        print(texte)
        for ligne in str(texte).splitlines():
            if ligne.strip(): self.messages.append(ligne.strip())
        del self.messages[:-4]

    def voir(self, image):
        """Repère les marqueurs dans l'image. Tant que les 4 sont vus, le repérage est mis à jour ; sinon on garde le dernier."""
        centres, contours = T.detecter(image); h = T.passage(centres, self.reglage)
        if h is not None: self.h = h
        self.vus = h is not None
        return centres, contours

    def clic(self, x, y):
        if self.occupe: self.dire('Le bras bouge : attends la fin du geste (ou ESPACE pour l\'arrêter).'); return
        if self.h is None: self.dire('La table n\'est pas encore repérée : il faut voir les 4 marqueurs au moins une fois.'); return
        if not self.vus: self.dire('Attention : des marqueurs sont cachés, je me sers du dernier repérage.')
        X, Y = T.vers_table(self.h, x, y); self.cible, self.plan = (X, Y), None
        try: self.plan = self.p.preparer(X, Y)
        except ErreurServo as err: self.dire(f'Refusé : {err}')
        if self.plan: self.dire('ENTRÉE pour y aller, ou clique ailleurs.')

    def _lancer(self, nom, geste):
        if self.occupe: self.dire(f'Le bras est déjà occupé ({self.occupe}) : attends, ou ESPACE pour l\'arrêter.'); return
        self.p.c.arret.clear(); self.occupe = nom
        def travail():
            try: geste()
            except ErreurServo as err: self.dire(f'Refusé : {err}'); self.p.vider()
            except Exception as err: self.dire(f'Erreur ({type(err).__name__} : {err}). Le bras reste tenu.')
            finally: self.occupe = None
        self.fil = threading.Thread(target=travail, daemon=True); self.fil.start()
        if self.attendre: self.fil.join()

    def touche(self, k):
        """Une touche du clavier. Renvoie False quand il faut quitter."""
        p = self.p; k = chr(k).lower() if 0 < k < 128 else ''
        if k == ' ':
            if self.occupe: p.c.arret.set(); self.dire('ARRÊT demandé : le bras reste tenu.')
        elif k == 'q':
            if self.occupe: p.c.arret.set(); self.fil.join(timeout=10)
            return False
        elif k in ('\r', '\n'):
            if not self.plan: self.dire('Clique d\'abord sur un point de la table.')
            else: plan = self.plan; self._lancer('il va au point', lambda: p.aller(*plan))
        elif k == 'd': self._lancer('il descend', p.descendre)
        elif k == 'm': self._lancer('il remonte', p.monter)
        elif k == 'r': self.plan = None; self._lancer('retour au repos', p.repos)
        elif k in ('o', 's'): self._lancer('la pince', lambda: (p.c._pince(k), p.vider()))
        elif k == 'i': self._lancer('lecture', p.infos)
        return True

    def dessiner(self, image, centres, contours):
        for i, c in contours.items():
            cv2.polylines(image, [c.astype(int)], True, (0, 200, 0), 2)
            cv2.putText(image, str(i), (int(centres[i][0]) - 8, int(centres[i][1]) + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        if self.h is None: V.ecrire(image, f'Marqueurs manquants : {[i for i in T.IDS if i not in centres]}', (10, 40), (80, 80, 255))
        elif self.occupe: V.ecrire(image, sans_accents(f'Le bras bouge ({self.occupe})... ESPACE = ARRET'), (10, 40), (0, 200, 255))
        elif not self.vus: V.ecrire(image, 'Marqueurs caches (par le bras ?) : dernier reperage garde', (10, 40), (0, 200, 255))
        else: V.ecrire(image, 'Table reperee : clique sur un point', (10, 40), (120, 255, 120))
        if self.cible and self.h is not None:
            X, Y = self.cible; pt = T.vers_image(self.h, X, Y); ok = self.plan is not None
            cv2.circle(image, pt, 11, (0, 0, 0), -1); cv2.circle(image, pt, 8, (0, 230, 255) if ok else (80, 80, 255), -1)
            V.ecrire(image, f'X {X:+.0f}   Y {Y:+.0f} mm' + ('' if ok else '   (impossible)'), (pt[0] + 16, pt[1] - 16), (0, 230, 255) if ok else (120, 120, 255), 0.8)
        haut = image.shape[0]; pas = int(30 * haut / 720)
        V.ecrire(image, AIDE, (10, haut - 14), (255, 255, 255), 0.55)
        for n, m in enumerate(reversed(self.messages[-3:])):
            V.ecrire(image, sans_accents(m)[:110], (10, haut - 14 - (n + 1) * pas), (0, 230, 255) if n == 0 else (190, 190, 190), 0.55)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--camera', type=int, default=1)
    ap.add_argument('--large', type=int, default=1280); ap.add_argument('--haut', type=int, default=960)
    ap.add_argument('--fenetre', type=int, default=700, help='hauteur maximale de la fenêtre à l\'écran (points)'); a = ap.parse_args()
    reglage = T.charger()
    if not reglage: print('Réglage de la table introuvable : lance d\'abord camera\\regler_table.bat'); return 1
    cam = cv2.VideoCapture(a.camera, cv2.CAP_DSHOW) if sys.platform == 'win32' else cv2.VideoCapture(a.camera)
    if not cam.isOpened(): print(f'Caméra n° {a.camera} introuvable : essaie --camera 0 dans viser_camera.bat.'); return 1
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, a.large); cam.set(cv2.CAP_PROP_FRAME_HEIGHT, a.haut)
    try: p = A.Pointeur()                                   # la caméra d'abord : si elle manque, on n'a pas encore pris le bras en main
    except ErreurServo as err: print('Impossible de commencer :', err); cam.release(); return 1
    poste = Poste(p, reglage); ech = {'v': 1.0}
    cv2.namedWindow('Calin : table et bras')
    cv2.setMouseCallback('Calin : table et bras', lambda evt, x, y, *_: poste.clic(x / ech['v'], y / ech['v']) if evt == cv2.EVENT_LBUTTONDOWN else None)
    z = A.G.zone_toutes(p.c.hauteur)
    poste.dire(f'Zone atteinte droit devant : de {z[0]} à {z[1]} mm de l\'axe du socle.')
    poste.dire('Clique sur un point de la table, puis ENTRÉE. ESPACE = arrêt. Q = quitter.')
    try:
        while True:
            ok, image = cam.read()
            if not ok: print('La caméra ne répond plus.'); break
            brute = image.copy(); centres, contours = poste.voir(image); poste.dessiner(image, centres, contours)
            ech['v'] = V.ech_fenetre(image.shape[0], a.fenetre)
            cv2.imshow('Calin : table et bras', image if ech['v'] == 1.0 else cv2.resize(image, None, fx=ech['v'], fy=ech['v'], interpolation=cv2.INTER_AREA))
            k = cv2.waitKey(1) & 0xFF
            if k in (ord('p'), ord('P')):
                V.PHOTOS.mkdir(exist_ok=True); nom = V.PHOTOS / time.strftime('table_%Y%m%d_%H%M%S.png'); cv2.imwrite(str(nom), brute); poste.dire(f'Photo enregistrée : {nom.name}')
            elif k != 255 and not poste.touche(k): break
    except KeyboardInterrupt: print('\nInterrompu : le bras reste tenu.')
    cam.release(); cv2.destroyAllWindows()
    return A.terminer(p)

if __name__ == '__main__': sys.exit(main())
