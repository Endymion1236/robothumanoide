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
  O         ouvrir la pince (secours)
  R         repos        ESPACE   ARRÊT (le bras reste tenu)        P   photo        Q   quitter
Il se sert des corrections de visée apprises dans viser_camera (flèches + C).

Comment il voit : il compare l'image à la photo du fond (camera/objets.py) ; il ne regarde que bras au repos, car le bras lui-même
changerait l'image. Il corrige le « penché » des objets hauts (60 mm par défaut, --hauteur pour changer)."""
import argparse, math, sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'camera'))
import cv2, numpy as np
import table as T, voir_table as V, objets as O
import rapport_tri as RT, largeur_pince as LP, consigne_vocale as CV
import aller_point as A, correction as C, geometrie as G, test_pince as PI, obstacles as OB, test_epaule as EP
from servos import ErreurServo
from viser_camera import Poste, sans_accents, FLECHES

# Les zones de dépôt sont des DIRECTIONS (angle du socle, + = à droite vu de derrière) : un objet pris pince inclinée doit être
# reposé avec la MÊME inclinaison, sinon il penche et tombe (Nicolas, 26/11/2026). Chaque inclinaison n'est possible que dans une
# bande de distances (environ 5 à 8 cm de large) : on pose donc dans la direction de la zone, à la distance qui va avec la prise.
# ±65° et pas ±40° : à ±40°, pince inclinée de 60 à 90°, la place de pose tombait SUR les marqueurs de devant (±46°, à 27 cm du
# socle). Essai de Nicolas du 26/11/2026 : objet posé à 28 mm du centre du marqueur n° 0, qui a disparu de la vue → arrêt.
ZONES = {'petit': -65.0, 'gros': 65.0}
LOIN_DES_MARQUEURS = 75.0                                         # mm : jamais de pose plus près du centre d'un marqueur
PLURIEL = {'petit': 'petits', 'gros': 'gros'}
SECTEUR = 16.0                                                    # degrés de part et d'autre : on n'y cherche pas d'objets à trier
ECART_DEPOT = 50.0                                                # mm entre deux objets posés dans une zone
# Pour agrandir la zone de pose (demande de Nicolas, 26/11/2026) : on accepte de poser avec la pince inclinée 15° de PLUS ou de
# MOINS qu'à la prise. L'objet arrive penché de 15° : ses coins descendraient sous la pince, on le lâche donc 13 mm plus haut ; il
# retombe droit tout seul (il ne bascule qu'au-delà de 23° pour la barre, 25° pour le petit rond, par le calcul).
ECART_INCL = 15.0
LEVE_PENCHE = 13.0                                                # mm : 32 (demi-longueur de la barre) × sin 15° + 5 de marge
# Points où le bras pose l'objet pour apprendre sa visée (touche A) : devant le socle, entre les marqueurs.
POINTS_VISEE = [(float(x), float(y)) for y in (250, 290, 330, 370, 410, 445) for x in (-110, 0, 110)]
PRES_DU_SOCLE = 150.0                                             # mm : plus près, c'est le robot lui-même (socle, câbles), jamais un objet
SEUIL_TAILLE = 37.0                                               # mm, largeur mesurée par la pince : en dessous, « petit »
# Tri de Nicolas du 26/11/2026 : la pince lit environ 5 mm de trop (petit rond 28 → 33, hexagone 38 → 41, carré 36 → 43) ;
# avec 32, le petit rond partait chez les gros. 37 passe au milieu de l'écart entre 33 et 41.
ECART_MIN = 55.0                                                  # mm entre deux objets : plus près, la pince ouverte risque de toucher le voisin
ESSAIS_MAX = 2                                                    # tentatives au même endroit avant d'abandonner l'objet
# Option BAC (demande de Nicolas, 26/11/2026) : une zone peut être un bac posé sur la table (réglé par regler_bac.bat, gardé
# dans bacs.json sur le PC). Le bras lâche alors l'objet AU-DESSUS du bac : n'importe quelle inclinaison convient, plus de
# problème de place. Le bas de l'objet passe GARDE_BAC mm au-dessus du bord. Le bac doit être en place AVANT la photo du fond.
FICHIER_BACS = Path(__file__).with_name('bacs.json')
GARDE_BAC = 45.0                # Nicolas, 26/11/2026 : avec 25, une mâchoire frottait sur le bord du bac
def charger_bacs():
    try:
        b = __import__('json').loads(FICHIER_BACS.read_text(encoding='utf-8'))
        return {z: v for z, v in b.items() if z in ZONES and all(k in v for k in ('X', 'Y', 'bord', 'largeur', 'profondeur'))}
    except Exception: return {}
def dans_un_bac(X, Y, bacs, marge=30.0):
    return any(abs(X - b['X']) < b['largeur'] / 2 + marge and abs(Y - b['Y']) < b['profondeur'] / 2 + marge for b in bacs.values())
def pose_dans_bac(bac, incl_prise, hauteur_epaule=179.0, corriger=None):
    """Comment lâcher au-dessus du bac : (point, inclinaison, levée) ou None. L'objet pend sous la pince d'environ la hauteur de
    prise ; on le monte du bord + la garde, en essayant d'abord l'inclinaison de la prise (l'objet descend droit), puis les autres."""
    ordre = sorted(G.INCLINAISONS, key=lambda i: abs(i - incl_prise))
    for i in ordre:
        leve = bac['bord'] + GARDE_BAC + max(0.0, abs(i - incl_prise)) * 0.6       # un objet penché descend un peu plus bas
        for pt in points_du_bac(bac):
            # le bras visera le point CORRIGÉ (correction de visée apprise) : c'est lui qu'on vérifie, exactement comme le fera
            # la pose (tri du 26/11/2026 à 17 h 42 : point bon sans correction, 55 mm plus près avec, hors de portée)
            v = corriger(*pt) if corriger else pt
            try: G.choisir_inclinaison(*v, hauteur_epaule, i, leve); return pt, i, leve
            except G.HorsDePortee: pass
    return None

MARGE_PAROI = 60.0              # mm entre le point de lâcher et la paroi intérieure du bac (demi-pince + jeu ; 45 : la mâchoire frottait)
def points_du_bac(bac, pas=15.0):
    """Les points où lâcher dans le bac, du plus PROCHE du socle au plus loin. Nicolas, 26/11/2026 : bacs de 18 cm de haut posés
    plus loin, le milieu n'était plus atteignable assez haut (« pose dans le bac impossible ») ; tout le fond du bac est bon."""
    dx, dy = max(bac['largeur'] / 2 - MARGE_PAROI, 0.0), max(bac['profondeur'] / 2 - MARGE_PAROI, 0.0)
    nx, ny = int(dx // pas), int(dy // pas)
    pts = [(bac['X'] + i * pas, bac['Y'] + j * pas) for i in range(-nx, nx + 1) for j in range(-ny, ny + 1)]
    return sorted(pts, key=lambda q: math.hypot(*q))

FICHIER_FOND = Path(__file__).resolve().parent.parent / 'camera' / 'fond_table.png'
AIDE = 'F = fond (table VIDE) | A = apprendre la visee (1 objet) | T = TRIER (taille) | 1 = un seul objet | O ouvrir | R repos | ESPACE = ARRET | P photo | Q quitter'

def choisir(objets, rates):
    """L'objet à prendre maintenant : le plus isolé, parmi ceux qui n'ont pas déjà raté ESSAIS_MAX fois au même endroit."""
    candidats = []
    for o in objets:
        if sum(1 for x, y in rates if math.hypot(o['X'] - x, o['Y'] - y) < 25) >= ESSAIS_MAX: continue
        voisin = min([math.hypot(o['X'] - a['X'], o['Y'] - a['Y']) for a in objets if a is not o] or [999.0])
        candidats.append((voisin, o))
    return max(candidats, key=lambda c: c[0]) if candidats else (None, None)

REPOS = {'epaule': EP.REPOS, 'coude': 0.0, 'flexion': 0.0}
# Ouverture à la prise : la largeur vue de l'objet + MARGE_OUVERTURE, pas plus de OUVERTURE_MAX (pour ne pas toucher les voisins ;
# le contrôle des obstacles en tient compte). Nicolas, 26/11/2026 : avec + 30 mm, une mâchoire tombait sur le gros rond (il ne
# restait que 15 à 20 mm de chaque côté pour l'erreur de visée) ; sa pince s'ouvre à 133 mm.
MARGE_OUVERTURE, OUVERTURE_MAX = 55.0, 115.0
def ouverture_prise(o, roulis=0.0):
    larg = o.get('etroit', o['largeur']) if roulis else o['largeur']                      # pince tournée : en travers de l'objet
    return min(OUVERTURE_MAX, max(larg, 30.0) + MARGE_OUVERTURE)

# Rotation du poignet pour un objet ALLONGÉ (la barre de 64 × 26 était prise dans sa longueur, Nicolas 26/11/2026) : la pince tourne
# sur elle-même pour serrer en travers. Seulement si la pince est assez penchée vers le bas : à plat, tourner mettrait une mâchoire
# en dessous de l'autre au lieu de la faire pivoter au-dessus de la table.
ALLONGE_ROTATION = 1.5          # long / étroit au pied, mesuré sur la photo : au-delà, on tourne la pince
LONG_ROTATION = 55.0            # mm : et seulement si l'objet est vraiment long. Tri du 26/11/2026 à 17 h 31 : les ronds de 28 et 40 mm,
                                # vus « 21 × 41 » sur la photo (pied mal vu), faisaient tourner la pince pour rien ; la barre fait 64-77
INCL_ROTATION = 45.0            # degrés : pince au moins aussi penchée pour tourner
ROULIS_MAX = 88.0               # degrés (butées du poignet : ±90)
SENS_ROULIS = 1                 # + = le haut de la pince part à gauche vu de derrière (tester_poignet, 21/11/2026) ; -1 si c'est l'inverse

def roulis_pour(o, incl, socle):
    """De combien tourner la pince (degrés) pour que ses mâchoires serrent l'objet en travers ; 0 s'il n'est pas allongé ou si la
    pince est trop à plat. Vu d'en haut, les mâchoires d'une pince penchée de i et tournée de r serrent dans la direction
    cos r · (travers du bras) + sin r · sin i · (devant) : on cherche r qui donne la direction étroite de l'objet."""
    if o.get('allonge_vraie', 1.0) < ALLONGE_ROTATION or o.get('long', 0.0) < LONG_ROTATION or abs(incl) < INCL_ROTATION: return 0.0
    a, s_ = math.radians(o['axe_court']), math.radians(socle)
    e = (math.cos(a), math.sin(a)); n = (math.cos(s_), -math.sin(s_)); r = (math.sin(s_), math.cos(s_))
    A, B_ = e[0] * n[0] + e[1] * n[1], e[0] * r[0] + e[1] * r[1]
    phi = math.degrees(math.atan2(B_, A * math.sin(math.radians(abs(incl)))))
    if phi > 90: phi -= 180
    if phi <= -90: phi += 180
    if abs(phi) < 10: return 0.0
    return SENS_ROULIS * max(-ROULIS_MAX, min(ROULIS_MAX, phi))

def leve_roulis(ouverture, incl, roulis):
    """De combien saisir plus haut (mm) : pince tournée et penchée, une mâchoire descend plus bas que l'autre."""
    return (ouverture / 2 + 6.0) * abs(math.sin(math.radians(roulis))) * math.cos(math.radians(abs(incl)))
def zone_de(largeur): return 'petit' if largeur < SEUIL_TAILLE else 'gros'

class Trieur(Poste):
    def __init__(self, pointeur, reglage, hauteur=O.HAUTEUR_OBJETS, attendre=False):
        super().__init__(pointeur, reglage, attendre)
        self.hauteur, self.fond, self.objets, self.image = hauteur, None, [], None
        self.demande, self.reponse = threading.Event(), threading.Event()
        self.au_repos, self.tries, self.rates = True, {'petit': 0, 'gros': 0}, []
        self.plan_vocal, self.claude, self.modele_ia = None, None, 'claude-sonnet-5-5'
        self.reco = None                                                # fil de la reconnaissance des formes en cours
        self.formes, self.modele_rapide = [], 'claude-haiku-5-5'      # formes reconnues à l'avance ; modèle des ordres (court, sans image)
        self.deposes = {z: [] for z in ZONES}; self.tenu = None; self.objets_tri, self.objet_pris = [], None; self.rap = None
        self.bacs = charger_bacs()
        for z, b in self.bacs.items(): self.dire(f'Les {PLURIEL[z]} vont dans le bac (X {b["X"]:+.0f}, Y {b["Y"]:.0f}, bord à {b["bord"]:.0f} mm).')
        if FICHIER_FOND.exists(): self.fond = cv2.imread(str(FICHIER_FOND)); self.dire('Photo du fond reprise du dernier essai (F pour la refaire si la caméra a bougé).')

    def dire(self, texte):
        super().dire(texte)
        if getattr(self, 'rap', None): self.rap.journal(texte)

    def annoter(self, image, choisi=None):
        """Une copie de l'image avec les objets reconnus (pour le rapport) ; l'objet choisi en rouge."""
        if image is None or self.h is None: return None
        vue = image.copy()
        for n, o in enumerate(self.objets, 1):
            pts = np.array([T.vers_image(self.h, x, y) for x, y in o['contour']], np.int32); rouge = o is choisi; hp = o.get('portee')
            coul = (0, 0, 255) if rouge else (0, 140, 255) if hp else (0, 255, 255)
            cv2.polylines(vue, [pts], True, coul, 3 if rouge else 2)
            pt = T.vers_image(self.h, o['X'], o['Y']); cv2.circle(vue, pt, 6, (0, 0, 255), -1)
            V.ecrire(vue, f'{n} : {o["largeur"]:.0f} mm  (X {o["X"]:+.0f} Y {o["Y"]:.0f})' + (f' - {hp}' if hp else ''), (pt[0] + 10, pt[1] - 10), coul, 0.55)
        return vue

    def voir(self, image):
        self.image = image.copy()
        centres, contours = super().voir(image)
        if self.fond is not None and self.vus and self.h is not None and self.au_repos and self.fond.shape == image.shape:
            self.objets = [o for o in O.trouver(image, self.fond, self.h, self.reglage, self.hauteur)
                           if not dans_un_bac(o['X'], o['Y'], self.bacs)
                           and not any(abs(math.degrees(math.atan2(o['X'], o['Y'])) - a) < SECTEUR for z, a in ZONES.items() if z not in self.bacs)
                           and math.hypot(o['X'], o['Y']) >= PRES_DU_SOCLE]
            for o in self.objets: o['portee'] = self.portee(o)
            if self.demande.is_set(): self.demande.clear(); self.reponse.set()
        return centres, contours

    def portee(self, o):
        """'' si le bras peut prendre l'objet (correction de visée comprise), sinon ce qu'il faut faire, en clair."""
        try:
            v = C.corriger(o['X'], o['Y'], self.corrections); G.choisir_inclinaison(*v, self.p.c.hauteur); return ''
        except G.HorsDePortee:
            if getattr(self, '_zone', None) is None: self._zone = G.zone_toutes(self.p.c.hauteur)      # calcul long : une fois
            d = math.hypot(*v); mini, maxi = self._zone
            if d < mini: return f'trop pres : eloigne-le de {(mini - d) / 10 + 1:.0f} cm'
            if d > maxi: return f'trop loin : rapproche-le de {(d - maxi) / 10 + 1:.0f} cm'
            return 'hors de portee'
        except Exception: return ''

    def photo_fond(self):
        if self.occupe or not self.au_repos: self.dire('Bras au repos d\'abord (R), table vide.'); return
        if self.image is None or not self.vus: self.dire('Il faut voir les 4 marqueurs pour prendre le fond.'); return
        self.fond = self.image.copy(); cv2.imwrite(str(FICHIER_FOND), self.fond); self.objets = []; self.formes = []
        self.deposes = {z: [] for z in ZONES}                                     # table vide : plus rien de posé dans les zones
        self.dire('Fond enregistré, zones vidées. Pose maintenant les objets sur la table.')

    def regarder(self, delai=8.0):
        """Ramène le socle droit devant (bras au repos, levé : le bras tourné de côté cachait un marqueur à la caméra, essai de
        Nicolas du 26/11/2026), attend une image et renvoie les objets trouvés (copie)."""
        c = self.p.c
        try:
            if abs(A.degres(c.bus.etat(c.socle)['position'] - A.MILIEU)) > 3 and self.p.angles()[0] > 55:
                c._bouger([(c.socle, A.MILIEU)], 'Socle droit devant'); self.p.vider()
        except ErreurServo: pass
        self.au_repos = True; time.sleep(0.6); self.reponse.clear(); self.demande.set()
        if not self.reponse.wait(delai): raise ErreurServo('je ne vois plus les 4 marqueurs, bras au repos : un marqueur est-il caché (bras, main, objet) ou la caméra a-t-elle bougé ?')
        return list(self.objets)

    def etape(self, ok, quoi):
        if self.p.c.arret.is_set(): raise ErreurServo('arrêt demandé')
        if not ok: raise ErreurServo(f'{quoi} n\'a pas pu se faire')

    def _atteignable(self, o):
        try: G.choisir_inclinaison(o['X'], o['Y'], self.p.c.hauteur); return True
        except G.HorsDePortee: return False

    def lacher_dans_bac(self, z, incl, largeur):
        p, c = self.p, self.p.c
        pose = pose_dans_bac(self.bacs[z], incl, c.hauteur, lambda x, y: C.corriger(x, y, self.corrections))
        if not pose: raise ErreurServo(f'Le bac des {PLURIEL[z]} est hors de portée pour cette prise.')
        pt, i, leve = pose
        self.note(posé_en_X=pt[0], posé_en_Y=pt[1], remarque='lâché dans le bac', **{'pince_à_la_pose_(°)': abs(i), 'lâché_plus_haut_(mm)': leve})
        self.dire(f'   {self.quoi(z, largeur)}, je le lâche dans son bac (pince à {abs(i):.0f}°, {leve:.0f} mm au-dessus de la hauteur de prise).')
        plan = p.preparer(*C.corriger(*pt, self.corrections), i, leve)
        if not plan: raise ErreurServo('Pose dans le bac impossible.')
        p.aller(*plan, relever=True); self.etape(p.prise is plan[0], 'le transport')     # bras relevé d'abord : voir aller()
        self.etape(p.descendre(), 'l\'arrivée au-dessus du bac'); self.ouvrir_a(largeur + 25); time.sleep(0.3); self.tenu = None      # pas grande ouverte : les mâchoires toucheraient la paroi
        self.etape(p.monter(), 'la remontée'); self.redresser(); p.repos(); self.tries[z] += 1
        return True

    def place_libre(self, zone, incl):
        """Où poser et comment : (point, inclinaison, levée) ou None. D'abord avec l'inclinaison de la prise (objet posé droit),
        sinon avec 15° de plus ou de moins (objet lâché 13 mm plus haut, il se redresse seul)."""
        l0 = getattr(self, 'leve_prise', 0.0)                                       # saisi plus haut : posé d'autant plus haut
        essais = ((incl, l0),) if getattr(self, 'roulis', 0.0) else ((incl, l0), (incl + ECART_INCL, l0 + LEVE_PENCHE), (incl - ECART_INCL, l0 + LEVE_PENCHE))
        for i, leve in essais:                     # pince tournée : changer l'inclinaison pencherait l'objet de côté
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
                if any(math.hypot(pt[0] - x, pt[1] - y) < LOIN_DES_MARQUEURS for x, y in T.coins_table(self.reglage).values()): continue
                if all(math.hypot(pt[0] - x, pt[1] - y) >= ECART_DEPOT for x, y in self.deposes[zone]):
                    # on vérifie le point que le bras visera vraiment, correction de visée comprise (Nicolas, 26/11/2026 : place
                    # trouvée à 245 mm, corrigée à 235, hors de portée pour la pince à 75° : bras arrêté objet en main)
                    try:
                        v = C.corriger(*pt, self.corrections); pr, ht = G.prise_et_approche(*v, self.p.c.hauteur, incl, leve)
                        pr = dict(pr, socle=G.angles_pour(*v, None, self.p.c.hauteur, incl)['socle']); ht = dict(ht, socle=pr['socle'])
                        if getattr(self, 'tenu', None) is None or self.transport_libre(ht, pr) is None: return pt
                    except G.HorsDePortee: pass
        return None

    def quoi(self, z, largeur):
        """Pourquoi cet objet va là : la consigne dictée, ou sa taille."""
        if self.plan_vocal is not None: return f'{largeur:.0f} mm, rangé selon la consigne'
        return f'{largeur:.0f} mm : c\'est un {z.upper()}'

    def zone_prevue(self, o):
        """Le bac prévu par la consigne dictée pour cet objet (retrouvé par sa place, à 35 mm près), ou None."""
        e = min(self.plan_vocal or [], key=lambda q: math.hypot(q['X'] - o['X'], q['Y'] - o['Y']), default=None)
        return e['zone'] if e and math.hypot(e['X'] - o['X'], e['Y'] - o['Y']) < 35 else None
    def forme_prevue(self, o):
        e = min(self.plan_vocal or [], key=lambda q: math.hypot(q['X'] - o['X'], q['Y'] - o['Y']), default=None)
        return CV.NOMS.get(e['forme'], e['forme']) if e else '?'

    def parler(self, texte):
        """Dit la phrase à voix haute si la parole est branchée (trier_voix.bat ; --muet pour la couper)."""
        if getattr(self, 'parole', None): self.parole.dire(texte)

    def cadres(self, objets):
        """Le rectangle de chaque objet dans la photo (pour les gros plans envoyés à Claude)."""
        out = []
        for o in objets:
            px = np.array([T.vers_image(self.h, x, y) for x, y in o['contour']]); out.append((*px.min(axis=0), *px.max(axis=0)))
        return out

    def forme_connue(self, o):
        """La forme déjà reconnue pour l'objet posé là (à 25 mm près), ou None."""
        f = min(self.formes, key=lambda q: math.hypot(q['X'] - o['X'], q['Y'] - o['Y']), default=None)
        return f if f and math.hypot(f['X'] - o['X'], f['Y'] - o['Y']) < 25 else None

    def retenir_formes(self, objets, reconnus):
        par_n = {e['n']: e for e in reconnus}
        self.formes = [dict(X=o['X'], Y=o['Y'], forme=par_n[n]['forme'], description=par_n[n]['description']) for n, o in enumerate(objets, 1) if n in par_n]

    def formes_maintenant(self):
        """Lance la reconnaissance des formes tout de suite, dans un fil à part, si des objets n'ont pas encore de forme connue.
        Appelé quand Nicolas COMMENCE à parler (choix du 26/11/2026, pour ne payer une analyse que s'il donne un ordre) : elle se
        fait pendant qu'il finit sa phrase et qu'elle est transcrite. Sans effet si une reconnaissance est déjà en cours."""
        if self.reco and self.reco.is_alive(): return
        if self.occupe or not self.au_repos or self.fond is None or self.h is None or self.image is None: return
        objets = list(self.objets)
        if not objets or all(self.forme_connue(o) for o in objets): return
        image = self.image.copy()
        def travail():
            try:
                if self.claude is None: self.claude = CV.client_claude()
                t0 = time.time(); reconnus = CV.reconnaitre(self.claude, CV.planche(image, self.cadres(objets)), len(objets), self.modele_ia)
                self.retenir_formes(objets, reconnus)
                self.dire(f'Formes reconnues en {time.time() - t0:.1f} s : ' + ', '.join(f'{e["n"]} {CV.NOMS.get(e["forme"], e["forme"])}' for e in reconnus))
            except Exception as err: self.dire(f'(formes pas reconnues : {type(err).__name__} : {err})')
        self.reco = threading.Thread(target=travail, daemon=True); self.reco.start()

    def prevoir_formes(self):
        """Fil de fond : dès que les objets sont posés et ne bougent plus (bras au repos), Claude reconnaît leurs formes sur les
        gros plans. Quand l'ordre arrivera, il n'y aura plus de photo à lire : la réponse est bien plus rapide."""
        vu, depuis = None, 0.0
        while True:
            time.sleep(0.5)
            try:
                if self.occupe or not self.au_repos or self.fond is None or self.h is None or not self.vus or self.image is None: vu = None; continue
                objets = [o for o in self.objets]
                if not objets or all(self.forme_connue(o) for o in objets): continue
                signature = sorted((round(o['X'] / 10), round(o['Y'] / 10)) for o in objets)
                if signature != vu: vu, depuis = signature, time.time(); continue
                if time.time() - depuis < 1.5: continue                              # on attend que la main soit sortie du champ
                if self.claude is None: self.claude = CV.client_claude()
                t0 = time.time(); image = self.image.copy()
                reconnus = CV.reconnaitre(self.claude, CV.planche(image, self.cadres(objets)), len(objets), self.modele_ia)
                self.retenir_formes(objets, reconnus)
                self.dire(f'Formes reconnues en {time.time() - t0:.1f} s : ' + ', '.join(f'{e["n"]} {CV.NOMS.get(e["forme"], e["forme"])}' for e in reconnus))
            except Exception as err:
                self.dire(f'(formes pas reconnues à l\'avance : {type(err).__name__} : {err})'); time.sleep(10)

    def consigne(self, texte):
        """Une phrase entendue (ou tapée). « Stop » arrête tout de suite ; le reste est confié à Claude avec la photo de la table."""
        self.dire(f'Entendu : « {texte} »')
        if CV.est_stop(texte):
            if self.occupe: self.p.c.arret.set(); self.dire('ARRÊT demandé à la voix : le bras reste tenu.')
            return
        if self.occupe: self.dire('Je suis occupé : dis « stop » d\'abord, ou attends la fin.'); return
        if self.fond is None or self.h is None or not self.au_repos: self.dire('Il me faut d\'abord la photo du fond (F), bras au repos.'); return
        objets, image = list(self.objets), self.image.copy()
        if not objets: self.dire('Je ne vois aucun objet sur la table.'); return
        t0 = time.time()
        if self.reco and self.reco.is_alive(): self.reco.join(timeout=20)       # la reconnaissance lancée au début de la phrase se termine
        formes = [self.forme_connue(o) for o in objets]
        try:
            if self.claude is None: self.claude = CV.client_claude()
            if all(formes):                      # formes déjà reconnues à l'avance : appel court, sans photo, et Câlin parle dès que sa phrase est écrite
                def tout_de_suite(phrase):
                    self.dire(f'Câlin ({time.time() - t0:.1f} s) : {phrase}'); self.parler(phrase)
                rep = CV.decider(self.claude, texte, objets, formes, self.modele_rapide, tout_de_suite)
            else:
                self.dire('Je regarde la table et je réfléchis...')
                rep = CV.interpreter(self.claude, self.annoter(image), texte, objets, self.modele_ia, CV.planche(image, self.cadres(objets)))
                self.retenir_formes(objets, rep['objets'])
        except Exception as err: self.dire(f'Je n\'ai pas pu demander à Claude ({type(err).__name__} : {err}).'); return
        for e in rep['objets']: self.dire(f'   {e["n"]} : {CV.NOMS.get(e["forme"], e["forme"])} ({e["description"]})')
        if not rep.get('deja_dit'): self.dire(f'Câlin ({time.time() - t0:.1f} s) : {rep["reponse"]}'); self.parler(rep['reponse'])
        if rep['action'] == 'rien': return
        apres = rep.get('apres', '')
        self.rates = []
        if rep['action'] == 'taille': self.plan_vocal = None
        else: self.plan_vocal = CV.plan_de(rep, objets)
        def geste():
            fini = False
            try: self.trier(None); fini = not self.p.c.arret.is_set()
            finally: self.au_repos = True; self.plan_vocal = None
            if fini and apres: self.dire(f'Câlin : {apres}'); self.parler(apres)
        self._lancer('tri à la voix', geste)

    def apprendre_visee(self):
        """Le bras apprend SEUL où il arrive vraiment (demande de Nicolas, 26/11/2026 : « quand il rate, il n'apprend pas »).
        Il prend l'unique objet de la table, le pose sur un point choisi, recule, et la caméra regarde où l'objet est vraiment :
        l'écart entre le point visé et l'endroit où l'objet se retrouve est la correction de visée de cet endroit. Puis il le
        reprend là où il est et recommence plus loin. Les points sont visités de proche en proche, pour que la pince garde
        (à 15° près) l'inclinaison de la prise. À la fin, les corrections apprises remplacent les anciennes (gardées à côté)."""
        p, c = self.p, self.p.c; h = c.hauteur
        p.repos(); self.redresser()
        def seul():
            objs = self.regarder()
            if len(objs) != 1: raise ErreurServo(f'pour apprendre la visée, il faut UN SEUL objet sur la table (un rond de préférence), j\'en vois {len(objs)}')
            return objs[0]
        o = seul(); nouvelles, erreurs, rates, k = [], [], 0, 0
        reste = [pt for pt in POINTS_VISEE if not dans_un_bac(*pt, self.bacs, 70.0)
                 and all(math.hypot(pt[0] - x, pt[1] - y) >= LOIN_DES_MARQUEURS for x, y in T.coins_table(self.reglage).values())]
        self.dire(f'J\'apprends la visée sur {len(reste)} points, avec cet objet. ESPACE pour arrêter.')
        while reste:
            visee = C.corriger(o['X'], o['Y'], self.corrections)
            try: incl_o = G.choisir_inclinaison(*visee, h)[0]
            except G.HorsDePortee: raise ErreurServo('l\'objet est hors de portée : mets-le vers le milieu de la table, puis A')
            cands = []
            for pt in reste:                                  # où le poser : même inclinaison si possible, sinon 15° d'écart, au plus près
                q = C.corriger(*pt, self.corrections)
                try:
                    ip = G.choisir_inclinaison(*q, h)[0]
                    if abs(ip - incl_o) > ECART_INCL:           # trop d'écart : on le pose là-bas avec l'inclinaison de la prise, si elle y passe
                        G.prise_et_approche(*q, h, incl_o, 0.0); ip = incl_o; rang = 2
                    else:
                        rang = int(ip != incl_o); G.prise_et_approche(*q, h, ip, 0.0 if ip == incl_o else LEVE_PENCHE)
                    cands.append((rang, abs(math.hypot(*pt) - math.hypot(o['X'], o['Y'])), pt, q, ip))
                except G.HorsDePortee: continue
            if not cands: self.dire(f'   Les {len(reste)} points restants ne sont pas atteignables d\'ici : je m\'arrête là.'); break
            _, _, pt, q, ip = min(cands); reste.remove(pt); k += 1
            self.dire(f'Point {k} : je prends l\'objet en X {o["X"]:+.0f}, Y {o["Y"]:.0f} pour le poser en X {pt[0]:+.0f}, Y {pt[1]:.0f}.')
            plan = p.preparer(*visee)
            if not plan: raise ErreurServo('prise impossible')
            self.au_repos = False; incl_prise = p.incl
            self.ouvrir_a(ouverture_prise(o)); p.aller(*plan); self.etape(p.prise is plan[0], 'l\'approche'); self.etape(p.descendre(), 'la descente')
            tenu, largeur = self.serrer(); self.etape(p.monter(), 'la remontée')
            if not tenu:
                self.ouvrir_a(ouverture_prise(o)); p.repos(); rates += 1; reste.append(pt)
                if rates >= 3: raise ErreurServo('3 prises ratées : la correction actuelle est trop fausse pour démarrer. Fais UN point à la main dans viser_camera (flèches puis C) près de l\'objet, puis reviens faire A.')
                self.dire('   Prise ratée : je regarde à nouveau.'); o = seul(); continue
            plan2 = p.preparer(*q, ip, 0.0 if ip == incl_prise else LEVE_PENCHE)
            if not plan2: raise ErreurServo('pose impossible (objet en main : O pour ouvrir, bras tenu)')
            p.aller(*plan2); self.etape(p.prise is plan2[0], 'le transport'); self.etape(p.descendre(), 'la pose')
            self.ouvrir_a(max(largeur, 20.0) + 20); self.etape(p.monter(), 'la remontée'); p.repos()
            o = seul(); arrive = (o['X'], o['Y']); e = math.hypot(arrive[0] - pt[0], arrive[1] - pt[1])
            if e > 90: raise ErreurServo(f'l\'objet est à {e:.0f} mm du point visé : il a roulé ou il est tombé. Rien n\'est enregistré pour ce point ; remets-le debout puis A.')
            nouvelles = C.apprendre(nouvelles, arrive, q); erreurs.append(e)
            self.dire(f'   Visé X {pt[0]:+.0f}, Y {pt[1]:.0f} → arrivé en X {arrive[0]:+.0f}, Y {arrive[1]:.0f} : {e:.0f} mm d\'écart ({C.en_clair(pt, arrive)}).')
        if len(nouvelles) < 4: self.dire(f'Seulement {len(nouvelles)} point(s) appris : il en faut 4. Les corrections ne changent pas.'); return
        C.FICHIER.with_name('correction_point_avant.json').write_text(__import__('json').dumps(self.corrections, indent=1), encoding='utf-8')
        # 8 points mesurés ou plus : ils remplacent tout. Moins : on garde aussi les anciens points qui sont loin des nouveaux.
        gardes = [] if len(nouvelles) >= 8 else [a for a in self.corrections if all(math.hypot(a['X'] - n['X'], a['Y'] - n['Y']) > 60 for n in nouvelles)]
        self.corrections = nouvelles + gardes; C.enregistrer(self.corrections)
        self.dire(f'Visée apprise sur {len(nouvelles)} points{f" ({len(gardes)} anciens gardés)" if gardes else ""}. Avec les corrections qu\'il avait AU DÉPART, l\'écart était de {sum(erreurs) / len(erreurs):.0f} mm en moyenne '
                  f'(pire : {max(erreurs):.0f} mm). Refais A : l\'écart mesuré sera celui des nouvelles corrections.')

    def tourner(self, angle):
        """Tourne la pince sur elle-même (bras en l'air, au repos ou au-dessus du point). La pose se fera pince tournée aussi."""
        c = self.p.c; c._poignet(angle); self.p.vider(); self.p.roulis_permis = abs(angle) > 15

    def redresser(self):
        """Remet la pince droite, pince vide et remontée, avant le repos."""
        c = self.p.c; self.roulis = 0.0; self.leve_prise = 0.0
        if c.poignet and abs(c._roulis()) > 3: c._poignet(0); self.p.vider()
        self.p.roulis_permis = False

    def serrer(self):
        c = self.p.c; r = c.reglages; c.bus.tenir(c.pince)
        texte, pos, tenu = c.bus.serrer(c.pince, c.ferme, r['serrage_doux'], maintien=min(r['maintien'], r['serrage_doux']))
        largeur = LP.ecart(pos, c.ouvert); self.dire(f'Serrer : {texte}' + (f' · largeur ≈ {largeur:.0f} mm' if tenu else ''))
        return tenu, largeur

    def obstacles(self, objets, sauf=None):
        """Les objets que le bras ne doit pas heurter : ceux de la table (sauf celui qu'il prend) et ceux déjà posés."""
        # Les gestes du bras sont calculés aux points CORRIGÉS (correction de visée apprise) : les obstacles doivent l'être aussi.
        # Sinon, avec une correction de 5 cm, le calcul croit le bras 5 cm plus court que les voisins vus par la caméra : faux
        # « gêné », ou contact non vu (trouvé en préparant le morpion, 26/11/2026). Le nom garde la position vue.
        vise = lambda x, y: C.corriger(x, y, self.corrections)
        obs = []
        for o in objets:
            if o is sauf: continue
            x, y = vise(o['X'], o['Y'])
            obs.append({'X': x, 'Y': y, 'rayon': min(max(o['largeur'], o['longueur']), 70.0) / 2, 'hauteur': self.hauteur, 'nom': f'X {o["X"]:+.0f} Y {o["Y"]:.0f}'})
        for z in self.deposes:
            for x0, y0 in self.deposes[z]:
                x, y = vise(x0, y0); obs.append({'X': x, 'Y': y, 'rayon': 22.0, 'hauteur': self.hauteur, 'nom': f'posé en X {x0:+.0f} Y {y0:.0f}'})
        return obs

    def libre_pour_prendre(self, o, objets):
        """(None, plan) si le geste de prise ne heurte rien ; (obstacle, None) sinon ; (None, None) si hors de portée."""
        visee = C.corriger(o['X'], o['Y'], self.corrections)
        try: incl, prise, haut = G.choisir_inclinaison(*visee, self.p.c.hauteur)
        except G.HorsDePortee: return None, None
        rl = roulis_pour(o, incl, prise['socle']) if self.p.c.poignet else 0.0
        gene = OB.geste_libre(prise['socle'], [REPOS, haut, prise], self.obstacles(objets, o), self.p.c.hauteur, ouverture_prise(o, rl), roulis=rl)
        return gene, (None if gene else (incl, prise, haut))

    def choisir(self, objets):
        """L'objet à prendre : le plus isolé parmi ceux qu'on peut prendre SANS heurter un autre objet (demande de Nicolas)."""
        _, premier = choisir(objets, self.rates)
        if premier is None: return None
        restants = [o for o in objets if sum(1 for x, y in self.rates if math.hypot(o['X'] - x, o['Y'] - y) < 25) < ESSAIS_MAX
                    and (self.plan_vocal is None or self.zone_prevue(o))]               # consigne dictée : seulement les objets nommés
        if not restants: return None
        genes = []
        for o in sorted(restants, key=lambda o: -min([math.hypot(o['X'] - a['X'], o['Y'] - a['Y']) for a in objets if a is not o] or [999.0])):
            gene, plan = self.libre_pour_prendre(o, objets)
            if gene is None: return o                                                # libre, ou hors de portée (le message suivra)
            genes.append((o, gene))
        for o, g in genes: self.dire(f'   L\'objet en X {o["X"]:+.0f}, Y {o["Y"]:.0f} est gêné : le bras toucherait l\'objet {g["nom"]}.')
        raise ErreurServo('tous les objets restants sont gênés par un voisin : écarte-les (6 cm au moins, et rien entre le socle et un objet), puis T.')

    def un_objet(self, objets):
        """Prend l'objet le plus isolé et le pose dans sa zone. Renvoie True si un objet a été trié, False s'il n'y en a plus."""
        p, c = self.p, self.p.c
        o = self.choisir(objets)
        if o is None: return False
        voisin = min([math.hypot(o['X'] - a['X'], o['Y'] - a['Y']) for a in objets if a is not o] or [999.0])
        self.objets_tri, self.objet_pris = objets, o
        if self.rap:
            n = self.rap.nouvel_essai(o); self.rap.note(longueur_vue=o['longueur']); self.rap.photo(f'objet_{n:02d}_avant', self.image, self.annoter(self.image, o))
        if voisin < ECART_MIN: self.dire(f'Attention : l\'objet en X {o["X"]:+.0f} Y {o["Y"]:.0f} a un voisin à {voisin:.0f} mm, la pince pourrait le toucher.')
        visee = C.corriger(o['X'], o['Y'], self.corrections)
        self.dire(f'Je prends l\'objet en X {o["X"]:+.0f}, Y {o["Y"]:.0f} (vu {o["largeur"]:.0f} mm de large).')
        plan = p.preparer(*visee); rl, self.leve_prise = 0.0, 0.0
        if plan and c.poignet:
            rl = roulis_pour(o, p.incl, plan[0]['socle'])
            if rl:
                lv = leve_roulis(ouverture_prise(o, rl), p.incl, rl); incl0 = p.incl
                plan2 = p.preparer(*visee, incl0, lv)
                if plan2: plan, self.leve_prise = plan2, lv
                else: rl = 0.0; p.preparer(*visee)                                      # trop haut pour cette distance : prise ordinaire
        self.note(visée_X=visee[0], visée_Y=visee[1])
        if not plan:
            self.note(résultat='hors de portée'); self.rates += [(o['X'], o['Y'])] * ESSAIS_MAX
            if math.hypot(visee[0] - o['X'], visee[1] - o['Y']) > 20 and self._atteignable(o):
                self.dire(f'   C\'est la CORRECTION de visée apprise qui l\'envoie hors de portée (elle vise {C.en_clair((o["X"], o["Y"]), visee)}). '
                          'Si tu as remonté des pièces depuis, refais la correction dans viser_camera (E deux fois, puis flèches + C, près ET loin).')
            else: self.dire('   Hors de portée : je le laisse.')
            return True
        self.au_repos = False
        self.note(**{'pince_à_la_prise_(°)': abs(p.incl), 'ouverture_(mm)': ouverture_prise(o, rl)})
        if rl:
            self.dire(f'   Objet allongé ({o["etroit"]:.0f} × {o["long"]:.0f} mm au pied) : je tourne la pince de {rl:+.0f}° pour le serrer en travers'
                      + (f', et je le saisis {self.leve_prise:.0f} mm plus haut' if self.leve_prise >= 1 else '') + '.')
            self.note(remarque=f'pince tournée de {rl:+.0f}°'); self.tourner(rl)
        self.roulis = rl
        self.ouvrir_a(ouverture_prise(o, rl))
        p.aller(*plan); self.etape(p.prise is plan[0], 'l\'approche')
        self.etape(p.descendre(), 'la descente')
        tenu, largeur = self.serrer(); self.tenu = (p.incl, G.hauteur_prise(p.incl), self.hauteur, max(largeur, 20.0) / 2 + 2)
        self.etape(p.monter(), 'la remontée')
        self.note(**{'largeur_mesurée_(mm)': largeur if tenu else 0.0})
        if not tenu:
            self.note(résultat='raté : rien entre les doigts')
            self.rates.append((o['X'], o['Y'])); self.suite_ratee += 1; self.ouvrir_a(ouverture_prise(o, rl))
            self.dire('   Raté : rien entre les doigts. Je regarde à nouveau.'); self.redresser(); p.repos()
            if self.suite_ratee >= 3: raise ErreurServo('3 prises ratées de suite : la visée est sans doute décalée. Refais la correction aux flèches dans viser_camera, puis reviens.')
            return True
        self.suite_ratee = 0
        z = zone_de(largeur); incl = p.incl; self.plan_prise = plan
        prevu = self.zone_prevue(o) if self.plan_vocal is not None else None
        if prevu:
            z = prevu; self.dire(f'   Consigne : {self.forme_prevue(o)} → bac de {"gauche" if z == "petit" else "droite"} (largeur lue {largeur:.0f} mm).')
        self.note(catégorie=z)
        try:
            r = self.poser(z, incl, largeur); self.note(résultat='trié'); return r
        except ErreurServo as err:
            if c.arret.is_set(): raise
            self.dire(f'   {err} Je le repose là où je l\'ai pris.'); self.rates += [(o['X'], o['Y'])] * ESSAIS_MAX
            self.note(résultat='reposé où il a été pris', remarque=str(err))
            self.reposer_ou_pris(); return True

    def controle_photo(self, e):
        """Regarde sur la photo d'après si l'objet a quitté sa place et s'il est bien DEBOUT là où il a été posé : on compare sa forme
        vue d'en haut à celle du départ (un objet couché paraît bien plus long). Tout est vu, zones de dépôt comprises."""
        try: tous = O.trouver(self.image, self.fond, self.h, self.reglage, self.hauteur)
        except Exception: return
        pres = lambda x, y, r: min(tous, key=lambda o: math.hypot(o['X'] - x, o['Y'] - y), default=None) if any(math.hypot(o['X'] - x, o['Y'] - y) < r for o in tous) else None
        if e.get('résultat') == 'trié' and 'posé en X' in e and 'lâché dans le bac' not in str(e.get('remarque', '')):
            o = pres(e['posé en X'], e['posé en Y'], 35)
            x0, y0, x1, y1 = O.cadre(self.reglage); u, v = T.vers_image(self.h, e['posé en X'], e['posé en Y'])
            visible = x0 + 25 < e['posé en X'] < x1 - 25 and y0 + 25 < e['posé en Y'] < y1 - 25 and 20 < u < self.image.shape[1] - 20 and 20 < v < self.image.shape[0] - 20
            if o is None and not visible: verdict = 'posé hors de la vue de la caméra : à vérifier à l\'œil'
            elif o is None: verdict = 'introuvable à l\'endroit de la pose (tombé ? roulé ?)'
            else:
                avant = sorted((e['largeur vue'], e.get('longueur vue', e['largeur vue']))); apres = sorted((o['largeur'], o['longueur']))
                ecart = math.hypot(o['X'] - e['posé en X'], o['Y'] - e['posé en Y'])
                debout = apres[1] <= avant[1] * 1.35 + 12 and apres[0] <= avant[0] * 1.35 + 12
                verdict = ((f'debout, à {ecart:.0f} mm du point visé' if ecart <= 25 else f'à {ecart:.0f} mm du point visé : glissé, roulé ou mal vu ?') if debout else f'forme différente ({apres[0]:.0f} × {apres[1]:.0f} mm au lieu de {avant[0]:.0f} × {avant[1]:.0f}) : couché ou renversé ?')
            if pres(e['X vu'], e['Y vu'], 25): verdict += ' ; un objet est encore à l\'endroit de la prise'
        elif e.get('résultat', '').startswith('raté') or e.get('résultat') == 'reposé où il a été pris':
            o = pres(e['X vu'], e['Y vu'], 40)
            verdict = 'toujours à sa place' if o and math.hypot(o['X'] - e['X vu'], o['Y'] - e['Y vu']) < 15 else (f'déplacé de {math.hypot(o["X"] - e["X vu"], o["Y"] - e["Y vu"]):.0f} mm' if o else 'disparu de sa place (renversé ?)')
        else: return
        e['contrôle photo'] = verdict; self.dire(f'   Contrôle sur la photo : {verdict}.')

    def note(self, **champs):
        if self.rap: self.rap.note(**champs)

    def ouvrir_a(self, mm):
        """Ouvre la pince à `mm` d'écart seulement (pas grande ouverte : elle toucherait les voisins)."""
        c = self.p.c; pos = LP.position_pour(mm, c.ouvert, c.ferme)
        c.bus.limiter_force(c.pince, PI.FORCE_MOUVEMENT); c.bus.tenir(c.pince)
        self.dire(f'   Pince ouverte à {LP.ecart(pos, c.ouvert):.0f} mm : ' + c.bus.aller(c.pince, pos, charge_max=PI.CHARGE_BLOCAGE))

    def transport_libre(self, haut, prise):
        """Le trajet objet en main, de la remontée jusqu'à la pose, ne heurte rien ? Renvoie l'obstacle touché ou None."""
        p = self.p; depart = p.haut or haut
        obs = self.obstacles(self.objets_tri, self.objet_pris)
        socle0 = getattr(p, 'prise', None)['socle'] if getattr(p, 'prise', None) else prise['socle']
        g = OB.geste_libre(socle0, [depart, REPOS], obs, p.c.hauteur, 0.0, self.tenu)
        return g or OB.geste_libre(prise['socle'], [REPOS, haut, prise], obs, p.c.hauteur, 0.0, self.tenu)

    def reposer_ou_pris(self):
        """Le bras tient un objet qu'il ne peut pas poser dans sa zone : il le remet exactement où il l'a pris (même point, même
        inclinaison : c'est toujours possible, il venait de là), ouvre, remonte, revient au repos."""
        p, c = self.p, self.p.c
        p.aller(*self.plan_prise); self.etape(p.prise is self.plan_prise[0], 'le retour au point de prise')
        self.etape(p.descendre(), 'la descente'); self.ouvrir_a(2 * self.tenu[3] + 16); self.tenu = None
        self.etape(p.monter(), 'la remontée'); self.redresser(); p.repos()

    def poser(self, z, incl, largeur):
        p, c = self.p, self.p.c
        if z in self.bacs: return self.lacher_dans_bac(z, incl, largeur)
        place = self.place_libre(z, incl)
        spot, incl_pose, leve = place if place else (None, None, None)
        if spot is None: raise ErreurServo(f'Plus de place dans la zone des {PLURIEL[z]} à la bonne distance.')
        cote = "gauche" if ZONES[z] < 0 else "droite"
        if leve and incl_pose != incl: self.dire(f'   {self.quoi(z, largeur)}, je le pose à {cote}, pince à {abs(incl_pose):.0f}° (prise à {abs(incl):.0f}°) : lâché {leve:.0f} mm plus haut, il se redresse seul.')
        else: self.dire(f'   {self.quoi(z, largeur)}, je le pose à {cote}, pince inclinée comme à la prise ({abs(incl):.0f}°).')
        self.note(posé_en_X=spot[0], posé_en_Y=spot[1], **{'pince_à_la_pose_(°)': abs(incl_pose), 'lâché_plus_haut_(mm)': leve})
        plan = p.preparer(*C.corriger(*spot, self.corrections), incl_pose, leve)
        if not plan: raise ErreurServo('Pose impossible à cet endroit.')
        p.aller(*plan); self.etape(p.prise is plan[0], 'le transport')
        self.etape(p.descendre(), 'la pose'); self.ouvrir_a(2 * self.tenu[3] + 16)
        self.etape(p.monter(), 'la remontée'); self.redresser(); p.repos(); self.tries[z] += 1; self.deposes[z].append(spot); self.tenu = None
        return True

    def trier(self, combien=None):
        try:
            cx, cy, cz, _ = O.camera(self.h, (self.image.shape[1], self.image.shape[0]))
            cam = f'{cz / 10:.0f} cm au-dessus de la table (X {cx:+.0f}, Y {cy:.0f})'
        except Exception: cam = 'inconnue'
        self.rap = RT.Rapport({'mode': 'un seul objet' if combien == 1 else 'tout trier', 'caméra calculée': cam,
                               'corrections de visée apprises': len(self.corrections), 'seuil petit / gros (mm)': SEUIL_TAILLE,
                               'zones': ', '.join(f'{PLURIEL[z]} ' + ('dans le bac' if z in self.bacs else f'à {a:+.0f}°') for z, a in ZONES.items()),
                               'hauteur des objets (mm)': self.hauteur})
        conclusion = ''
        try:
            conclusion = self._trier(combien)
        except ErreurServo as err:
            conclusion = f'ARRÊT : {err}'; raise
        finally:
            try:
                reste = self.regarder() if not self.p.c.arret.is_set() else self.objets
                self.rap.photo('fin', self.image, self.annoter(self.image))
            except ErreurServo: pass
            d = self.rap.fermer(conclusion); self.rap = None
            self.dire(f'Rapport enregistré : bras\\rapports\\{d.name}')

    def _trier(self, combien=None):
        n = 0; self.suite_ratee = 0; avant = dict(self.tries)       # les compteurs courent depuis le lancement : on ne compte que CE tri
        self.p.repos(); self.redresser()                              # un arrêt a pu laisser la pince tournée
        objets = self.regarder(); self.rap.photo('00_debut', self.image, self.annoter(self.image))
        loin = [o for o in objets if o.get('portee')]
        if loin:                                                      # demande de Nicolas (26/11/2026) : le dire AVANT de commencer
            self.dire(f'⚠️  AVANT DE COMMENCER : {len(loin)} objet(s) hors de portée, je ne les toucherai pas (en orange à l\'écran) :')
            for o in loin:
                self.dire(f'   objet en X {o["X"]:+.0f}, Y {o["Y"]:.0f} : {o["portee"].replace("pres", "près").replace("eloigne", "éloigne").replace("portee", "portée")}')
                self.rates += [(o['X'], o['Y'])] * ESSAIS_MAX
            if len(loin) == len(objets): raise ErreurServo('aucun objet à portée : déplace-les (voir ci-dessus), puis T.')
        while combien is None or n < combien:
            if not objets: break
            self.dire(f'{len(objets)} objet(s) sur la table.')
            if not self.un_objet(objets): break
            objets = self.regarder()                                          # bras revenu au repos : la table après ce geste
            if self.rap.essai:
                self.rap.photo(f'objet_{self.rap.essai["n"]:02d}_apres', self.image, self.annoter(self.image))
                self.controle_photo(self.rap.essai)
            n += 1
        reste = [o for o in self.regarder()]
        txt = (f'Fini : {self.tries["petit"] - avant["petit"]} petit(s) à gauche, {self.tries["gros"] - avant["gros"]} gros à droite.' + (f' {len(reste)} objet(s) laissé(s) (hors de portée ou ratés).' if reste and combien is None else ''))
        self.dire(txt); return txt

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
        if kk == 'a':
            if self.fond is None: self.dire('Il faut d\'abord la photo du fond : table VIDE, bras au repos, touche F.'); return True
            def geste():
                try: self.apprendre_visee()
                finally: self.au_repos = True
            self.rates = []; self._lancer('apprentissage de la visée', geste); return True
        if kk == 'r':
            def repos():
                self.p.repos(); self.redresser(); self.au_repos = True
            self.plan = None; self._lancer('retour au repos', repos); return True
        if kk == 'o':
            self._lancer('la pince', lambda: (self.p.c._pince('o'), self.p.vider())); return True
        if kk in ('d', 'm', 'c', 'e', 's', 'i', 'j', 'l', 'u', 'n', '\r', '\n') or k in FLECHES:
            return True                                                  # gestes à la main : dans viser_camera, pas ici
        return super().touche(k)

    def clic(self, x, y): self.dire('Ici on ne clique pas : F (fond), puis T pour trier. Pour viser à la main : viser_camera.')

    def dessiner(self, image, centres, contours):
        if self.h is not None:
            for nom, b in self.bacs.items():
                w, d = b['largeur'] / 2, b['profondeur'] / 2
                pts = np.array([T.vers_image(self.h, b['X'] + sx * w, b['Y'] + sy * d) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))], np.int32)
                cv2.polylines(image, [pts], True, (255, 160, 0), 2)
                # un bac hors du champ de la caméra (Nicolas, 26/11/2026 : « on ne voit pas les bacs ») : flèche au bord de l'image
                H, W_ = image.shape[:2]; u, v = T.vers_image(self.h, b['X'], b['Y'])
                texte = f'bac des {PLURIEL[nom]} (bord {b["bord"]:.0f} mm)'
                if 0 <= u < W_ and 0 <= v < H: V.ecrire(image, texte, (max(5, min(u - 80, W_ - 260)), v), (255, 200, 80), 0.6)
                else:
                    bu, bv = min(max(u, 30), W_ - 30), min(max(v, 60), H - 60)
                    cv2.arrowedLine(image, (int(bu - (u - bu) * 0.0 - (60 if u >= W_ else -60 if u < 0 else 0)), int(bv - (60 if v >= H else -60 if v < 0 else 0))), (int(bu), int(bv)), (255, 160, 0), 4, tipLength=0.4)
                    V.ecrire(image, texte, (max(5, min(int(bu) - 120, W_ - 300)), int(bv) + 30), (255, 200, 80), 0.6)
            for nom, a in ZONES.items():
                if nom in self.bacs: continue
                for b in (a - SECTEUR, a + SECTEUR):
                    cv2.line(image, T.vers_image(self.h, *G.point_dans_direction(b, 190)), T.vers_image(self.h, *G.point_dans_direction(b, 480)), (255, 160, 0), 2)
                V.ecrire(image, f'zone des {PLURIEL[nom]}', T.vers_image(self.h, *G.point_dans_direction(a, 480)), (255, 200, 80), 0.6)
                for x, y in self.deposes[nom]: cv2.circle(image, T.vers_image(self.h, x, y), 8, (255, 160, 0), 2)
            for n, o in enumerate(self.objets, 1):
                pts = np.array([T.vers_image(self.h, x, y) for x, y in o['contour']], np.int32); hp = o.get('portee')
                coul = (0, 140, 255) if hp else (0, 255, 255)
                cv2.polylines(image, [pts], True, coul, 2)
                pt = T.vers_image(self.h, o['X'], o['Y']); cv2.circle(image, pt, 6, (0, 0, 255), -1)
                fc = self.forme_connue(o) if self.formes else None
                V.ecrire(image, f'{n} : ' + (sans_accents(CV.NOMS.get(fc['forme'], fc['forme'])) + ', ' if fc else '') + f'{o["largeur"]:.0f} mm' + (f' - {hp}' if hp else ''), (pt[0] + 10, pt[1] - 10), coul, 0.6)
        haut = image.shape[0]; pas = int(30 * haut / 720)
        etat = ('Le bras trie... ESPACE = ARRET' if self.occupe else 'Photo du fond manquante : table VIDE, bras au repos, touche F' if self.fond is None
                else f'{len(self.objets)} objet(s) vu(s)' + (f', dont {sum(1 for o in self.objets if o.get("portee"))} HORS DE PORTEE (en orange)' if any(o.get('portee') for o in self.objets) else '') + '. T = trier' if self.vus else 'Marqueurs caches : dernier reperage garde')
        V.ecrire(image, sans_accents(etat), (10, 40), (0, 200, 255) if self.occupe or self.fond is None else (120, 255, 120))
        if self.fond is not None and getattr(O.trouver, 'lumiere', None):
            V.ecrire(image, 'La lumiere a change depuis la photo du fond : retire les objets, puis F', (10, 80), (80, 80, 255))
            for X, Y, _ in O.trouver.lumiere:
                if self.h is not None: V.ecrire(image, '?', T.vers_image(self.h, X, Y), (80, 80, 255), 1.0)
        V.ecrire(image, AIDE, (10, haut - 14), (255, 255, 255), 0.55)
        m = getattr(self, 'micro', None)
        if m:                                                                 # niveau du micro : une barre, et le trait du seuil
            x0, y0, L = image.shape[1] - 330, 30, 300; plein = 0.3
            cv2.rectangle(image, (x0, y0), (x0 + L, y0 + 16), (60, 60, 60), -1)
            cv2.rectangle(image, (x0, y0), (x0 + int(L * min(m['volume'] / plein, 1.0)), y0 + 16), (80, 220, 80) if m['parle'] else (200, 200, 200), -1)
            xs = x0 + int(L * min(m['seuil'] / plein, 1.0)); cv2.line(image, (xs, y0 - 5), (xs, y0 + 21), (0, 0, 255), 2)
            V.ecrire(image, 'micro : ' + ('JE T ENTENDS' if m['parle'] else m['etat']), (x0, y0 + 45), (80, 220, 80) if m['parle'] else (220, 220, 220), 0.55)
        for n, m in enumerate(reversed(self.messages[-3:])):
            V.ecrire(image, sans_accents(m)[:110], (10, haut - 14 - (n + 1) * pas), (0, 230, 255) if n == 0 else (190, 190, 190), 0.55)

def verifier_zones(hauteur_epaule=179.0):
    """Chaque zone doit accepter toutes les inclinaisons de prise : sinon un objet pris pourrait ne pas pouvoir y être posé."""
    bacs = charger_bacs(); corr = C.charger()
    for nom, b in bacs.items():
        for incl in G.INCLINAISONS:
            if not pose_dans_bac(b, incl, hauteur_epaule, lambda x, y: C.corriger(x, y, corr)): raise G.HorsDePortee(f'bac des {PLURIEL[nom]} : impossible d\'y lâcher un objet pris pince à {abs(incl)}° (relance regler_bac.bat)')
    for nom, a in ZONES.items():
        if nom in bacs: continue
        for incl in G.INCLINAISONS:
            if not G.bande(incl, hauteur_epaule, a): raise G.HorsDePortee(f'zone des {PLURIEL[nom]} ({a:+.0f}°) : impossible de poser pince inclinée de {abs(incl)}°')

def ecouter_consignes(t, a):
    """Fil d'écoute : chaque phrase entendue (ou tapée) est passée au trieur. Le micro est ouvert en continu."""
    try:
        if a.clavier:
            while True: t.consigne(input('Consigne (ex. « range les ronds à gauche et le reste à droite », « stop ») : ').strip())
        sys.path.insert(0, str(CV.TETE)); import ecouter as E
        modele = None
        if a.ecoute != 'whisper':                                             # transcription dans le nuage : 2 à 3 fois plus rapide que Whisper sur le PC
            try:
                import parler
                cle = parler.lire_cles()[0].get('ELEVENLABS_API_KEY')
                if cle: modele = E.ScribeElevenLabs(cle); print('Écoute : ElevenLabs (rapide). Pour Whisper sur le PC : --ecoute whisper')
            except Exception as err: print(f'Écoute ElevenLabs indisponible ({err}) : Whisper sur le PC.')
        oreille = E.Oreille(modele or E.charger_modele(a.modele), a.micro, a.seuil)
        # Nicolas, 26/11/2026 : bruit de fond 0,048 → seuil 0,145 (3 fois le bruit) : sa voix ne le dépassait jamais, rien n'était
        # entendu. Quand le micro est bruyant, on se contente de 1,6 fois le bruit ; et le niveau du micro s'affiche à l'écran.
        if a.seuil is None and oreille.seuil > 0.05:
            oreille.seuil = max(oreille.seuil / 3 * 1.6, 0.02); oreille.decoupeur = E.Decoupeur(oreille.seuil)
            print(f'Micro bruyant : seuil ramené à {oreille.seuil:.3f} (réglable : trier_voix.bat --seuil 0.06 ; autre micro : --micro N)')
        t.micro = {'volume': 0.0, 'seuil': oreille.seuil, 'parle': False, 'etat': 'ecoute'}
        t.dire('Je t\'écoute : dis par exemple « range les ronds à gauche et le reste à droite », ou « stop ».')
        while True:
            bloc = oreille.file.get()
            par = getattr(t, 'parole', None)
            if par and (par.en_cours or par.vient_de_parler):               # Câlin parle : il ne doit pas s'écouter lui-même
                if not par.en_cours: par.vient_de_parler = False
                t.micro.update(etat='Calin parle', parle=False); oreille.vider(); continue
            if t.micro['etat'] == 'Calin parle': t.micro['etat'] = 'ecoute'
            t.micro['volume'] = max(float(np.sqrt(np.mean(bloc ** 2))), t.micro['volume'] * 0.85)      # retombe doucement, lisible
            avant = oreille.decoupeur.en_cours
            son = oreille.decoupeur.ajouter(bloc); t.micro['parle'] = oreille.decoupeur.en_cours
            if oreille.decoupeur.en_cours and not avant and a.formes == 'parole': t.formes_maintenant()   # il commence à parler : on regarde les formes
            if son is None: continue
            t.micro['etat'] = 'je transcris'; t1 = time.time(); texte = E.comprendre(oreille.modele, son); t.micro['etat'] = 'ecoute'
            print(f'   (phrase transcrite en {time.time() - t1:.1f} s)')
            if not E.phrase_valable(texte): t.dire('(j\'ai entendu un bruit, pas une phrase)'); continue
            t.micro['etat'] = 'je reflechis'; t.consigne(texte); t.micro['etat'] = 'ecoute'
            oreille.vider()                                               # ce qui s'est dit pendant que je réfléchissais est oublié
    except Exception as err: t.dire(f'L\'écoute s\'est arrêtée ({type(err).__name__} : {err}). Les touches marchent toujours.')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--camera', type=int, default=1); ap.add_argument('--hauteur', type=float, default=O.HAUTEUR_OBJETS)
    ap.add_argument('--fenetre', type=int, default=700)
    ap.add_argument('--voix', action='store_true', help='écouter le micro : « range les ronds à gauche », « stop »')
    ap.add_argument('--clavier', action='store_true', help='taper les consignes dans cette fenêtre noire au lieu de les dire')
    ap.add_argument('--micro', type=int, default=None); ap.add_argument('--modele', default='small', help='modèle Whisper')
    ap.add_argument('--seuil', type=float, default=None, help='volume à partir duquel une phrase commence (affiché à l\'écran)')
    ap.add_argument('--ecoute', default='auto', choices=['auto', 'whisper'], help='auto = ElevenLabs si la clé est là (rapide), sinon Whisper')
    ap.add_argument('--formes', default='parole', choices=['parole', 'avance'],
                    help='parole = les formes sont reconnues quand tu commences à parler (défaut, moins d\'appels) ; avance = dès que la table change (plus rapide, plus d\'appels)')
    ap.add_argument('--muet', action='store_true', help='Câlin répond à l\'écran seulement, sans voix')
    ap.add_argument('--voix-pc', action='store_true', help='voix de Windows au lieu d\'ElevenLabs')
    ap.add_argument('--ia', default='sonnet', choices=['sonnet', 'opus']); a = ap.parse_args()
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
    t.modele_ia = {'sonnet': 'claude-sonnet-5-5', 'opus': 'claude-opus-5-5'}[a.ia]
    if (a.voix or a.clavier) and not a.muet: t.parole = CV.Parole(a.voix_pc)
    if a.voix or a.clavier:
        threading.Thread(target=ecouter_consignes, args=(t, a), daemon=True).start()
        if a.formes == 'avance': threading.Thread(target=t.prevoir_formes, daemon=True).start()
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
