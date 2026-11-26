"""Banc d'essai d'UN doigt motorisé : le doigt d'essai (generer_doigt.py) tiré par un servo Feetech SCS0009.
Prototype : vérifié par le calcul, rien n'est imprimé ni monté.

Mécanisme « deux fils » (décision du 18/11/2026) : le fil du dessous (côté paume) ferme le doigt, celui du dessus l'ouvre. Les deux
s'enroulent EN SENS INVERSE sur une poulie à deux gorges : quand le servo tourne, l'un s'enroule pendant que l'autre se déroule.

5 pièces à imprimer :
  - le BANC : une platine avec un montant et une cloison percée d'une fenêtre où le servo entre couché ; ses pattes s'y appuient ;
  - la CONSOLE : vissée sur le montant (2 vis M3 × 10 + 2 inserts), elle porte la base du doigt au-dessus du vide (2 vis M3 × 10,
    2 rondelles imprimées, 2 inserts) : plié à fond, le doigt s'enroule et repasse sous sa base ;
  - le SERRE-SERVO : un étrier vissé derrière la cloison (2 vis M3 × 10 par l'avant + 2 inserts) qui plaque le servo contre elle ;
  - la POULIE : elle coiffe le palonnier ROND du servo (logé dans un creux) et s'y visse par une des petites vis fournies ;
    au-dessus, un tambour à deux gorges de Ø 8 au fond ;
  - 2 RONDELLES de 2 mm, sous les têtes des vis de la base du doigt.
Le servo est couché, son axe horizontal (perpendiculaire au doigt) : les deux gorges tombent juste dans le plan des deux canaux du
doigt, à 3,6 mm au-dessus et au-dessous de ses axes.

Mesures utilisées (Nicolas, 25/11/2026, voir CLAUDE.md) : boîtier 23,1 × 12,1 ; dessous des pattes à 17,0, pattes de 1,2 d'épaisseur,
32,4 de bout en bout ; dessus de la partie ronde à 20,6 ; axe doré Ø 3,7 dépassant de 3,8, centre à 6,6 du bout le plus proche ;
palonnier rond Ø 17,5, disque 1,2, 3,8 avec le moyeu, trous les plus écartés à 16,3 l'un de l'autre ; vis fournies Ø 1,3 × 6,1.
Supposé (non mesuré) : le moyeu du palonnier est côté servo, son disque affleure le bout de l'axe doré (h = 20,6 + 3,8).

Repère du banc : X le long du doigt (vers le bout), Y en travers, Z vers le haut ; dessus de la platine à z = 0.
Lancer : python generer_banc_doigt.py → sortie/banc_*.stl, sortie/verification_banc_doigt.json"""
import json, math
from pathlib import Path
import numpy as np, manifold3d as mf
import generer_doigt as D

OUT = D.OUT
box, mesh = D.box, D.mesh
def cyl_axe(r, h0, h1, n=64):
    """Cylindre sur l'axe du servo (repère du servo : axe le long de h)."""
    return mf.Manifold.cylinder(h1 - h0, r, r, n).translate((0, 0, h0))

# ---------------- Le servo SCS0009, dans SON repère : u le long du boîtier (0 = axe, + vers le bout proche), w en travers, h en hauteur
L_PRES, L_LOIN = 6.6, 23.1 - 6.6          # du centre de l'axe aux deux bouts du boîtier
LARG = 12.1
H_PATTE0, EP_PATTE, L_PATTES = 17.0, 1.2, 32.4
H_ROND, R_ROND = 20.6, 11.7 / 2          # dessus de la partie ronde, son rayon
H_HAUT_BOITIER = 19.0                    # dessus du boîtier : NON mesuré (entre le dessus des pattes, 18,2, et celui de la partie ronde)
R_AXE, H_AXE = 3.7 / 2, 20.6 + 3.8
R_DISQUE, EP_DISQUE = 17.5 / 2, 1.2
R_TROU_PAL = 16.3 / 2                    # les deux trous les plus écartés du palonnier rond
VIS_PAL = 6.1                            # vis fournies Ø 1,3 × 6,1 sous tête

def servo():
    deb = (L_PATTES - (L_PRES + L_LOIN)) / 2
    s = box(-L_LOIN, -LARG / 2, 0, L_PRES, LARG / 2, H_HAUT_BOITIER)
    s += box(-L_LOIN - deb, -LARG / 2, H_PATTE0, L_PRES + deb, LARG / 2, H_PATTE0 + EP_PATTE)
    s += cyl_axe(R_ROND, H_HAUT_BOITIER - 0.1, H_ROND) + cyl_axe(R_AXE, H_ROND - 0.1, H_AXE, 32)
    return s
def palonnier():
    return cyl_axe(2.8, H_ROND, H_AXE - EP_DISQUE + 0.01, 32) + cyl_axe(R_DISQUE, H_AXE - EP_DISQUE, H_AXE)

# ---------------- La poulie (repère du servo) ----------------
JEU_P = 0.2
R_BASE = R_DISQUE + 0.15 + 1.3           # la poulie coiffe le disque du palonnier : creux de Ø 17,8, paroi de 1,3
SOUS_TETE = VIS_PAL - EP_DISQUE          # 4,9 : épaisseur de plastique sous la tête de la vis, pour que sa pointe s'arrête au ras du disque
H_P0 = H_AXE - EP_DISQUE                 # dessous de la poulie = dessous du disque du palonnier
H_P1 = H_AXE + SOUS_TETE                 # dessus de la base
R_FOND, R_JOUE = 4.0, 5.5                # fond des gorges (Ø 8, comme conseillé le 25/11) et joues du tambour
GORGES = [(H_P1 + 1.0, H_P1 + 2.5), (H_P1 + 3.5, H_P1 + 5.0)]     # gorge « ferme » (côté servo), gorge « ouvre »
H_P2 = H_P1 + 6.0                        # dessus du tambour
H_FILS = (GORGES[0][1] + GORGES[1][0]) / 2                        # plan médian des deux gorges : il doit tomber dans le plan du doigt
LARGEUR_FENTE = 1.4
ANCRES = [(90.0, 0), (270.0, 1)]         # (angle, gorge) : un petit trou par fil, du fond de sa gorge jusqu'au dessus du tambour

def poulie():
    p = cyl_axe(R_BASE, H_P0, H_P1) + cyl_axe(R_JOUE, H_P1 - 0.01, H_P2, 64)
    p -= cyl_axe(R_DISQUE + 0.15, H_P0 - 0.1, H_AXE + JEU_P)          # creux du disque du palonnier
    p -= cyl_axe(3.0, H_P0 - 0.1, H_AXE + 1.2, 32)                     # tête de la vis centrale du palonnier (posée AVANT la poulie)
    for h0, h1 in GORGES: p -= cyl_axe(R_JOUE + 1, h0, h1) - cyl_axe(R_FOND, h0 - 0.1, h1 + 0.1)
    for a in (0.0, 180.0):                                              # 2 trous pour les vis fournies (une suffit), face aux 2 trous écartés
        x, y = R_TROU_PAL * math.cos(math.radians(a)), R_TROU_PAL * math.sin(math.radians(a))
        p -= mf.Manifold.cylinder(H_P1 - H_P0 + 1, 0.75, 0.75, 16).translate((x, y, H_P0 - 0.5))
    for a, g in ANCRES:
        # Ancrage du fil : une FENTE ouverte vers l'extérieur, large de 1,4 mm, du fond de sa gorge jusqu'au dessus du tambour.
        # Avant : un trou fermé de Ø 1,2, qui ne s'est pas formé à l'impression (Nicolas, 26/11/2026 : « impossible de faire passer
        # le fil »). Le fil se glisse dans la fente par le côté ; son nœud, sur le dessus du tambour, est plus gros qu'elle.
        fente = mf.Manifold.cube((R_JOUE + 1 - (R_FOND - 0.6), LARGEUR_FENTE, H_P2 - GORGES[g][0] + 1)).translate((R_FOND - 0.6, -LARGEUR_FENTE / 2, GORGES[g][0]))
        p -= fente.rotate((0, 0, a))
    return p

# ---------------- Placement dans le banc ----------------
H = 16.0                                  # hauteur des axes du doigt et de l'axe du servo au-dessus de la platine
Y_FILS = 0.0                              # plan du doigt
ECART = 25.0                              # du bord de la poulie au bout arrière de la base du doigt
X_DOIGT0 = -D.L_BASE                      # bout arrière de la base du doigt (repère du doigt = repère du banc, décalé en z)
XP = X_DOIGT0 - ECART - R_BASE            # axe du servo
def du_servo(m):
    """Repère du servo → banc : u → X, w → Z (autour de H), h → Y (h = H_FILS tombe en Y_FILS). Le servo est couché sur le flanc."""
    return m.transform([[1, 0, 0, XP], [0, 0, 1, Y_FILS - H_FILS], [0, 1, 0, H]])
def y_de_h(h): return Y_FILS - H_FILS + h

EP_PLATINE, EP_CLOISON, JEU = 4.0, 7.0, 0.2
Y_CLOISON = y_de_h(H_PATTE0)              # face avant de la cloison : le dessous des pattes s'y appuie
Y_FOND = y_de_h(0.0)                      # dessous du servo
# Plié à fond, le doigt s'enroule et revient SOUS sa base, jusqu'à 40 mm en arrière de sa charnière et 13,4 mm sous ses axes
# (calcul du 25/11/2026). Donc : la base est portée par une CONSOLE mince en porte-à-faux, et la platine s'arrête avant ; le banc se
# pose au bord de la table, la console et le doigt dans le vide (serre-joint sur la platine).
X_FIN_PLATINE = -42.0                     # la platine et le bord de la table : rien au-delà
X_CONSOLE = (-50.0, -8.0); EP_CONSOLE = 4.0
X_MONTANT = (-50.0, X_FIN_PLATINE)
VIS_CONSOLE = [(-46.0, s * 12.0) for s in (1, -1)]   # 2 vis M3 × 10 : console sur le montant (2 inserts dans le montant)
H_MARCHE = H - D.R                        # le dessous de la base du doigt = dessus de la console
RONDELLE = 2.0                            # rondelle imprimée sous la tête des vis M3 × 10 de la base : leur pointe reste dans la console
FENETRE = (XP - L_LOIN - JEU, XP + L_PRES + JEU, H - LARG / 2 - JEU, H + LARG / 2 + JEU)
CLOISON_X = (XP - L_LOIN - 8.5, XP + L_PRES + 8.5)
X_ETRIER = (XP - 10.0, XP)                # l'étrier presse le milieu du dessous du servo ; la sortie du câble (bout lointain) reste libre
Z_JAMBES = [(0.3, H - LARG / 2 - JEU - 0.15), (H + LARG / 2 + JEU + 0.15, H + LARG / 2 + 7.2)]
Z_VIS = [sum(z) / 2 for z in Z_JAMBES]
H_CLOISON = Z_JAMBES[1][1] + 0.6
PATTES_DOIGT = [(X_DOIGT0 + 6, s * (D.LARGEUR / 2 + 4.5)) for s in (1, -1)]

def banc():
    m = box(CLOISON_X[0] - 3, Y_FOND - 7, -EP_PLATINE, X_FIN_PLATINE, 20, 0)                                   # platine
    yc = D.LARGEUR / 2 + 11
    m += box(X_MONTANT[0], -yc, -0.01, X_MONTANT[1], yc, H_MARCHE - EP_CONSOLE)                                # montant : la console se visse dessus
    for x, y in VIS_CONSOLE: m -= D.cyl_z(x, y, H_MARCHE - EP_CONSOLE - 6.5, H_MARCHE - EP_CONSOLE + 0.1, 4.0)  # inserts M3
    cl = box(CLOISON_X[0], Y_CLOISON - EP_CLOISON, -0.01, CLOISON_X[1], Y_CLOISON, H_CLOISON)
    cl -= box(FENETRE[0], Y_CLOISON - EP_CLOISON - 1, FENETRE[2], FENETRE[1], Y_CLOISON + 1, FENETRE[3])
    for z in Z_VIS: cl -= D.cyl_y(sum(X_ETRIER) / 2, z, Y_CLOISON - EP_CLOISON - 1, Y_CLOISON + 1, 3.4)        # vis de l'étrier, par l'avant
    return m + cl

def console():
    """Pièce à part (une console en porte-à-faux ne s'imprime pas sans supports) : vissée sur le montant, elle porte la base du
    doigt au-dessus du vide. 2 inserts M3 pour la base du doigt, 2 trous pour les vis qui la tiennent au montant."""
    yc = D.LARGEUR / 2 + 11
    m = box(X_CONSOLE[0], -yc, H_MARCHE - EP_CONSOLE, X_CONSOLE[1], yc, H_MARCHE)
    for x, y in PATTES_DOIGT: m -= D.cyl_z(x, y, H_MARCHE - EP_CONSOLE - 0.1, H_MARCHE + 0.1, 4.0)             # inserts M3, traversants
    for x, y in VIS_CONSOLE: m -= D.cyl_z(x, y, H_MARCHE - EP_CONSOLE - 0.1, H_MARCHE + 0.1, 3.4)
    return m

def etrier():
    """Plaque le servo contre la cloison. Deux jambes, au-dessus et au-dessous du servo, viennent contre l'arrière de la cloison ;
    un insert M3 au bout de chacune ; la traverse appuie sur le dessous du servo."""
    x0, x1 = X_ETRIER; yb = Y_FOND - 3.0
    m = box(x0, yb, Z_JAMBES[0][0], x1, Y_FOND, Z_JAMBES[1][1])
    for z0, z1 in Z_JAMBES: m += box(x0, yb, z0, x1, Y_CLOISON - EP_CLOISON, z1)
    for z in Z_VIS: m -= D.cyl_y(sum(X_ETRIER) / 2, z, Y_CLOISON - EP_CLOISON - 5.0, Y_CLOISON - EP_CLOISON + 0.1, 4.0)
    return m

SERVO, PAL, POULIE = du_servo(servo()), du_servo(palonnier()), poulie()
BANC, ETRIER, CONSOLE = banc(), etrier(), console()
def poulie_a(angle): return du_servo(POULIE.rotate((0, 0, angle)))
def doigt_a(angles): return [p.translate((0, 0, H)) for p in D.doigt(angles)]

def fils(angle=0.0):
    """Les deux fils, en segments droits : du bas (fermer) et du haut (ouvrir) du tambour jusqu'aux canaux du doigt."""
    out = []
    for s, (h0, h1) in zip((-1, 1), GORGES):
        y = y_de_h((h0 + h1) / 2); z = H + s * (R_FOND + 0.15)
        a = np.array([XP, y, z]); b = np.array([X_DOIGT0 - 1, Y_FILS, H + s * D.Z_FIL])
        out.append((a, b))
    return out
def tige(a, b, d=0.4):
    v = b - a; L = float(np.linalg.norm(v)); u = v / L
    ax = np.cross([0, 0, 1], u); s = float(np.linalg.norm(ax)); ang = math.degrees(math.atan2(s, u[2]))
    c = mf.Manifold.cylinder(L, d / 2, d / 2, 8)
    if s > 1e-9: c = c.rotate((0, ang, 0)) if False else c.transform(_rot(ax / s, math.radians(ang)))
    return c.translate(tuple(a))
def _rot(k, t):
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]]); R = np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K
    return [[*R[0], 0], [*R[1], 0], [*R[2], 0]]

if __name__ == '__main__':
    r = {'etat': 'PROTOTYPE, rien n\'est imprimé ni monté'}
    v = lambda a, b: (a ^ b).volume()
    # 1. le servo entre dans la fenêtre et ses pattes s'appuient sur la cloison ; l'étrier le touche sans y entrer
    assert v(SERVO, BANC) < 0.05, f'le servo entre en collision avec le banc ({v(SERVO, BANC):.2f} mm3)'
    assert v(SERVO.translate((0, -0.05, 0)), BANC) > 0, 'les pattes du servo ne s\'appuient pas sur la cloison'
    assert v(SERVO, ETRIER) < 0.05 and v(ETRIER, BANC) < 0.05, 'l\'étrier entre dans le servo ou dans la cloison'
    assert all(len(m.decompose()) == 1 for m in (BANC, ETRIER, POULIE, CONSOLE))
    assert v(CONSOLE, BANC) < 0.05 and v(CONSOLE.translate((0, 0, -0.05)), BANC) > 0, 'la console ne repose pas sur le montant'
    r['montant'] = f'{H_MARCHE - EP_CONSOLE + EP_PLATINE:.0f} mm de plastique sous les inserts de la console (vis M3 × 10 : 6 mm dedans)'
    # 2. la poulie tourne sur un tour complet sans rien toucher (banc, étrier, servo) et coiffe le palonnier sans le toucher
    pire = max(max(v(poulie_a(a), BANC), v(poulie_a(a), ETRIER), v(poulie_a(a), SERVO), v(poulie_a(a), CONSOLE)) for a in range(0, 360, 15))
    assert pire < 0.05, f'la poulie touche en tournant ({pire:.2f} mm3)'
    assert v(du_servo(POULIE), PAL) < 0.05, 'la poulie entre dans le palonnier'
    r['poulie'] = 'tourne sur 360° sans toucher le banc, l\'étrier ni le servo'
    # 3. la vis de la poulie : sa pointe s'arrête au ras du dessous du disque du palonnier
    r['vis_poulie'] = f'Ø 1,3 × {VIS_PAL} : {SOUS_TETE:.1f} mm de plastique sous la tête, {EP_DISQUE} mm dans le palonnier, pointe au ras du disque'
    # 4. le doigt : base sur la marche, pliage complet sans toucher le banc
    dg = doigt_a([0, 0, 0])
    vis_base = [D.cyl_z(x, y, H_MARCHE + 4.0 + RONDELLE - 10.0, H_MARCHE + 4.0 + RONDELLE, 3.0) for x, y in PATTES_DOIGT]
    for vb in vis_base: assert vb.bounding_box()[2] > H_MARCHE - EP_CONSOLE - 0.01, 'une vis de la base dépasse sous la console'
    assert v(dg[0], CONSOLE) < 0.05 and v(dg[0].translate((0, 0, -0.05)), CONSOLE) > 0, 'la base du doigt ne repose pas sur la console'
    for angles in ([30] * 3, [60] * 3, [85] * 3, [85, 0, 0], [0, 85, 85]):
        for p in doigt_a(angles)[1:]:
            assert v(p, BANC) < 0.05 and v(p, CONSOLE) < 0.05, f'le doigt plié {angles} touche le banc'
            for vb in vis_base: assert v(p, vb) < 0.01, f'le doigt plié {angles} touche une vis de la base'
    pliages = [[a] * 3 for a in range(0, 86, 5)] + [[a, 0, 0] for a in range(0, 86, 5)] + [[0, a, a] for a in range(0, 86, 5)]
    for angles in pliages:
        for p in doigt_a(angles)[1:]: assert v(p, BANC) < 0.05 and v(p, CONSOLE) < 0.05, f'le doigt plié {angles} touche le banc'
    r['doigt'] = f'{len(pliages)} positions essayées, de tendu à plié à fond : il ne touche ni le banc ni les vis de sa base'
    # 5. les fils : rien sur leur chemin, et ils partent bien dans le prolongement des canaux
    for a, b in fils():
        f = tige(a, b)
        for nom, piece in (('banc', BANC), ('étrier', ETRIER), ('servo', SERVO), ('console', CONSOLE)):
            assert v(f, piece) < 0.01, f'un fil touche le {nom}'
        assert v(f, dg[0].translate((0.2, 0, 0))) < 0.05, 'un fil frotte sur la base du doigt avant d\'entrer dans son canal'
    angles_fils = [round(math.degrees(math.atan2(math.hypot(b[1] - a[1], b[2] - a[2]), b[0] - a[0])), 1) for a, b in fils()]
    r['fils'] = {'longueur libre (mm)': round(float(np.linalg.norm(fils()[0][1] - fils()[0][0])), 1),
                 'écart d\'angle à l\'entrée des canaux (°)': angles_fils, 'rayon d\'enroulement (mm)': R_FOND + 0.15}
    # 6. course et force
    tirer = 16.0                                       # mm de fil à tirer pour plier le doigt à fond (generer_doigt.py)
    tour = math.degrees(tirer / (R_FOND + 0.15))
    assert tour < 270, f'il faudrait tourner le servo de {tour:.0f}° (le SCS0009 en fait environ 300)'
    r['course_servo_deg'] = f'{tour:.0f}° pour plier le doigt à fond (le SCS0009 tourne d\'environ 300°)'
    couple = 2.3 * 9.81 / 100                          # N·m : 2,3 kg·cm, couple de blocage à 6 V d'après les revendeurs
    r['force_dans_le_fil_N'] = {'au blocage (fiche revendeur)': round(couple / ((R_FOND + 0.15) / 1000), 0),
                                'en usage (un tiers)': round(couple / 3 / ((R_FOND + 0.15) / 1000), 0)}
    # 7. visserie
    r['visserie'] = {'base du doigt sur la console': '2 vis M3 × 10 + 2 rondelles imprimées de 2 mm + 2 inserts M3',
                     'console sur le montant': '2 vis M3 × 10 + 2 inserts M3', 'étrier': '2 vis M3 × 10 par l\'avant de la cloison + 2 inserts M3 dans l\'étrier',
                     'poulie sur le palonnier': '1 vis fournie Ø 1,3 × 6,1 (2 trous prévus)', 'palonnier sur le servo': 'sa vis centrale, posée avant la poulie'}
    r['masses_g'] = {n: round(m.volume() * 1.25e-3, 1) for n, m in (('banc', BANC), ('console', CONSOLE), ('étrier', ETRIER), ('poulie', POULIE))}
    # fichiers, posés pour l'impression
    poses = {'banc_doigt_platine': BANC.translate((0, 0, EP_PLATINE)),
             'banc_doigt_etrier': ETRIER.transform([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, -(Y_FOND - 3.0)]]),   # traverse sur le plateau, jambes en l'air
             'banc_doigt_poulie': POULIE.translate((0, 0, -H_P0)),
             'banc_doigt_console': CONSOLE.translate((0, 0, -(H_MARCHE - EP_CONSOLE))),
             'banc_doigt_rondelles': D.cyl_z(0, 0, 0, RONDELLE, 8.0) - D.cyl_z(0, 0, -1, RONDELLE + 1, 3.4) + (D.cyl_z(12, 0, 0, RONDELLE, 8.0) - D.cyl_z(12, 0, -1, RONDELLE + 1, 3.4))}                                            # creux du palonnier en dessous
    for nom, m in poses.items():
        bb = m.bounding_box(); assert abs(bb[2]) < 0.05, f'{nom} : mal posé ({bb[2]:.2f})'
        mesh(m).export(OUT / f'{nom}.stl'); r.setdefault('stl', []).append(f'{nom}.stl')
    json.dump(r, open(OUT / 'verification_banc_doigt.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False, indent=1))
