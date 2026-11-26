"""Câlin joue au morpion contre Nicolas : la caméra lit le plateau, un petit programme choisit le coup (morpion.py), le bras
prend un de ses pions dans sa réserve et le pose dans la case. Essayé sur des servos simulés seulement.

Lancer : jouer_morpion.bat (FD et la fenêtre de contrôle fermés, 12 V, USB et caméra branchés ; camera\\regler_table.bat déjà fait).

Le matériel : 5 PETITS ronds (objets/objet_rond_petit.stl, Ø 28) pour Câlin, 5 GROS pions pour Nicolas (objet_carre.stl ou
objet_rond_grand.stl). Pas de plateau en papier (sur du papier blanc, la caméra verrait mal les pions gris) : la grille se
marque avec 4 bandes de ruban de masquage, en suivant les traits bleus que le programme dessine à l'écran.

Déroulement :
  1. bras au repos, table VIDE (rubans posés, aucun pion) : F, la photo du fond ;
  2. pose un petit rond de Câlin sur chacun des deux RONDS BLEUS dessinés à l'écran (sa réserve, de part et d'autre du plateau) ;
     tu en remets un quand il en a pris un : il lui en faut toujours au moins un ;
  3. N = nouvelle partie, tu commences (C = Câlin commence). Tu poses un gros pion dans une case et tu retires ta main :
     Câlin voit ton coup tout seul (J pour le forcer à regarder), joue le sien, et ainsi de suite.
Touches : F fond | N nouvelle partie | C Câlin commence | J j'ai joué | 1 2 3 = niveau facile, normal, imbattable | R repos |
ESPACE = ARRÊT (le bras reste tenu) | Q quitter."""
import argparse, math, sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'camera'))
import cv2, numpy as np
import table as T, voir_table as V, objets as O
import trier as TR, morpion as M, correction as C, geometrie as G, obstacles as OB, aller_point as A, consigne_vocale as CV
from servos import ErreurServo
from viser_camera import sans_accents, FLECHES

NIVEAUX = {'1': 'facile', '2': 'normal', '3': 'imbattable'}
ANGLES_RESERVE = (33.0, -33.0)                # les deux emplacements des pions de Câlin : à droite et à gauche du plateau
OUV_PION = 68.0                               # ouverture de la pince pour prendre un pion de Ø 28 (40 mm de marge)
AIDE = 'F = fond (table VIDE) | N = nouvelle partie | C = Calin commence | J = j ai joue | 1 2 3 = niveau | R repos | ESPACE = ARRET | Q quitter'

class Joueur(TR.Trieur):
    def __init__(self, pointeur, reglage, hauteur=O.HAUTEUR_OBJETS, attendre=False, niveau='normal'):
        super().__init__(pointeur, reglage, hauteur, attendre)
        self.bacs = {}                                   # pas de bac ici : on ne filtre aucune zone de la table
        self.grille, self.en_jeu, self.tour, self.niveau = [M.VIDE] * 9, False, None, niveau
        self.stable, self.depuis, self.averti = None, 0.0, None

    # ---- ce que la caméra voit ----
    def voir(self, image):
        self.image = image.copy()
        centres, contours = TR.Poste.voir(self, image)
        if self.fond is not None and self.vus and self.h is not None and self.au_repos and self.fond.shape == image.shape:
            self.objets = [o for o in O.trouver(image, self.fond, self.h, self.reglage, self.hauteur) if math.hypot(o['X'], o['Y']) >= TR.PRES_DU_SOCLE]
            if self.demande.is_set(): self.demande.clear(); self.reponse.set()
        return centres, contours

    def parler_et_dire(self, texte):
        self.dire(f'Câlin : {texte}'); self.parler(texte)

    # ---- la partie ----
    def nouvelle_partie(self, calin_commence):
        if self.occupe: self.dire('Le bras est occupé : attends, ou ESPACE.'); return
        if self.fond is None: self.dire('Il faut d\'abord la photo du fond : table VIDE (sans pion), bras au repos, touche F.'); return
        g, reserve = M.lire_plateau(self.objets)
        if any(g): self.dire('Il reste des pions sur le plateau : vide les 9 cases, puis N.'); return
        if not reserve: self.dire('Il me faut au moins un petit pion sur un des deux ronds bleus (ma réserve).'); return
        self.grille, self.en_jeu, self.stable, self.averti = [M.VIDE] * 9, True, None, None
        self.dire(f'Nouvelle partie, niveau {self.niveau}.')
        if calin_commence: self.parler_et_dire(M.phrase('debut_calin')); self.tour = M.CALIN; self.lancer_coup()
        else: self.parler_et_dire(M.phrase('debut_nicolas')); self.tour = M.NICOLAS

    def surveiller(self, forcer=False):
        """Appelé à chaque image : quand c'est à Nicolas, on attend que le plateau ne bouge plus (1,2 s) puis on cherche son coup."""
        if not self.en_jeu or self.tour != M.NICOLAS or self.occupe or not self.au_repos or not self.vus: return
        vu, _ = M.lire_plateau(self.objets)
        if vu != self.stable: self.stable, self.depuis = vu, time.time(); return
        if not forcer and time.time() - self.depuis < 1.2: return
        if getattr(O.trouver, 'lumiere', None): return                           # une main ou une ombre dans le champ : on attend
        case, souci = M.coup_de_nicolas(self.grille, vu)
        if souci:
            if souci != self.averti: self.averti = souci; self.parler_et_dire(M.phrase('triche', raison=souci))
            return
        self.averti = None
        if case is None:
            if forcer: self.dire('Je ne vois pas de nouveau pion dans une case (à moins de 3 cm de son centre).')
            return
        self.grille[case] = M.NICOLAS; self.dire(f'Tu as joué en case {M.nom_case(case)}.   {M.dessin(self.grille)}')
        if self.fin_de_partie(): return
        self.tour = M.CALIN; self.lancer_coup()

    def fin_de_partie(self):
        w = M.gagnant(self.grille)
        if not w: return False
        self.en_jeu = False
        self.parler_et_dire(M.phrase('nul') if w == 'nul' else M.phrase('perdu') if w == M.NICOLAS else 'Merci pour la partie !')
        self.dire('Partie finie. Vide le plateau, remets mes pions dans ma réserve, puis N.')
        return True

    def lancer_coup(self):
        def geste():
            try: self.jouer_un_coup()
            finally: self.au_repos = True
        self._lancer('Câlin joue', geste)

    def jouer_un_coup(self):
        p, c = self.p, self.p.c; h = c.hauteur
        case = M.choisir_coup(self.grille, self.niveau)
        bloque = any(M.gagnant(self.grille[:k] + [M.NICOLAS] + self.grille[k + 1:]) == M.NICOLAS for k in [case])
        gagne = M.gagnant(self.grille[:case] + [M.CALIN] + self.grille[case + 1:]) == M.CALIN
        self.parler_et_dire(M.phrase('gagne' if gagne else 'bloque' if bloque else 'coup', c=M.nom_case(case)))
        cible = M.centre_case(case)
        for essai in range(2):
            p.repos(); self.redresser(); objets = self.regarder()
            _, reserve = M.lire_plateau(objets)
            plan = self.plan_du_coup(reserve, objets, cible)
            if plan is None: self.parler_et_dire(M.phrase('plus_de_pion')); self.dire('Quand c\'est fait, appuie sur J : je rejoue.'); return
            o, visee, ip, q, iq, leve = plan
            pr = p.preparer(*visee, ip)
            if not pr: raise ErreurServo('prise impossible')
            self.au_repos = False
            self.ouvrir_a(OUV_PION); p.aller(*pr); self.etape(p.prise is pr[0], 'l\'approche'); self.etape(p.descendre(), 'la descente')
            tenu, largeur = self.serrer(); self.etape(p.monter(), 'la remontée')
            if tenu: break
            self.ouvrir_a(OUV_PION); self.dire('   Prise ratée : je recommence avec un autre regard.')
        else:
            p.repos(); raise ErreurServo('je n\'arrive pas à prendre mon pion : refais l\'apprentissage de la visée (touche A de trier), puis J.')
        self.tenu = (ip, G.hauteur_prise(ip), self.hauteur, max(largeur, 20.0) / 2 + 2)
        pose = p.preparer(*q, iq, leve)
        if not pose: raise ErreurServo('pose impossible (pion en main : le bras reste tenu)')
        p.aller(*pose); self.etape(p.prise is pose[0], 'le transport'); self.etape(p.descendre(), 'la pose')
        self.ouvrir_a(max(largeur, 20.0) + 20); self.tenu = None
        self.etape(p.monter(), 'la remontée'); p.repos()
        # contrôle : mon pion est-il bien dans sa case ?
        vu, _ = M.lire_plateau(self.regarder()); attendu = self.grille[:]; attendu[case] = M.CALIN
        self.grille = attendu; self.dire(f'   {M.dessin(self.grille)}')
        if vu[case] != M.CALIN: self.parler_et_dire(M.phrase('rate', c=M.nom_case(case)))
        if self.fin_de_partie(): return
        self.tour, self.stable = M.NICOLAS, None
        reste = M.lire_plateau(self.objets)[1]
        self.parler_et_dire(M.phrase('a_toi') + ('' if reste else ' Et remets-moi un pion sur un rond bleu, s\'il te plaît.'))

    def spots(self):
        """Les deux emplacements de la réserve (calculés une fois) : de chaque côté du plateau, à la distance d'où un pion peut
        aller dans le plus de cases possible, correction de visée comprise."""
        if getattr(self, '_spots', None) is None: self._spots = emplacements(self.p.c.hauteur, self.corrections)
        return self._spots

    def plan_du_coup(self, reserve, objets, cible):
        """Quel pion de la réserve prendre, et comment : (pion, visée, inclinaison de prise, point de pose, inclinaison de pose,
        levée) ou None. La pince doit poser avec l'inclinaison de la prise (à 15° près, le pion étant alors lâché 13 mm plus
        haut) : pour chaque pion, on cherche une inclinaison qui convient aux deux bouts du geste, sans rien heurter."""
        h = self.p.c.hauteur; q = C.corriger(*cible, self.corrections); meilleurs = []
        def possible(pt, incl, leve=0.0):
            try: return G.prise_et_approche(*pt, h, incl, leve)
            except G.HorsDePortee: return None
        for o in reserve:
            visee = C.corriger(o['X'], o['Y'], self.corrections); obs = self.obstacles(objets, o)
            for ip in G.INCLINAISONS:
                pr = possible(visee, ip)
                if not pr: continue
                socle = G.angles_pour(*visee, None, h, ip)['socle']
                if OB.geste_libre(socle, [TR.REPOS, pr[1], pr[0]], obs, h, OUV_PION): continue      # la pince ouverte toucherait un voisin
                for iq, leve in ((ip, 0.0), (ip - TR.ECART_INCL, TR.LEVE_PENCHE), (ip + TR.ECART_INCL, TR.LEVE_PENCHE)):
                    if not -90.0 <= iq <= 0.0: continue
                    po = possible(q, iq, leve)
                    if not po: continue
                    socle2 = G.angles_pour(*q, None, h, iq)['socle']
                    tenu = (ip, G.hauteur_prise(ip), self.hauteur, 16.0)
                    if OB.geste_libre(socle2, [TR.REPOS, po[1], po[0]], obs, h, 0.0, tenu): continue              # le pion tenu toucherait un pion du plateau
                    meilleurs.append((leve > 0, abs(ip), math.hypot(o['X'] - cible[0], o['Y'] - cible[1]), id(o), (o, visee, ip, q, iq, leve)))
        return min(meilleurs)[-1] if meilleurs else None

    # ---- touches et écran ----
    def touche(self, k):
        kk = chr(k).lower() if 0 < k < 128 else ''
        if kk == 'f':
            self.photo_fond(); self.en_jeu = False; return True
        if kk in ('n', 'c'): self.nouvelle_partie(kk == 'c'); return True
        if kk == 'j':
            if self.en_jeu and self.tour == M.CALIN and not self.occupe: self.lancer_coup()      # son coup avait échoué : il le retente
            else: self.surveiller(forcer=True)
            return True
        if kk in NIVEAUX: self.niveau = NIVEAUX[kk]; self.dire(f'Niveau {self.niveau}.'); return True
        if kk == 'r':
            def repos():
                self.p.repos(); self.redresser(); self.au_repos = True
            self._lancer('retour au repos', repos); return True
        if kk in ('t', 'a', 'o', 'd', 'm', 'e', 's', 'i', 'l', 'u', '\r', '\n') or k in FLECHES: return True
        return TR.Poste.touche(self, k)

    def clic(self, x, y): pass

    def dessiner(self, image, centres, contours):
        if self.h is not None:
            pt = lambda x, y: T.vers_image(self.h, x, y)
            cx, cy = M.CENTRE; d = 1.5 * M.CASE; bleu = (255, 160, 0)
            for s in (-0.5, 0.5):                                                # les 4 traits de la grille : là où coller les rubans
                cv2.line(image, pt(cx + s * M.CASE, cy - d + 10), pt(cx + s * M.CASE, cy + d - 10), bleu, 2)
                cv2.line(image, pt(cx - d + 10, cy + s * M.CASE), pt(cx + d - 10, cy + s * M.CASE), bleu, 2)
            for k in range(9):
                x, y = M.centre_case(k); v = self.grille[k]
                V.ecrire(image, M.nom_case(k), pt(x - 28, y + 28), (200, 200, 200), 0.45)
                if v == M.CALIN: cv2.circle(image, pt(x, y), 22, (0, 200, 0), 3)
                elif v == M.NICOLAS: cv2.drawMarker(image, pt(x, y), (0, 0, 255), cv2.MARKER_TILTED_CROSS, 44, 3)
            for x, y in self.spots():
                cv2.circle(image, pt(x, y), 26, bleu, 2); V.ecrire(image, 'pion de Calin', pt(x - 40, y - 34), (255, 200, 80), 0.45)
            for o in self.objets:
                cv2.circle(image, pt(o['X'], o['Y']), 5, (0, 255, 255) if o['largeur'] < M.SEUIL_PION else (0, 140, 255), -1)
        haut = image.shape[0]; pas = int(30 * haut / 720)
        etat = ('Calin joue... ESPACE = ARRET' if self.occupe else 'Photo du fond manquante : table VIDE, bras au repos, touche F' if self.fond is None
                else 'A toi : pose un gros pion dans une case, puis retire ta main' if self.en_jeu and self.tour == M.NICOLAS
                else f'N = nouvelle partie (niveau {self.niveau})' if not self.en_jeu else '...')
        V.ecrire(image, sans_accents(etat), (10, 40), (0, 200, 255) if self.occupe or self.fond is None else (120, 255, 120))
        V.ecrire(image, AIDE, (10, haut - 14), (255, 255, 255), 0.5)
        for n, m in enumerate(reversed(self.messages[-3:])):
            V.ecrire(image, sans_accents(m)[:110], (10, haut - 14 - (n + 1) * pas), (0, 230, 255) if n == 0 else (190, 190, 190), 0.55)

def cases_servies(pt, h_epaule, corrections):
    """Les cases où peut aller un pion posé en `pt` (sans compter les voisins) : pose à l'inclinaison de la prise, à 15° près."""
    v = C.corriger(*pt, corrections); cases = set()
    for ip in G.INCLINAISONS:
        try: G.prise_et_approche(*v, h_epaule, ip)
        except G.HorsDePortee: continue
        for k in range(9):
            q = C.corriger(*M.centre_case(k), corrections)
            for iq, leve in ((ip, 0.0), (ip - TR.ECART_INCL, TR.LEVE_PENCHE), (ip + TR.ECART_INCL, TR.LEVE_PENCHE)):
                if not -90.0 <= iq <= 0.0: continue
                try: G.prise_et_approche(*q, h_epaule, iq, leve); cases.add(k)
                except G.HorsDePortee: pass
    return cases

def emplacements(h_epaule, corrections):
    """Où poser les pions de Câlin : pour chaque côté, la distance au socle d'où un pion atteint le plus de cases."""
    out = []
    for a in ANGLES_RESERVE:
        notes = [(len(cases_servies(G.point_dans_direction(a, R), h_epaule, corrections)), -abs(R - 380), R) for R in range(300, 451, 10)]
        out.append(G.point_dans_direction(a, max(notes)[2]))
    return out

def verifier_plateau(h_epaule, corrections):
    """Chaque case doit être à portée de la pince, correction de visée comprise. Renvoie la liste des cases hors de portée."""
    hors = []
    for k in range(9):
        try: G.choisir_inclinaison(*C.corriger(*M.centre_case(k), corrections), h_epaule)
        except G.HorsDePortee: hors.append(M.nom_case(k))
    return hors

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--camera', type=int, default=1); ap.add_argument('--fenetre', type=int, default=700)
    ap.add_argument('--niveau', default='normal', choices=list(NIVEAUX.values()))
    ap.add_argument('--muet', action='store_true', help='Câlin écrit ses phrases sans les dire')
    ap.add_argument('--voix-pc', action='store_true', help='voix de Windows au lieu d\'ElevenLabs'); a = ap.parse_args()
    reglage = T.charger()
    if not reglage: print('Réglage de la table introuvable : lance d\'abord camera\\regler_table.bat'); return 1
    cam = cv2.VideoCapture(a.camera, cv2.CAP_DSHOW) if sys.platform == 'win32' else cv2.VideoCapture(a.camera)
    if not cam.isOpened(): print(f'Caméra n° {a.camera} introuvable : essaie --camera 0.'); return 1
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280); cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
    try: p = A.Pointeur()
    except ErreurServo as err: print('Impossible de commencer :', err); cam.release(); return 1
    t = Joueur(p, reglage, niveau=a.niveau)
    if not a.muet: t.parole = CV.Parole(a.voix_pc)
    hors = verifier_plateau(p.c.hauteur, t.corrections)
    if hors: t.dire(f'ATTENTION : les cases {", ".join(hors)} sont hors de portée de la pince (correction de visée comprise). Refais la visée (touche A de trier).')
    cv2.namedWindow('Calin joue au morpion')
    t.dire('Bras au repos (R), table VIDE avec les rubans : F. Puis mes 5 petits pions dans ma réserve, et N.' if t.fond is None else 'Mes petits pions dans ma réserve (cadre bleu), puis N pour jouer.')
    try:
        while True:
            ok, image = cam.read()
            if not ok: print('La caméra ne répond plus.'); break
            centres, contours = t.voir(image); t.surveiller(); t.dessiner(image, centres, contours)
            ech = V.ech_fenetre(image.shape[0], a.fenetre)
            cv2.imshow('Calin joue au morpion', image if ech == 1.0 else cv2.resize(image, None, fx=ech, fy=ech, interpolation=cv2.INTER_AREA))
            k = cv2.waitKeyEx(1); k = k if k in FLECHES else (k & 0xFF if k != -1 else 255)
            if k != 255 and not t.touche(k): break
    except KeyboardInterrupt: print('\nInterrompu : le bras reste tenu.')
    cam.release(); cv2.destroyAllWindows()
    return A.terminer(p)

if __name__ == '__main__': sys.exit(main())
