"""Câlin trie les objets posés sur la table : il les trouve à la caméra, les prend un par un, les mesure en serrant la pince, et
les pose dans la zone de leur taille (petits à GAUCHE, gros à DROITE, vu de derrière le bras).

Lancer : trier.bat (FD et la fenêtre de contrôle fermés, 12 V allumé, caméra branchée, regler_table.bat déjà fait).
Dans la fenêtre :
  F         photo du FOND : table VIDE, bras au repos. À refaire si la caméra ou la lumière change beaucoup.
  (ensuite) les objets trouvés sont entourés, numérotés, avec leur largeur ; les deux zones de dépôt (à gauche et à droite) sont
            entre deux traits orange : n'y mets pas les objets à trier
  Une zone peut être un BAC (regler_bac.bat) : l'objet y est lâché d'au-dessus. Bac en place AVANT la photo du fond (F).
  Un objet pris pince inclinée est REPOSÉ avec la même inclinaison (sinon il penche) : la distance de pose suit celle de la prise.
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

# Les zones de dépôt sont des DIRECTIONS (angle du socle, + = à droite vu de derrière) : un objet pris pince inclinée doit être
# reposé avec la MÊME inclinaison, sinon il penche et tombe (Nicolas, 26/11/2026). Chaque inclinaison n'est possible que dans une
# bande de distances (environ 5 à 8 cm de large) : on pose donc dans la direction de la zone, à la distance qui va avec la prise.
ZONES = {'petit': -40.0, 'gros': 40.0}
PLURIEL = {'petit': 'petits', 'gros': 'gros'}
SECTEUR = 16.0                                                    # degrés de part et d'autre : on n'y cherche pas d'objets à trier
ECART_DEPOT = 50.0                                                # mm entre deux objets posés dans une zone
# Pour agrandir la zone de pose (demande de Nicolas, 26/11/2026) : on accepte de poser avec la pince inclinée 15° de PLUS ou de
# MOINS qu'à la prise. L'objet arrive penché de 15° : ses coins descendraient sous la pince, on le lâche donc 13 mm plus haut ; il
# retombe droit tout seul (il ne bascule qu'au-delà de 23° pour la barre, 25° pour le petit rond, par le calcul).
ECART_INCL = 15.0
LEVE_PENCHE = 13.0                                                # mm : 32 (demi-longueur de la barre) × sin 15° + 5 de marge
SEUIL_TAILLE = 32.0                                               # mm, largeur mesurée par la pince : en dessous, « petit »
ECART_MIN = 55.0                                                  # mm entre deux objets : plus près, la pince ouverte risque de toucher le voisin
ESSAIS_MAX = 2                                                    # tentatives au même endroit avant d'abandonner l'objet
# Option BAC (demande de Nicolas, 26/11/2026) : une zone peut être un bac posé sur la table (réglé par regler_bac.bat, gardé
# dans bacs.json sur le PC). Le bras lâche alors l'objet AU-DESSUS du bac : n'importe quelle inclinaison convient, plus de
# problème de place. Le bas de l'objet passe GARDE_BAC mm au-dessus du bord. Le bac doit être en place AVANT la photo du fond.
FICHIER_BACS = Path(__file__).with_name('bacs.json')
GARDE_BAC = 25.0
def charger_bacs():
    try:
        b = __import__('json').loads(FICHIER_BACS.read_text(encoding='utf-8'))
        return {z: v for z, v in b.items() if z in ZONES and all(k in v for k in ('X', 'Y', 'bord', 'largeur', 'profondeur'))}
    except Exception: return {}
def dans_un_bac(X, Y, bacs, marge=30.0):
    return any(abs(X - b['X']) < b['largeur'] / 2 + marge and abs(Y - b['Y']) < b['profondeur'] / 2 + marge for b in bacs.values())
def pose_dans_bac(bac, incl_prise, hauteur_epaule=179.0):
    """Comment lâcher au-dessus du bac : (point, inclinaison, levée) ou None. L'objet pend sous la pince d'environ la hauteur de
    prise ; on le monte du bord + la garde, en essayant d'abord l'inclinaison de la prise (l'objet descend droit), puis les autres."""
    ordre = sorted(G.INCLINAISONS, key=lambda i: abs(i - incl_prise))
    for i in ordre:
        leve = bac['bord'] + GARDE_BAC + max(0.0, abs(i - incl_prise)) * 0.6       # un objet penché descend un peu plus bas
        for dx, dy in ((0, 0), (15, 0), (-15, 0), (0, 15), (0, -15)):
            pt = (bac['X'] + dx, bac['Y'] + dy)
            try: G.prise_et_approche(*pt, hauteur_epaule, i, leve); return pt, i, leve
            except G.HorsDePortee: pass
    return None

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
        self.deposes = {z: [] for z in ZONES}
        self.bacs = charger_bacs()
        for z, b in self.bacs.items(): self.dire(f'Les {PLURIEL[z]} vont dans le bac (X {b["X"]:+.0f}, Y {b["Y"]:.0f}, bord à {b["bord"]:.0f} mm).')
        if FICHIER_FOND.exists(): self.fond = cv2.imread(str(FICHIER_FOND)); self.dire('Photo du fond reprise du dernier essai (F pour la refaire si la caméra a bougé).')

    def voir(self, image):
        self.image = image.copy()
        centres, contours = super().voir(image)
        if self.fond is not None and self.vus and self.h is not None and self.au_repos and self.fond.shape == image.shape:
            self.objets = [o for o in O.trouver(image, self.fond, self.h, self.reglage, self.hauteur)
                           if not dans_un_bac(o['X'], o['Y'], self.bacs)
                           and not any(abs(math.degrees(math.atan2(o['X'], o['Y'])) - a) < SECTEUR for z, a in ZONES.items() if z not in self.bacs)]
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

    def lacher_dans_bac(self, z, incl, largeur):
        p, c = self.p, self.p.c
        pose = pose_dans_bac(self.bacs[z], incl, c.hauteur)
        if not pose: raise ErreurServo(f'le bac des {PLURIEL[z]} est hors de portée : objet toujours tenu. R, puis tiens-le et ouvre la pince à la main.')
        pt, i, leve = pose
        self.dire(f'   {largeur:.0f} mm : c\'est un {z.upper()}, je le lâche dans son bac (pince à {abs(i):.0f}°, {leve:.0f} mm au-dessus de la hauteur de prise).')
        plan = p.preparer(*C.corriger(*pt, self.corrections), i, leve)
        if not plan: raise ErreurServo('pose dans le bac impossible : objet toujours tenu. R, puis tiens-le et ouvre la pince à la main.')
        p.aller(*plan); self.etape(p.prise is plan[0], 'le transport')
        self.etape(p.descendre(), 'l\'arrivée au-dessus du bac'); c._pince('o'); p.vider(); time.sleep(0.3)
        self.etape(p.monter(), 'la remontée'); p.repos(); self.tries[z] += 1
        return True

    def place_libre(self, zone, incl):
        """Où poser et comment : (point, inclinaison, levée) ou None. D'abord avec l'inclinaison de la prise (objet posé droit),
        sinon avec 15° de plus ou de moins (objet lâché 13 mm plus haut, il se redresse seul)."""
        for i, leve in ((incl, 0.0), (incl + ECART_INCL, LEVE_PENCHE), (incl - ECART_INCL, LEVE_PENCHE)):
            if not -90.0 <= i <= 0.0: continue
            pt = self.place_libre_incl(zone, i, leve)
            if pt: return pt, i, leve
        return None

    def place_libre_incl(self, zone, incl, leve=0.0):
        """Un point de la zone où poser avec l'inclinaison `incl` : dans la direction de la zone, à une distance possible pour
        cette inclinaison, loin des objets déjà posés. On essaie d'abord le milieu de la bande, puis de part et d'autre."""
        a = ZONES[zone]; bd = G.bande(incl, self.p.c.hauteur, a)
        if not bd: return None
        milieu = (bd[0] + bd[1]) / 2
        for R in sorted(range(int(bd[0]) + 5, int(bd[1]) - 4, 5), key=lambda r: abs(r - milieu)):
            for da in (0.0, -10.0, 10.0):
                pt = G.point_dans_direction(a + da, R)
                if all(math.hypot(pt[0] - x, pt[1] - y) >= ECART_DEPOT for x, y in self.deposes[zone]):
                    try: G.prise_et_approche(*pt, self.p.c.hauteur, incl, leve); return pt
                    except G.HorsDePortee: pass
        return None

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
        z = zone_de(largeur); incl = p.incl
        if z in self.bacs: return self.lacher_dans_bac(z, incl, largeur)
        place = self.place_libre(z, incl)
        spot, incl_pose, leve = place if place else (None, None, None)
        if spot is None: raise ErreurServo(f'plus de place dans la zone des {PLURIEL[z]} à la bonne distance : objet toujours tenu. Vide la zone, puis R (tiens l\'objet).')
        cote = "gauche" if ZONES[z] < 0 else "droite"
        if leve: self.dire(f'   {largeur:.0f} mm : c\'est un {z.upper()}, je le pose à {cote}, pince à {abs(incl_pose):.0f}° (prise à {abs(incl):.0f}°) : lâché {leve:.0f} mm plus haut, il se redresse seul.')
        else: self.dire(f'   {largeur:.0f} mm : c\'est un {z.upper()}, je le pose à {cote}, pince inclinée comme à la prise ({abs(incl):.0f}°).')
        plan = p.preparer(*C.corriger(*spot, self.corrections), incl_pose, leve)
        if not plan: raise ErreurServo(f'pose impossible : objet toujours tenu. R, puis tiens-le et ouvre la pince à la main (O dans viser_camera).')
        p.aller(*plan); self.etape(p.prise is plan[0], 'le transport')
        self.etape(p.descendre(), 'la pose'); c._pince('o'); p.vider()
        self.etape(p.monter(), 'la remontée'); p.repos(); self.tries[z] += 1; self.deposes[z].append(spot)
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
            for nom, b in self.bacs.items():
                w, d = b['largeur'] / 2, b['profondeur'] / 2
                pts = np.array([T.vers_image(self.h, b['X'] + sx * w, b['Y'] + sy * d) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))], np.int32)
                cv2.polylines(image, [pts], True, (255, 160, 0), 2); V.ecrire(image, f'bac des {PLURIEL[nom]}', T.vers_image(self.h, b['X'] - w, b['Y'] + d + 15), (255, 200, 80), 0.6)
            for nom, a in ZONES.items():
                if nom in self.bacs: continue
                for b in (a - SECTEUR, a + SECTEUR):
                    cv2.line(image, T.vers_image(self.h, *G.point_dans_direction(b, 190)), T.vers_image(self.h, *G.point_dans_direction(b, 480)), (255, 160, 0), 2)
                V.ecrire(image, f'zone des {PLURIEL[nom]}', T.vers_image(self.h, *G.point_dans_direction(a, 480)), (255, 200, 80), 0.6)
                for x, y in self.deposes[nom]: cv2.circle(image, T.vers_image(self.h, x, y), 8, (255, 160, 0), 2)
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
    """Chaque zone doit accepter toutes les inclinaisons de prise : sinon un objet pris pourrait ne pas pouvoir y être posé."""
    bacs = charger_bacs()
    for nom, b in bacs.items():
        for incl in G.INCLINAISONS:
            if not pose_dans_bac(b, incl, hauteur_epaule): raise G.HorsDePortee(f'bac des {PLURIEL[nom]} : impossible d\'y lâcher un objet pris pince à {abs(incl)}° (relance regler_bac.bat)')
    for nom, a in ZONES.items():
        if nom in bacs: continue
        for incl in G.INCLINAISONS:
            if not G.bande(incl, hauteur_epaule, a): raise G.HorsDePortee(f'zone des {PLURIEL[nom]} ({a:+.0f}°) : impossible de poser pince inclinée de {abs(incl)}°')

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
