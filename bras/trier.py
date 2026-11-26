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
import rapport_tri as RT, largeur_pince as LP
import aller_point as A, correction as C, geometrie as G, test_pince as PI, obstacles as OB, test_epaule as EP
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
AIDE = 'F = fond (table VIDE) | T = TRIER | 1 = un seul objet | O ouvrir | R repos | ESPACE = ARRET | P photo | Q quitter'

def choisir(objets, rates):
    """L'objet à prendre maintenant : le plus isolé, parmi ceux qui n'ont pas déjà raté ESSAIS_MAX fois au même endroit."""
    candidats = []
    for o in objets:
        if sum(1 for x, y in rates if math.hypot(o['X'] - x, o['Y'] - y) < 25) >= ESSAIS_MAX: continue
        voisin = min([math.hypot(o['X'] - a['X'], o['Y'] - a['Y']) for a in objets if a is not o] or [999.0])
        candidats.append((voisin, o))
    return max(candidats, key=lambda c: c[0]) if candidats else (None, None)

REPOS = {'epaule': EP.REPOS, 'coude': 0.0, 'flexion': 0.0}
def ouverture_prise(o): return min(100.0, max(o['largeur'], 30.0) + 30.0)      # mm : juste ce qu'il faut, pour ne pas toucher les voisins
def zone_de(largeur): return 'petit' if largeur < SEUIL_TAILLE else 'gros'

class Trieur(Poste):
    def __init__(self, pointeur, reglage, hauteur=O.HAUTEUR_OBJETS, attendre=False):
        super().__init__(pointeur, reglage, attendre)
        self.hauteur, self.fond, self.objets, self.image = hauteur, None, [], None
        self.demande, self.reponse = threading.Event(), threading.Event()
        self.au_repos, self.tries, self.rates = True, {'petit': 0, 'gros': 0}, []
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
            pts = np.array([T.vers_image(self.h, x, y) for x, y in o['contour']], np.int32); rouge = o is choisi
            cv2.polylines(vue, [pts], True, (0, 0, 255) if rouge else (0, 255, 255), 3 if rouge else 2)
            pt = T.vers_image(self.h, o['X'], o['Y']); cv2.circle(vue, pt, 6, (0, 0, 255), -1)
            V.ecrire(vue, f'{n} : {o["largeur"]:.0f} mm  (X {o["X"]:+.0f} Y {o["Y"]:.0f})', (pt[0] + 10, pt[1] - 10), (0, 0, 255) if rouge else (0, 255, 255), 0.55)
        return vue

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
        pose = pose_dans_bac(self.bacs[z], incl, c.hauteur)
        if not pose: raise ErreurServo(f'Le bac des {PLURIEL[z]} est hors de portée pour cette prise.')
        pt, i, leve = pose
        self.note(posé_en_X=pt[0], posé_en_Y=pt[1], remarque='lâché dans le bac', **{'pince_à_la_pose_(°)': abs(i), 'lâché_plus_haut_(mm)': leve})
        self.dire(f'   {largeur:.0f} mm : c\'est un {z.upper()}, je le lâche dans son bac (pince à {abs(i):.0f}°, {leve:.0f} mm au-dessus de la hauteur de prise).')
        plan = p.preparer(*C.corriger(*pt, self.corrections), i, leve)
        if not plan: raise ErreurServo('Pose dans le bac impossible.')
        p.aller(*plan); self.etape(p.prise is plan[0], 'le transport')
        self.etape(p.descendre(), 'l\'arrivée au-dessus du bac'); c._pince('o'); p.vider(); time.sleep(0.3); self.tenu = None
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
                    # on vérifie le point que le bras visera vraiment, correction de visée comprise (Nicolas, 26/11/2026 : place
                    # trouvée à 245 mm, corrigée à 235, hors de portée pour la pince à 75° : bras arrêté objet en main)
                    try:
                        v = C.corriger(*pt, self.corrections); pr, ht = G.prise_et_approche(*v, self.p.c.hauteur, incl, leve)
                        pr = dict(pr, socle=G.angles_pour(*v, None, self.p.c.hauteur, incl)['socle']); ht = dict(ht, socle=pr['socle'])
                        if getattr(self, 'tenu', None) is None or self.transport_libre(ht, pr) is None: return pt
                    except G.HorsDePortee: pass
        return None

    def serrer(self):
        c = self.p.c; r = c.reglages; c.bus.tenir(c.pince)
        texte, pos, tenu = c.bus.serrer(c.pince, c.ferme, r['serrage_doux'], maintien=min(r['maintien'], r['serrage_doux']))
        largeur = LP.ecart(pos, c.ouvert); self.dire(f'Serrer : {texte}' + (f' · largeur ≈ {largeur:.0f} mm' if tenu else ''))
        return tenu, largeur

    def obstacles(self, objets, sauf=None):
        """Les objets que le bras ne doit pas heurter : ceux de la table (sauf celui qu'il prend) et ceux déjà posés."""
        obs = [{'X': o['X'], 'Y': o['Y'], 'rayon': min(max(o['largeur'], o['longueur']), 70.0) / 2, 'hauteur': self.hauteur,
                'nom': f'X {o["X"]:+.0f} Y {o["Y"]:.0f}'} for o in objets if o is not sauf]
        obs += [{'X': x, 'Y': y, 'rayon': 22.0, 'hauteur': self.hauteur, 'nom': f'posé en X {x:+.0f} Y {y:.0f}'} for z in self.deposes for x, y in self.deposes[z]]
        return obs

    def libre_pour_prendre(self, o, objets):
        """(None, plan) si le geste de prise ne heurte rien ; (obstacle, None) sinon ; (None, None) si hors de portée."""
        visee = C.corriger(o['X'], o['Y'], self.corrections)
        try: incl, prise, haut = G.choisir_inclinaison(*visee, self.p.c.hauteur)
        except G.HorsDePortee: return None, None
        gene = OB.geste_libre(prise['socle'], [REPOS, haut, prise], self.obstacles(objets, o), self.p.c.hauteur, ouverture_prise(o))
        return gene, (None if gene else (incl, prise, haut))

    def choisir(self, objets):
        """L'objet à prendre : le plus isolé parmi ceux qu'on peut prendre SANS heurter un autre objet (demande de Nicolas)."""
        _, premier = choisir(objets, self.rates)
        if premier is None: return None
        restants = [o for o in objets if sum(1 for x, y in self.rates if math.hypot(o['X'] - x, o['Y'] - y) < 25) < ESSAIS_MAX]
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
        plan = p.preparer(*visee)
        self.note(visée_X=visee[0], visée_Y=visee[1])
        if not plan:
            self.note(résultat='hors de portée'); self.rates += [(o['X'], o['Y'])] * ESSAIS_MAX
            if math.hypot(visee[0] - o['X'], visee[1] - o['Y']) > 20 and self._atteignable(o):
                self.dire(f'   C\'est la CORRECTION de visée apprise qui l\'envoie hors de portée (elle vise {C.en_clair((o["X"], o["Y"]), visee)}). '
                          'Si tu as remonté des pièces depuis, refais la correction dans viser_camera (E deux fois, puis flèches + C, près ET loin).')
            else: self.dire('   Hors de portée : je le laisse.')
            return True
        self.au_repos = False
        self.note(**{'pince_à_la_prise_(°)': abs(p.incl), 'ouverture_(mm)': ouverture_prise(o)})
        self.ouvrir_a(ouverture_prise(o))
        p.aller(*plan); self.etape(p.prise is plan[0], 'l\'approche')
        self.etape(p.descendre(), 'la descente')
        tenu, largeur = self.serrer(); self.tenu = (p.incl, G.hauteur_prise(p.incl), self.hauteur, max(largeur, 20.0) / 2 + 2)
        self.etape(p.monter(), 'la remontée')
        self.note(**{'largeur_mesurée_(mm)': largeur if tenu else 0.0})
        if not tenu:
            self.note(résultat='raté : rien entre les doigts')
            self.rates.append((o['X'], o['Y'])); self.suite_ratee += 1; self.ouvrir_a(ouverture_prise(o))
            self.dire('   Raté : rien entre les doigts. Je regarde à nouveau.'); p.repos()
            if self.suite_ratee >= 3: raise ErreurServo('3 prises ratées de suite : la visée est sans doute décalée. Refais la correction aux flèches dans viser_camera, puis reviens.')
            return True
        self.suite_ratee = 0
        z = zone_de(largeur); incl = p.incl; self.plan_prise = plan
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
            if o is None: verdict = 'introuvable à l\'endroit de la pose (tombé ? roulé ?)'
            else:
                avant = sorted((e['largeur vue'], e.get('longueur vue', e['largeur vue']))); apres = sorted((o['largeur'], o['longueur']))
                ecart = math.hypot(o['X'] - e['posé en X'], o['Y'] - e['posé en Y'])
                debout = apres[1] <= avant[1] * 1.35 + 12 and apres[0] <= avant[0] * 1.35 + 12
                verdict = (f'debout, à {ecart:.0f} mm du point visé' if debout else f'forme différente ({apres[0]:.0f} × {apres[1]:.0f} mm au lieu de {avant[0]:.0f} × {avant[1]:.0f}) : couché ou renversé ?')
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
        self.etape(p.monter(), 'la remontée'); p.repos()

    def poser(self, z, incl, largeur):
        p, c = self.p, self.p.c
        if z in self.bacs: return self.lacher_dans_bac(z, incl, largeur)
        place = self.place_libre(z, incl)
        spot, incl_pose, leve = place if place else (None, None, None)
        if spot is None: raise ErreurServo(f'Plus de place dans la zone des {PLURIEL[z]} à la bonne distance.')
        cote = "gauche" if ZONES[z] < 0 else "droite"
        if leve: self.dire(f'   {largeur:.0f} mm : c\'est un {z.upper()}, je le pose à {cote}, pince à {abs(incl_pose):.0f}° (prise à {abs(incl):.0f}°) : lâché {leve:.0f} mm plus haut, il se redresse seul.')
        else: self.dire(f'   {largeur:.0f} mm : c\'est un {z.upper()}, je le pose à {cote}, pince inclinée comme à la prise ({abs(incl):.0f}°).')
        self.note(posé_en_X=spot[0], posé_en_Y=spot[1], **{'pince_à_la_pose_(°)': abs(incl_pose), 'lâché_plus_haut_(mm)': leve})
        plan = p.preparer(*C.corriger(*spot, self.corrections), incl_pose, leve)
        if not plan: raise ErreurServo('Pose impossible à cet endroit.')
        p.aller(*plan); self.etape(p.prise is plan[0], 'le transport')
        self.etape(p.descendre(), 'la pose'); self.ouvrir_a(2 * self.tenu[3] + 16)
        self.etape(p.monter(), 'la remontée'); p.repos(); self.tries[z] += 1; self.deposes[z].append(spot); self.tenu = None
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
        n = 0; self.suite_ratee = 0
        self.p.repos()
        objets = self.regarder(); self.rap.photo('00_debut', self.image, self.annoter(self.image))
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
        txt = (f'Fini : {self.tries["petit"]} petit(s) à gauche, {self.tries["gros"]} gros à droite.' + (f' {len(reste)} objet(s) laissé(s) (hors de portée ou ratés).' if reste and combien is None else ''))
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
        if kk == 'r':
            def repos():
                self.p.repos(); self.au_repos = True
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
        if self.fond is not None and getattr(O.trouver, 'lumiere', None):
            V.ecrire(image, 'La lumiere a change depuis la photo du fond : retire les objets, puis F', (10, 80), (80, 80, 255))
            for X, Y, _ in O.trouver.lumiere:
                if self.h is not None: V.ecrire(image, '?', T.vers_image(self.h, X, Y), (80, 80, 255), 1.0)
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
