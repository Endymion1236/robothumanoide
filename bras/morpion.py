"""Le morpion de Câlin : les règles, le choix des coups, la lecture du plateau et les phrases de Câlin. Calcul seul (ni caméra ni
bras) : utilisé par jouer_morpion.py. Demande de Nicolas (feuille de route du 23/11/2026, lancée le 26/11/2026).

Le plateau : 9 cases de 70 mm (une feuille A4), numérotées comme un clavier de téléphone vu depuis Nicolas, assis derrière le bras :
    1 2 3      ← rangée du FOND (loin du socle)
    4 5 6
    7 8 9      ← rangée près du socle
Les pions : Câlin joue les PETITS ronds (Ø 28, les seuls que sa pince prend facilement entre des voisins), Nicolas les GROS
(carrés de 36 ou ronds de 40). La caméra les distingue par leur largeur vue d'en haut : tout est imprimé dans la même couleur.
Le coup de Câlin est choisi par ce programme, qui connaît les règles (pas par l'IA de conversation) : c'est immédiat et gratuit."""
import math, random

CASE = 70.0                                   # mm : côté d'une case
CENTRE = (0.0, 350.0)                         # centre du plateau sur la table (X, Y), devant le socle
RAYON_CASE = 30.0                             # un pion compte dans une case s'il est à moins de 30 mm de son centre
SEUIL_PION = 37.0                             # largeur vue (mm), utilisée seulement si la largeur étroite manque
SEUIL_ETROIT = 28.0                           # largeur ÉTROITE au pied (mm) : en dessous, pion de Câlin ; au-dessus, pion de Nicolas
def est_petit(o):
    """Un pion de Câlin (petit rond de 28) ou un pion de Nicolas ? La « largeur vue » gonfle avec l'ombre et le penché : un petit
    rond a été vu de 29 à 39 mm (partie de Nicolas du 27/11/2026 : ses petits ronds, pris pour des gros, n'étaient pas reconnus
    comme pions de Câlin). La largeur étroite au pied, penché retiré, sépare mieux : 20 à 24 mm pour le petit rond, 31 mm et
    plus pour le gros rond, le carré et l'hexagone (photos des tris du 26/11/2026)."""
    e = o.get('etroit')
    return e < SEUIL_ETROIT if e is not None else o['largeur'] < SEUIL_PION
LIGNES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
VIDE, CALIN, NICOLAS = '', 'C', 'N'

def centre_case(k, centre=CENTRE):
    """Le centre de la case k (0 à 8 ; 0 = au fond à gauche) sur la table."""
    ligne, col = divmod(k, 3)
    return centre[0] + (col - 1) * CASE, centre[1] + (1 - ligne) * CASE
def nom_case(k): return str(k + 1)

def gagnant(g):
    """'C', 'N', 'nul' ou None (partie en cours). g : liste de 9 cases."""
    for a, b, c in LIGNES:
        if g[a] and g[a] == g[b] == g[c]: return g[a]
    return 'nul' if all(g) else None
def ligne_gagnante(g):
    return next(((a, b, c) for a, b, c in LIGNES if g[a] and g[a] == g[b] == g[c]), None)
def libres(g): return [k for k in range(9) if not g[k]]

def _valeur(g, joueur, moi):
    """Valeur de la position pour `moi` si les deux jouent au mieux (1 gagné, 0 nul, −1 perdu) ; c'est à `joueur` de jouer."""
    w = gagnant(g)
    if w: return 0 if w == 'nul' else (1 if w == moi else -1)
    autre = NICOLAS if joueur == CALIN else CALIN
    vals = [_valeur(g[:k] + [joueur] + g[k + 1:], autre, moi) for k in libres(g)]
    return max(vals) if joueur == moi else min(vals)

def choisir_coup(g, niveau='normal', hasard=random):
    """La case où Câlin joue. facile : il gagne s'il peut, bloque s'il le voit, sinon au hasard. normal : il joue au mieux, mais se
    trompe une fois sur quatre quand rien ne presse (on peut le battre). imbattable : il ne perd jamais."""
    cases = libres(g)
    if not cases: return None
    def complete(qui): return next((k for k in cases if gagnant(g[:k] + [qui] + g[k + 1:]) == qui), None)
    gagne, bloque = complete(CALIN), complete(NICOLAS)
    if gagne is not None: return gagne
    if niveau == 'facile': return bloque if bloque is not None and hasard.random() < 0.7 else hasard.choice(cases)
    if bloque is not None: return bloque
    if niveau == 'normal' and hasard.random() < 0.25: return hasard.choice(cases)
    notes = {k: _valeur(g[:k] + [CALIN] + g[k + 1:], NICOLAS, CALIN) for k in cases}
    meilleur = max(notes.values())
    return hasard.choice([k for k, v in notes.items() if v == meilleur])

RAYON_RESERVE = 35.0                          # un objet à moins de 35 mm d'un rond bleu est un pion de Câlin, quelle que soit sa largeur vue
def lire_plateau(objets, centre=CENTRE, spots=(), connue=None):
    """Ce que la caméra voit : (grille de 9 cases, réserve). Un objet à moins de 30 mm du centre d'une case est un pion posé.
    À qui est-il ? Pendant une partie (`connue` = la grille que Câlin a en tête), on ne se fie plus à la largeur vue : une case
    déjà occupée garde son propriétaire, et un pion apparu dans une case vide est celui de Nicolas (Câlin sait où il a posé les
    siens). Sans partie en cours : petit = Câlin, gros = Nicolas.
    La réserve de Câlin : tout objet posé sur un de ses ronds bleus (`spots`), même si la caméra le voit trop large — sur les
    côtés de la table, loin de la caméra, un petit rond penche et paraît gros (Nicolas, 27/11/2026 : « il a beaucoup de mal à
    reconnaître les pions sur le côté ») — Rien d'autre : un objet posé ailleurs (ou le fantôme d'un pion resté sur la photo du fond) est ignoré. Sans `spots` : tout PETIT objet hors du plateau. Deux pions dans une case : '?'."""
    g, reserve = [VIDE] * 9, []
    for o in objets:
        k = min(range(9), key=lambda c: math.hypot(o['X'] - centre_case(c, centre)[0], o['Y'] - centre_case(c, centre)[1]))
        cx, cy = centre_case(k, centre); petit = est_petit(o)
        hors = not (abs(o['X'] - centre[0]) < 1.5 * CASE + 15 and abs(o['Y'] - centre[1]) < 1.5 * CASE + 15)
        if math.hypot(o['X'] - cx, o['Y'] - cy) <= RAYON_CASE:
            qui = (connue[k] or NICOLAS) if connue is not None else (CALIN if petit else NICOLAS)
            g[k] = '?' if g[k] else qui
        elif hors and (any(math.hypot(o['X'] - x, o['Y'] - y) <= RAYON_RESERVE for x, y in spots) if spots else petit): reserve.append(o)
    return g, reserve

def coup_de_nicolas(avant, vu):
    """Compare la grille attendue et celle vue. Renvoie (case jouée, None) si Nicolas a posé UN pion de plus, (None, None) si rien
    n'a changé, sinon (None, explication)."""
    if '?' in vu: return None, f'il y a deux pions dans la case {nom_case(vu.index("?"))}'
    nouveaux = [k for k in range(9) if vu[k] != avant[k]]
    if not nouveaux: return None, None
    for k in nouveaux:
        if avant[k] and not vu[k]: return None, f'le pion de la case {nom_case(k)} a disparu : remets-le'
        if avant[k] and vu[k] != avant[k]: return None, f'le pion de la case {nom_case(k)} a changé : remets celui d\'avant'
        if vu[k] == CALIN: return None, f'un de MES pions est apparu en case {nom_case(k)} : c\'est moi qui les pose, enlève-le'
    if len(nouveaux) > 1: return None, f'je vois {len(nouveaux)} nouveaux pions : un seul coup à la fois, enlève-en'
    return nouveaux[0], None

def dessin(g):
    """La grille en texte, pour le journal."""
    s = lambda v: {CALIN: 'o', NICOLAS: 'X', VIDE: '.', '?': '?'}[v]
    return ' / '.join(' '.join(s(g[3 * l + c]) for c in range(3)) for l in range(3))

# ---- Ce que dit Câlin (gratuit et immédiat : pas d'appel à l'IA). Humour gentil, demande de Nicolas du 26/11/2026. ----
PHRASES = {
    'debut_nicolas': ['À toi l\'honneur ! Pose ton pion, je regarde.', 'Tu commences. Je te préviens, je me suis entraîné toute la nuit.', 'Vas-y, je ne triche pas : je n\'ai qu\'un bras.'],
    'debut_calin': ['Je commence ! Prépare-toi.', 'À moi de jouer le premier. Ne bouge pas tes pions, je les compte.'],
    'coup': ['Je joue en case {c}.', 'Hop, case {c}.', 'Case {c}. Doucement, ma pince, doucement…', 'Je pose mon pion en {c}. Un pas de côté, comme en dressage.'],
    'bloque': ['Pas si vite ! Je bloque en {c}.', 'Je t\'ai vu venir : case {c}.', 'Refus devant l\'obstacle : je ferme la case {c}.'],
    'gagne': ['Et de trois ! J\'ai gagné, case {c}.', 'Case {c}, et c\'est gagné ! Sans faute au tour d\'honneur.'],
    'perdu': ['Bravo, tu as gagné ! Je demande une revanche.', 'Bien joué ! Mes servos s\'inclinent.', 'Gagné pour toi. Je vais dire que c\'était la faute de ma pince.'],
    'nul': ['Match nul ! On est aussi têtus l\'un que l\'autre.', 'Égalité. Comme deux poneys devant la même carotte.'],
    'a_toi': ['À toi.', 'À ton tour.', 'C\'est à toi de jouer.'],
    'rate': ['Oups, je l\'ai mal posé. Tu peux remettre mon pion en case {c} ?', 'Raté ! Mon pion devrait être en case {c} : un coup de main ?'],
    'aide': ['Je n\'arrive pas à poser en case {c} sans bousculer un voisin. Tu peux y mettre un de mes pions pour moi ?', 'La case {c} est trop entourée pour ma pince. Un coup de main ? Pose-y un de mes pions, s\'il te plaît.', 'Case {c} : trop serré pour moi, je ne suis qu\'un bras ! Tu poses mon pion ?'],
    'merci_aide': ['Merci ! Mon pion est en case {c}.', 'Merci pour le coup de main, case {c} !'],
    'plus_de_pion': ['Je n\'ai pas de pion à prendre : pose-m\'en un petit sur un rond bleu.', 'Ma réserve est vide ! Un petit pion sur un rond bleu, et je joue.'],
    'triche': ['Hé ! {raison}.', 'Minute : {raison}.'],
}
def phrase(quoi, hasard=random, **mots): return hasard.choice(PHRASES[quoi]).format(**mots)
