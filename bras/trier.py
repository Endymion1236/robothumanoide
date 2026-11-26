"""Câlin trie les objets posés sur la table : il les trouve à la caméra, les prend un par un, les mesure en serrant la pince, et
les pose dans la zone de leur taille (petits à GAUCHE, gros à DROITE, vu de derrière le bras).

Lancer : trier.bat (FD et la fenêtre de contrôle fermés, 12 V allumé, caméra branchée, regler_table.bat déjà fait).
Dans la fenêtre :
  F         photo du FOND : table VIDE, bras au repos. À refaire si la caméra ou la lumière change beaucoup.
  (ensuite) les objets trouvés sont entourés, numérotés, avec leur position ; les deux zones de dépôt sont dessinées en cercle
  T         TRIER : il prend les objets un par un jusqu'à ce qu'il n'y en ait plus (ou ESPACE)
  1         n'en trier qu'UN (pour les premiers essais)
  R         repos        ESPACE   ARRÊT (le bras reste tenu)        P   photo        Q   quitter
Il se sert des corrections de visée apprises dans viser_camera (flèches + C).

Comment il voit : il compare l'image à la photo du fond (camera/objets.py) ; il ne regarde que bras au repos, car le bras lui-même
changerait l'image. Il corrige le « penché » des objets hauts (60 mm par défaut, --hauteur pour changer)."""
import argparse, math, sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'camera'))
import cv2, numpy as np
import table as T, voir_table as V, objets as O
import aller_point as A, correction as C, geometrie as G, test_pince as PI
from servos import ErreurServo
from viser_camera import Poste, sans_accents, FLECHES

ZONES = {'petit': (-235.0, 330.0), 'gros': (235.0, 330.0)}      # où poser (mm) ; petits à gauche, gros à droite, vu de derrière
R_ZONE = 60.0                                                     # rayon autour d'une zone où on ne cherche pas d'objet
SEUIL_TAILLE = 32.0                                               # mm, largeur mesurée par la pince : en dessous, « petit »
ECART_MIN = 55.0                                                  # mm entre deux objets : plus près, la pince ouverte risque de toucher le voisin
ESSAIS_MAX = 2                                                    # tentatives au même endroit avant d'abandonner l'objet
FICHIER_FOND = Path(__file__).resolve().parent.parent / 'camera' / 'fond_table.png'
AIDE = 'F = photo du fond (table VIDE) | T = TRIER | 1 = un seul objet | R repos | ESPACE = ARRET | P photo | Q quitter'

def choisir(objets, rates):
    """L'objet à prendre maintenant : le plus isolé, parmi ceux qui n'ont pas déjà raté ESSAIS_MAX fois au même endroit."""
    candidats = []
    for o in objets:
        if sum(1 for x, y in rates if math.hypot(o['X'] - x, o['Y'] - y) < 25) >= ESSAIS_MAX: continue
        voisin = min([math.hypot(o['X'] - a['X'], o['Y'] - a['Y']) for a in objets if a is not o] or [999.0])
        candidats.append((voisin, o))
    return max(candidats, key=lambda c: c[0]) if candidats else (None, None)

def zone_de(largeur): return 'petit' if largeur < SEUIL_TAILLE else 'gros'

class Trieur(Poste):
    def __init__(self, pointeur, reglage, hauteur=O.HAUTEUR_OBJETS, attendre=False):
        super().__init__(pointeur, reglage, attendre)
        self.hauteur, self.fond, self.objets, self.image = hauteur, None, [], None
        self.demande, self.reponse = threading.Event(), threading.Event()
        self.au_repos, self.tries, self.rates = True, {'petit': 0, 'gros': 0}, []
        if FICHIER_FOND.exists(): self.fond = cv2.imread(str(FICHIER_FOND)); self.dire('Photo du fond reprise du dernier essai (F pour la refaire si la caméra a bougé).')

    def voir(self, image):
        self.image = image.copy()
        centres, contours = super().voir(image)
        if self.fond is not None and self.vus and self.h is not None and self.au_repos and self.fond.shape == image.shape:
            self.objets = O.trouver(image, self.fond, self.h, self.reglage, self.hauteur, exclure=[(x, y, R_ZONE) for x, y in ZONES.values()])
            if self.demande.is_set(): self.demande.clear(); self.reponse.set()
        return centres, contours

    def photo_fond(self):
        if self.occupe or not self.au_repos: self.dire('Bras au repos d\'abord (R), table vide.'); return
        if self.image is None or not self.vus: self.dire('Il faut voir les 4 marqueurs pour prendre le fond.'); return
        self.fond = self.image.copy(); cv2.imwrite(str(FICHIER_FOND), self.fond); self.objets = []
        self.dire('Fond enregistré. Pose maintenant les objets sur la table.')

    def regarder(self, delai=8.0):
        """Attend une image prise bras au repos et renvoie les objets trouvés (copie)."""
        self.au_repos = True; time.sleep(0.6); self.reponse.clear(); self.demande.set()
        if not self.reponse.wait(delai): raise ErreurServo('je ne vois plus les 4 marqueurs, bras au repos : la caméra a-t-elle bougé ?')
        return list(self.objets)

    def etape(self, ok, quoi):
        if self.p.c.arret.is_set(): raise ErreurServo('arrêt demandé')
        if not ok: raise ErreurServo(f'{quoi} n\'a pas pu se faire')

    def serrer(self):
        c = self.p.c; r = c.reglages; c.bus.tenir(c.pince)
        texte, pos, tenu = c.bus.serrer(c.pince, c.ferme, r['serrage_doux'], maintien=min(r['maintien'], r['serrage_doux']))
        largeur = PI.ecart_mm(pos, c.ouvert); self.dire(f'Serrer : {texte}' + (f' · largeur ≈ {largeur:.0f} mm' if tenu else ''))
        return tenu, largeur

    def un_objet(self, objets):
        """Prend l'objet le plus isolé et le pose dans sa zone. Renvoie True si un objet a été trié, False s'il n'y en a plus."""
        p, c = self.p, self.p.c
        voisin, o = choisir(objets, self.rates)
        if o is None: return False
        if voisin < ECART_MIN: self.dire(f'Attention : l\'objet en X {o["X"]:+.0f} Y {o["Y"]:.0f} a un voisin à {voisin:.0f} mm, la pince pourrait le toucher.')
        visee = C.corriger(o['X'], o['Y'], self.corrections)
        self.dire(f'Je prends l\'objet en X {o["X"]:+.0f}, Y {o["Y"]:.0f} (vu {o["largeur"]:.0f} mm de large).')
        plan = p.preparer(*visee)
        if not plan: self.rates += [(o['X'], o['Y'])] * ESSAIS_MAX; self.dire('   Hors de portée : je le laisse.'); return True
        self.au_repos = False
        c._pince('o'); p.vider()
        p.aller(*plan); self.etape(p.prise is plan[0], 'l\'approche')
        self.etape(p.descendre(), 'la descente')
        tenu, largeur = self.serrer()
        self.etape(p.monter(), 'la remontée')
        if not tenu:
            self.rates.append((o['X'], o['Y'])); self.suite_ratee += 1; c._pince('o'); p.vider()
            self.dire('   Raté : rien entre les doigts. Je regarde à nouveau.'); p.repos()
            if self.suite_ratee >= 3: raise ErreurServo('3 prises ratées de suite : la visée est sans doute décalée. Refais la correction aux flèches dans viser_camera, puis reviens.')
            return True
        self.suite_ratee = 0
        z = zone_de(largeur); zx, zy = ZONES[z]
        self.dire(f'   {largeur:.0f} mm : c\'est un {z.upper()}, je le pose à {"gauche" if zx < 0 else "droite"}.')
        plan = p.preparer(*C.corriger(zx, zy, self.corrections))
        if not plan: raise ErreurServo(f'la zone des {z} est hors de portée : objet toujours tenu, pose-le à la main (r puis tiens-le)')
        p.aller(*plan); self.etape(p.prise is plan[0], 'le transport')
        self.etape(p.descendre(), 'la pose'); c._pince('o'); p.vider()
        self.etape(p.monter(), 'la remontée'); p.repos(); self.tries[z] += 1
        return True

    def trier(self, combien=None):
        n = 0; self.suite_ratee = 0
        self.p.repos()
        while combien is None or n < combien:
            objets = self.regarder()
            if not objets: break
            self.dire(f'{len(objets)} objet(s) sur la table.')
            if not self.un_objet(objets): break
            n += 1
        reste = [o for o in self.regarder()]
        self.dire(f'Fini : {self.tries["petit"]} petit(s) à gauche, {self.tries["gros"]} gros à droite.' + (f' {len(reste)} objet(s) laissé(s) (hors de portée ou ratés).' if reste and combien is None else ''))

    def touche(self, k):
        kk = chr(k).lower() if 0 < k < 128 else ''
        if kk == 'f': self.photo_fond(); return True
        if kk in ('t', '1'):
            if self.fond is None: self.dire('Il faut d\'abord la photo du fond : table VIDE, bras au repos, touche F.'); return True
            self.rates = []
            def geste():
                try: self.trier(None if kk == 't' else 1)
                finally: self.au_repos = True
            self._lancer('tri en cours', geste); return True
        if kk == 'r':
            def repos():
                self.p.repos(); self.au_repos = True
            self.plan = None; self._lancer('retour au repos', repos); return True
        if kk in ('d', 'm', 'c', 'e', 'o', 's', 'i', 'j', 'l', 'u', 'n', '\r', '\n') or k in FLECHES:
            return True                                                  # gestes à la main : dans viser_camera, pas ici
        return super().touche(k)

    def clic(self, x, y): self.dire('Ici on ne clique pas : F (fond), puis T pour trier. Pour viser à la main : viser_camera.')

    def dessiner(self, image, centres, contours):
        if self.h is not None:
            for nom, (x, y) in ZONES.items():
                pts = np.array([T.vers_image(self.h, x + R_ZONE * math.cos(a), y + R_ZONE * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40)], np.int32)
                cv2.polylines(image, [pts], True, (255, 160, 0), 2); V.ecrire(image, f'zone {nom}s', T.vers_image(self.h, x - 40, y + R_ZONE + 15), (255, 200, 80), 0.6)
            for n, o in enumerate(self.objets, 1):
                pts = np.array([T.vers_image(self.h, x, y) for x, y in o['contour']], np.int32)
                cv2.polylines(image, [pts], True, (0, 255, 255), 2)
                pt = T.vers_image(self.h, o['X'], o['Y']); cv2.circle(image, pt, 6, (0, 0, 255), -1)
                V.ecrire(image, f'{n} : {o["largeur"]:.0f} mm', (pt[0] + 10, pt[1] - 10), (0, 255, 255), 0.6)
        haut = image.shape[0]; pas = int(30 * haut / 720)
        etat = ('Le bras trie... ESPACE = ARRET' if self.occupe else 'Photo du fond manquante : table VIDE, bras au repos, touche F' if self.fond is None
                else f'{len(self.objets)} objet(s) vu(s). T = trier' if self.vus else 'Marqueurs caches : dernier reperage garde')
        V.ecrire(image, sans_accents(etat), (10, 40), (0, 200, 255) if self.occupe or self.fond is None else (120, 255, 120))
        V.ecrire(image, AIDE, (10, haut - 14), (255, 255, 255), 0.55)
        for n, m in enumerate(reversed(self.messages[-3:])):
            V.ecrire(image, sans_accents(m)[:110], (10, haut - 14 - (n + 1) * pas), (0, 230, 255) if n == 0 else (190, 190, 190), 0.55)

def verifier_zones(hauteur_epaule=179.0):
    for nom, (x, y) in ZONES.items(): G.choisir_inclinaison(*(x, y), hauteur_epaule)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--camera', type=int, default=1); ap.add_argument('--hauteur', type=float, default=O.HAUTEUR_OBJETS)
    ap.add_argument('--fenetre', type=int, default=700); a = ap.parse_args()
    reglage = T.charger()
    if not reglage: print('Réglage de la table introuvable : lance d\'abord camera\\regler_table.bat'); return 1
    cam = cv2.VideoCapture(a.camera, cv2.CAP_DSHOW) if sys.platform == 'win32' else cv2.VideoCapture(a.camera)
    if not cam.isOpened(): print(f'Caméra n° {a.camera} introuvable : essaie --camera 0 dans trier.bat.'); return 1
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280); cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
    try: p = A.Pointeur()
    except ErreurServo as err: print('Impossible de commencer :', err); cam.release(); return 1
    try: verifier_zones(p.c.hauteur)
    except G.HorsDePortee as e: print('Une zone de dépôt est hors de portée :', e); cam.release(); return A.terminer(p)
    t = Trieur(p, reglage, a.hauteur); ech = {'v': 1.0}
    cv2.namedWindow('Calin trie')
    cv2.setMouseCallback('Calin trie', lambda evt, x, y, *_: t.clic(x, y) if evt == cv2.EVENT_LBUTTONDOWN else None)
    t.dire('Bras au repos (R), table VIDE : F. Puis pose les objets et T.' if t.fond is None else 'Pose les objets, puis T (ou 1 pour un seul).')
    cam_dite = False
    try:
        while True:
            ok, image = cam.read()
            if not ok: print('La caméra ne répond plus.'); break
            brute = image.copy(); centres, contours = t.voir(image)
            if not cam_dite and t.h is not None and t.vus:
                cx, cy, cz, f = O.camera(t.h, (image.shape[1], image.shape[0])); cam_dite = True
                t.dire(f'Caméra calculée à {cz / 10:.0f} cm au-dessus de la table (X {cx:+.0f}, Y {cy:.0f} mm) : vérifie au mètre.')
            t.dessiner(image, centres, contours)
            ech['v'] = V.ech_fenetre(image.shape[0], a.fenetre)
            cv2.imshow('Calin trie', image if ech['v'] == 1.0 else cv2.resize(image, None, fx=ech['v'], fy=ech['v'], interpolation=cv2.INTER_AREA))
            k = cv2.waitKeyEx(1); k = k if k in FLECHES else (k & 0xFF if k != -1 else 255)
            if k in (ord('p'), ord('P')):
                V.PHOTOS.mkdir(exist_ok=True); nom = V.PHOTOS / time.strftime('table_%Y%m%d_%H%M%S.png'); cv2.imwrite(str(nom), brute); t.dire(f'Photo enregistrée : {nom.name}')
            elif k != 255 and not t.touche(k): break
    except KeyboardInterrupt: print('\nInterrompu : le bras reste tenu.')
    cam.release(); cv2.destroyAllWindows()
    return A.terminer(p)

if __name__ == '__main__': sys.exit(main())
