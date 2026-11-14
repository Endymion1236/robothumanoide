"""Pince à mâchoires parallèles pour le bras de Câlin (STS3215) — V3 : sans point mort (14/11/2026).

V3 : en V2, le pivot du bras libre était juste DERRIÈRE celui du bras moteur. Pince presque fermée
(20 mm entre les mâchoires), les deux bras s'alignaient avec le doigt : à ce « point mort », plus rien
ne tenait le doigt droit. Essai réel du 14/11/2026 : un doigt s'est retourné, a coincé la pince, et les
dents des engrenages ont sauté. V3 : le pivot du bras libre est déplacé en DIAGONALE (vers l'arrière et
vers l'extérieur) : les bras ne s'alignent plus jamais avec le doigt sur toute la course. Les deux pivots
sont maintenant des poteaux de la base (plus de pivot sur la bride), le poteau de l'engrenage B est plus gros.
Engrenages : fond de dent plat (en V2, la tête de chaque dent passait à 0,03 mm du fond de la dent d'en face).
Bras libres : élargis à 15 mm (2,45 mm de paroi autour des roulements au lieu de 0,95). Bouchons : inchangés.

V2 (11/11/2026) : en V1, un gobelet de 80 mm tenu au milieu des mâchoires butait contre la base et
l'engrenage A, la marge était de 7,5 mm par côté et les mâchoires plates le tenaient mal. Bras de 50 mm,
mâchoires de 40 mm placées plus en avant et creusées en arrondi (rayon 45) qui centrent le gobelet.

Principe : le servo fait tourner l'engrenage A ; l'engrenage B (même taille) tourne en sens inverse.
Chaque engrenage porte un bras moteur ; un bras libre parallèle le double (parallélogramme), si bien que
chaque doigt reste parallèle à l'autre en s'ouvrant. Pivots sur roulements 623ZZ (3 × 10 × 4) et vis M3.
La pince s'enfile sur le bout de l'avant-bras (fourche du coude V1.2) et se fixe par les 2 vis M3 × 30
de l'entretoise du bout.

Repère de la pince : X vers l'avant (prolongement de l'avant-bras), Y = sens de fermeture des doigts
(= axe du coude), Z = axe du servo de la pince. Y = 0 : plan de symétrie entre les doigts.
Ce programme construit les pièces, vérifie l'ouverture et l'absence de collision sur tout le mouvement,
exporte les STL (posées pour l'impression) et des images. Prototype : aucune validation physique.
"""
from pathlib import Path
import json, math
import numpy as np, manifold3d as mf, trimesh as tm

OUT = Path(__file__).resolve().parent / 'sortie'; OUT.mkdir(exist_ok=True)

# ---------------- Mesures (servo de Nicolas, 08/11/2026) ----------------
SL, SW = 45.2, 24.4               # boîtier
H_BAS, H_HAUT = 28.8, 33.0         # dessus côté palonnier / partie haute (à partir de 15,6 du bout palonnier)
HAUT_DEBUT, HAUT_ARC = 15.6, 10.0
AXE_BOUT = 8.1                     # axe du palonnier à 8,1 du bout
PAL_D, PAL_H = 19.7, 4.3           # palonnier
CERCLE_TROUS = 13.45               # 4 trous M2,5 du palonnier
BOSS_L, BOSS_W, BOSS_BORD, RELIEF = 11.9, 18.3, 5.0, 2.0
FOURCHE_EP, FOURCHE_L = 45.3, 24.0 # avant-bras (fourche V1.2) : épaisseur hors tout, largeur des plaques
ENT_B, VIS_ENT_Y = 15.0, 6.0       # entretoise du bout : 15 de long, vis M3 à ±6 de l'axe

# ---------------- Choix de conception ----------------
JEU = 0.2
AX, AY = 40.0, 15.0                # axe du servo = centre de l'engrenage A
MOD, DENTS = 1.5, 20               # module 1,5 ; 20 dents : diamètre primitif 30 = entraxe
R_PRIM = MOD * DENTS / 2
L_BRAS = 50.0                      # longueur des bras (pivot → axe du doigt)
PIV_LIBRE = (2.0, 34.0)            # pivot du bras libre côté +Y (côté -Y : symétrique)
GX, GY = PIV_LIBRE[0] - AX, PIV_LIBRE[1] - AY   # du pivot du bras moteur au pivot du bras libre = du trou avant au trou arrière du doigt
ENTRAXE_DOIGT = math.hypot(GX, GY) # distance entre les deux trous du doigt
E_DOIGT = 5.0                      # de l'axe du doigt à sa face de serrage
Z0 = H_BAS + PAL_H + 1.0           # dessous des engrenages : 1 mm au-dessus du palonnier (patin), 1,1 au-dessus de la partie haute
EP_ENG, EP_DOIGT, EP_LIBRE, JEU_Z = 6.0, 4.0, 5.0, 0.5
Z_DOIGT = Z0 + EP_ENG + JEU_Z
Z_LIBRE = Z_DOIGT + EP_DOIGT + JEU_Z
PAD_LONG, PAD_EP, PAD_BAS = 40.0, 6.0, -20.0
PAD_DEVANT = 7.0                   # la mâchoire commence 7 mm devant l'axe du doigt (au-delà du bout du bras)
PAD_R = 45.0                       # mâchoires creusées en arc de rayon 45 : elles centrent un gobelet de 50 à 90 mm
PAD_FLECHE = PAD_R - math.sqrt(PAD_R**2 - (PAD_LONG / 2) ** 2)   # les bouts avancent de 4,7 mm vers l'intérieur
ECART_MAX = 110.0
ROUL_D, ROUL_EP = 10.1, 4.0        # logement de roulement 623 (10 mm, serré 0,1)
W_LIBRE = 15.0                     # largeur du bras libre. 12 mm jusqu'au 14/11/2026 : il ne restait que 0,95 mm de paroi
                                   # autour du roulement, qui l'a fendue en entrant (retour d'impression de Nicolas)
PAROI_ROULEMENT_MIN = 1.8          # mm de plastique à garder autour de chaque roulement enfoncé en force
M3, M3_INSERT, M2_5 = 3.4, 4.0, 2.9
INSERT_COURT = 4.3                 # insert M3 x 5 x 4 (Ø ext. 5, 4 de long) : trou de 4,3 conseillé par le fabricant
M3_TARAUD = 2.8                    # la vis M3 se visse directement dans le plastique (bout des bras libres)
PASSAGE_TETE = 6.5                 # au-dessus d'un roulement : la tête de vis (5,5) n'appuie que sur la bague intérieure

# angles du bras moteur (depuis +X vers +Y) : fermé = doigts qui se touchent, ouvert = 95 mm
# Écarts mesurés au CREUX des mâchoires. Fermée : 14 mm au creux, soit 4,6 mm entre les bouts des mâchoires.
ECART_MIN = 14.0
TH_FERME = math.degrees(math.asin((ECART_MIN / 2 + E_DOIGT - AY) / L_BRAS))
TH_OUVERT = math.degrees(math.asin((ECART_MAX / 2 + E_DOIGT - AY) / L_BRAS))

def box(x0, y0, z0, x1, y1, z1): return mf.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))
def cyl(x, y, z0, z1, d, n=64): return mf.Manifold.cylinder(z1 - z0, d / 2, d / 2, n).translate((x, y, z0))
def extruder(poly, z0, z1): return mf.Manifold.extrude(mf.CrossSection([poly]), z1 - z0).translate((0, 0, z0))
def mesh(m):
    a = m.to_mesh(); return tm.Trimesh(vertices=a.vert_properties[:, :3], faces=a.tri_verts, process=True)

def profil_engrenage(dents=DENTS, module=MOD, pression=20.0, jeu_dent=0.35, pts=8):
    """Profil en développante de cercle (contour 2D), centré sur l'origine, une dent sur +X."""
    rp = module * dents / 2; rb = rp * math.cos(math.radians(pression))
    ra, rf = rp + module, rp - 1.25 * module
    inv = lambda a: math.tan(a) - a
    ap = math.radians(pression)
    demi = (math.pi / (2 * dents)) - jeu_dent / (2 * rp) + inv(ap)        # demi-épaisseur angulaire au cercle de base
    flanc = []
    for k in range(pts + 1):
        r = rb + (ra - rb) * k / pts
        a = math.acos(min(1.0, rb / r)); flanc.append((r, demi - inv(a)))
    contour = []
    for i in range(dents):
        c = 2 * math.pi * i / dents
        pied = max(rf, 0.1)
        # V3 : fond de dent PLAT (un point au pied de chaque flanc). En V2 le fond était en V (un seul point au
        # milieu du creux) : la tête de la dent d'en face passait à 0,03 mm du fond, donc frottait une fois imprimée
        # et poussait les engrenages à s'écarter. Mesuré par verifier_engrenages.py.
        contour.append((pied * math.cos(c - demi), pied * math.sin(c - demi)))
        for r, t in flanc: contour.append((r * math.cos(c - t), r * math.sin(c - t)))
        for r, t in reversed(flanc): contour.append((r * math.cos(c + t), r * math.sin(c + t)))
        contour.append((pied * math.cos(c + demi), pied * math.sin(c + demi)))
    return contour

def barre(p, q, larg):
    """Contour 2D d'une barre arrondie de p à q."""
    (x0, y0), (x1, y1) = p, q
    a = math.atan2(y1 - y0, x1 - x0); n = (-math.sin(a) * larg / 2, math.cos(a) * larg / 2)
    pts = []
    for k in range(17):
        t = a + math.pi / 2 + math.pi * k / 16; pts.append((x1 + larg / 2 * math.cos(t - math.pi), y1 + larg / 2 * math.sin(t - math.pi)))
    for k in range(17):
        t = a + math.pi / 2 + math.pi * k / 16; pts.append((x0 + larg / 2 * math.cos(t), y0 + larg / 2 * math.sin(t)))
    return pts

# ---------------- Pièces mobiles (construites à leur position « bras à 0° ») ----------------
def engrenage_a(longueur_vis=8):
    """Engrenage moteur, vissé sur le palonnier, avec son bras (côté +Y).
    longueur_vis : longueur (sous tête) des 4 vis M2,5. Le logement des têtes est creusé pour qu'elles
    entrent de 2,5 mm dans le palonnier, en gardant au moins 2 mm de plastique sous la tête."""
    m = extruder(profil_engrenage(), Z0, Z0 + EP_ENG).translate((AX, AY, 0))
    m += extruder(barre((AX, AY), (AX + L_BRAS, AY), 11), Z0, Z0 + EP_ENG)
    m += cyl(AX, AY, Z0 - 1.0, Z0, 18)                                     # patin sur le palonnier
    for k in range(4):                                                      # 4 vis M2,5 du palonnier, lamées
        a = math.radians(45 + 90 * k); x, y = AX + CERCLE_TROUS / 2 * math.cos(a), AY + CERCLE_TROUS / 2 * math.sin(a)
        sous_tete = max(2.0, min(EP_ENG + 1.0 - 2.0, longueur_vis - 2.5))           # plastique sous la tête (patin compris)
        m -= cyl(x, y, Z0 - 1.1, Z0 + EP_ENG + 0.1, M2_5, 24); m -= cyl(x, y, Z0 - 1.0 + sous_tete, Z0 + EP_ENG + 0.1, 5.4, 24)
    m -= cyl(AX, AY, Z0 - 1.1, Z0 + EP_ENG + 0.1, 7)                       # vis centrale du palonnier
    m -= cyl(AX + L_BRAS, AY, Z0 - 0.1, Z0 + EP_ENG + 0.1, M3, 24)          # axe du doigt
    return m

def engrenage_b():
    """Engrenage mené, sur roulement 623, avec son bras (côté -Y), symétrique ; dents décalées d'une demi-dent."""
    prof = [(x, -y) for x, y in reversed(profil_engrenage())]          # miroir : contour remis dans le bon sens
    m = extruder(prof, Z0, Z0 + EP_ENG).rotate((0, 0, 180 / DENTS)).translate((AX, -AY, 0))
    m += extruder(barre((AX, -AY), (AX + L_BRAS, -AY), 11), Z0, Z0 + EP_ENG)
    m -= cyl(AX, -AY, Z0 - 0.1, Z0 + ROUL_EP, ROUL_D, 48)                  # logement du roulement (par-dessous)
    m -= cyl(AX, -AY, Z0 - 0.1, Z0 + EP_ENG + 0.1, PASSAGE_TETE, 32)       # passage de la tête de vis
    m -= cyl(AX + L_BRAS, -AY, Z0 - 0.1, Z0 + EP_ENG + 0.1, M3, 24)
    return m

def bras_libre(s):
    """Bras libre (s = +1 côté +Y, -1 côté -Y) : un roulement 623 à chaque bout, enfoncé par-dessous.
    Au pivot comme au doigt, la tête de vis descend dans le passage de 6,5 et serre la bague intérieure :
    le bras tourne mais ne peut pas se soulever (correction du 13/11/2026 : au doigt, la vis vissée dans
    le bras n'entrait que de 2,5 mm dans le roulement du doigt ; en serrant, le doigt basculait, soulevait
    le bras et la vis sortait : la mâchoire tournait et la pince s'ouvrait)."""
    p, q = (PIV_LIBRE[0], s * PIV_LIBRE[1]), (PIV_LIBRE[0] + L_BRAS, s * PIV_LIBRE[1])
    m = extruder(barre(p, q, W_LIBRE), Z_LIBRE, Z_LIBRE + EP_LIBRE)
    for c in (p, q):
        m -= cyl(c[0], c[1], Z_LIBRE - 0.1, Z_LIBRE + ROUL_EP, ROUL_D, 48)
        m -= cyl(c[0], c[1], Z_LIBRE - 0.1, Z_LIBRE + EP_LIBRE + 0.1, PASSAGE_TETE, 32)
    return m

def bouchon_doigt(insert=False):
    """Remplace le roulement ARRIÈRE du doigt (même trou de 10,1) : la vis M3 x 8 du bras libre s'y visse
    (trou de 2,8). Ainsi les doigts déjà imprimés restent bons."""
    return cyl(0, 0, 0, ROUL_EP, 9.9, 64) - cyl(0, 0, -0.1, ROUL_EP + 0.1, INSERT_COURT if insert else M3_TARAUD, 32)

def doigt(s, insert_arriere=False):
    """Doigt : plaque qui relie les deux bras + mâchoire qui descend. Trou avant : roulement 623.
    Trou arrière : logement de 10,1 pour le bouchon, ou (insert_arriere) trou de 4,3 pour un insert M3 x 5 x 4."""
    q1 = (AX + L_BRAS, s * AY); q2 = (q1[0] + GX, q1[1] + s * GY)
    m = extruder(barre(q2, q1, 14), Z_DOIGT, Z_DOIGT + EP_DOIGT)
    for q, d in ((q1, ROUL_D), (q2, INSERT_COURT if insert_arriere else ROUL_D)):
        m -= cyl(q[0], q[1], Z_DOIGT - 0.1, Z_DOIGT + EP_DOIGT + 0.1, d, 48)
    # mâchoire : plaque verticale devant l'axe du doigt ; face de serrage creusée en arc (creux à E_DOIGT de l'axe)
    xm0 = q1[0] + PAD_DEVANT
    yi = q1[1] - s * E_DOIGT                                   # face au creux de l'arc
    y_bout = yi - s * PAD_FLECHE                               # face aux deux bouts de la mâchoire
    y0, y1 = (y_bout, yi + PAD_EP) if s > 0 else (yi - PAD_EP, y_bout)
    m += box(q1[0] + 4, min(y0, q1[1]), Z_DOIGT, xm0 + 2, max(y1, q1[1]), Z_DOIGT + EP_DOIGT)   # jonction
    machoire = box(xm0, y0, PAD_BAS, xm0 + PAD_LONG, y1, Z_DOIGT + EP_DOIGT)
    machoire -= cyl(xm0 + PAD_LONG / 2, yi - s * PAD_R, PAD_BAS - 1, Z_DOIGT + EP_DOIGT + 1, 2 * PAD_R, 192)
    m += machoire
    ry0, ry1 = (y1, y1 + 4) if s > 0 else (y0 - 4, y0)                                          # nervure
    m += box(xm0 + PAD_LONG / 2 - 2, ry0 if s > 0 else y0 - 4, PAD_BAS + 5,
             xm0 + PAD_LONG / 2 + 2, (y1 + 4) if s > 0 else y0, Z_DOIGT + EP_DOIGT)
    return m

# ---------------- Pièces fixes ----------------
X0S = AX + AXE_BOUT - SL           # arrière du servo
SY0, SY1 = AY - SW / 2, AY + SW / 2
Z_BASE = -7.0                      # dessous de la base
P_LIBRE = [(PIV_LIBRE[0], PIV_LIBRE[1]), (PIV_LIBRE[0], -PIV_LIBRE[1])]
ZC = 15.0                          # axe de l'avant-bras dans la hauteur de la pince
XF = X0S - JEU - 3                 # le bout de l'avant-bras bute contre le mur arrière du logement du servo
# Bride à dessous plat : les piliers s'arrêtent 0,5 mm SOUS le dessus du servo ; en vissant, la bride
# appuie sur le servo avec 0,5 mm de serrage. Elle s'imprime à plat, sans support.
BRIDE_X0, BRIDE_X1, BRIDE_Z = 9.0, 22.0, H_HAUT - 0.5   # V3 : commence à 9 (1 mm après le poteau du bras libre)
D_POTEAU_B, D_POTEAU_LIBRE = 16.0, 12.0

def base():
    b = box(XF - ENT_B, -25, Z_BASE, 55, 39, Z_BASE + 4)                       # plaque
    b += box(XF - ENT_B, -(PIV_LIBRE[1] + 7), Z_BASE, PIV_LIBRE[0] + 8, PIV_LIBRE[1] + 7, Z_BASE + 4)   # élargie sous les poteaux des bras libres
    # logement du servo : rails d'appui sous ses bords, murs
    for y0, y1 in ((SY0 - JEU, SY0 + 2), (SY1 - 2, SY1 + JEU)):
        b += box(X0S - JEU, y0, -3, X0S + SL + JEU, y1, 0)
    b += box(X0S - JEU - 3, SY0 - JEU - 3, -3, X0S + SL + JEU + 3, SY1 + JEU + 3, 15)
    b -= box(X0S - JEU, SY0 - JEU, -3.01, X0S + SL + JEU, SY1 + JEU, 15.1)
    b += box(X0S - JEU, SY0 - JEU, -3, X0S + SL + JEU, SY0 + 2, 0) + box(X0S - JEU, SY1 - 2, -3, X0S + SL + JEU, SY1 + JEU, 0)
    b -= box(X0S + 17, SY0 - 4, -3, X0S + 29, SY1 + 4, 15.1)                  # sorties de câble des deux côtés
    # piliers de la bride (inserts M3 en haut)
    for y0 in (SY0 - JEU - 3 - 8, SY1 + JEU + 3):
        b += box(BRIDE_X0 + 1, y0, Z_BASE, BRIDE_X0 + 9, y0 + 8, BRIDE_Z)
        b -= cyl(BRIDE_X0 + 5, y0 + 4, BRIDE_Z - 9, BRIDE_Z + 0.1, M3_INSERT, 24)
    # poteau de l'engrenage B et poteaux des deux bras libres : insert M3 en haut, épaulement pour la bague intérieure
    b += box(AX - 3, -AY + 1, Z_BASE, AX + 3, SY0 - JEU - 3 + 0.1, 15)         # nervure : poteau de B appuyé contre le mur du servo
    for s_ in (1, -1):                                                         # goussets : poteaux appuyés contre le manchon
        x, y = PIV_LIBRE[0], s_ * PIV_LIBRE[1]
        ya, yb = sorted((y, y - s_ * 6)); b += box(x - 6, ya, Z_BASE, x + 8, yb, BRIDE_Z)
        ya, yb = sorted((y - s_ * 6, s_ * (FOURCHE_EP / 2 + JEU + 2))); b += box(x - 6, ya, Z_BASE, X0S - JEU, yb, BRIDE_Z)
    for (x, y, zt, d) in ((AX, -AY, Z0, D_POTEAU_B), (*P_LIBRE[0], Z_LIBRE, D_POTEAU_LIBRE), (*P_LIBRE[1], Z_LIBRE, D_POTEAU_LIBRE)):
        b += cyl(x, y, Z_BASE, zt - 0.6, d) + cyl(x, y, zt - 0.6, zt, 6.5, 32)
        b -= cyl(x, y, zt - 9, zt + 0.1, M3_INSERT, 24)
    # manchon sur le bout de l'avant-bras (entretoise du bout), vis M3 par le côté +Y
    yi, zi = FOURCHE_EP / 2 + JEU, FOURCHE_L / 2 + JEU
    b += box(XF - ENT_B, -yi - 3, Z_BASE, XF + 3, yi + 3, ZC + zi + 3)
    b -= box(XF - ENT_B - 0.1, -yi, ZC - zi, XF, yi, ZC + zi)
    for dz in (-VIS_ENT_Y, VIS_ENT_Y):
        b -= mf.Manifold.cylinder(10, M3 / 2, M3 / 2, 24).rotate((-90, 0, 0)).translate((XF - ENT_B / 2, yi - 1, ZC + dz))
    return b

def bride():
    """Bride posée sur la partie haute du servo (0,5 mm de serrage au vissage). V3 : simple barre, plus de pivot."""
    y0, y1 = SY0 - JEU - 3 - 8, SY1 + JEU + 3 + 8
    m = box(BRIDE_X0, y0, H_HAUT, BRIDE_X1, y1, H_HAUT + 4)
    for yc in (y0 + 4, y1 - 4):
        m -= cyl(BRIDE_X0 + 5, yc, H_HAUT - 0.1, H_HAUT + 4.1, M3, 24)
    return m

def servo_ref():
    s = box(X0S, SY0, 0, X0S + SL, SY1, H_BAS)
    haut = box(X0S, SY0, H_BAS, AX + AXE_BOUT - HAUT_DEBUT, SY1, H_HAUT) - cyl(AX, AY, H_BAS - 0.1, H_HAUT + 0.1, 2 * HAUT_ARC)
    s += haut + cyl(AX, AY, H_BAS, H_BAS + PAL_H, PAL_D)
    s += box(AX + AXE_BOUT - BOSS_BORD - BOSS_L, AY - BOSS_W / 2, -RELIEF, AX + AXE_BOUT - BOSS_BORD, AY + BOSS_W / 2, 0)
    s += cyl(AX, AY, -RELIEF, 0, 5.5)
    return s

def avant_bras_ref():
    return box(XF - 60, -FOURCHE_EP / 2, ZC - FOURCHE_L / 2, XF, FOURCHE_EP / 2, ZC + FOURCHE_L / 2)

# ---------------- Mise en position pour un angle de bras θ ----------------
def tourner(m, cx, cy, deg): return m.translate((-cx, -cy, 0)).rotate((0, 0, deg)).translate((cx, cy, 0))
def pose(th):
    """Pièces mobiles pour l'angle θ du bras moteur côté +Y (côté -Y : symétrique)."""
    q = lambda s: (AX + L_BRAS * math.cos(math.radians(th)), s * (AY + L_BRAS * math.sin(math.radians(th))))
    p = {'engrenage A': tourner(EA, AX, AY, th), 'engrenage B': tourner(EB, AX, -AY, -th),
         'bras libre +Y': tourner(BL[1], *P_LIBRE[0], th), 'bras libre -Y': tourner(BL[-1], *P_LIBRE[1], -th)}
    for s, nom in ((1, 'doigt +Y'), (-1, 'doigt -Y')):
        q1 = q(s); p[nom] = DG[s].translate((q1[0] - (AX + L_BRAS), q1[1] - s * AY, 0))
    return p

# ---------------- Cinématique : le doigt peut-il se retourner ? ----------------
def bras_de_levier(th, g=None):
    """Distance (mm) entre les deux bras parallèles pour l'angle θ : c'est le bras de levier qui tient le
    doigt droit. À 0, bras moteur, bras libre et doigt sont alignés : POINT MORT, le doigt peut se retourner."""
    gx, gy = g or (GX, GY); t = math.radians(th)
    return abs(gx * math.sin(t) - gy * math.cos(t))

def deux_montages(th, g=None, L=None):
    """Pour un angle θ du bras moteur, le trou arrière du doigt a DEUX places possibles (intersection de deux
    cercles) : la bonne (doigt parallèle) et la mauvaise (doigt retourné). Renvoie (bonne, mauvaise, écart en mm).
    Le doigt ne peut passer de l'une à l'autre que là où elles se confondent (écart = 0)."""
    gx, gy = g or (GX, GY); L = L or L_BRAS; t = math.radians(th)
    q1 = np.array([AX + L * math.cos(t), AY + L * math.sin(t)]); f = np.array([AX + gx, AY + gy]); D = math.hypot(gx, gy)
    d = np.linalg.norm(f - q1)                     # du trou avant du doigt au pivot du bras libre
    a = (D * D - L * L + d * d) / (2 * d); h2 = D * D - a * a
    if h2 < 0: return None, None, 0.0              # montage impossible
    h = math.sqrt(h2); e = (f - q1) / d; n = np.array([-e[1], e[0]]); m = q1 + a * e
    sols = [m + h * n, m - h * n]; bonne = q1 + np.array([gx, gy])
    sols.sort(key=lambda p: np.linalg.norm(p - bonne))
    return sols[0], sols[1], float(np.linalg.norm(sols[0] - sols[1]))

def angle_doigt(th, mauvaise=False, g=None):
    """Rotation du doigt (degrés) par rapport à sa position parallèle : 0 pour le bon montage."""
    gx, gy = g or (GX, GY); t = math.radians(th)
    q1 = np.array([AX + L_BRAS * math.cos(t), AY + L_BRAS * math.sin(t)])
    p = deux_montages(th, g)[1 if mauvaise else 0]
    a = math.degrees(math.atan2(p[1] - q1[1], p[0] - q1[0]) - math.atan2(gy, gx))
    return (a + 180) % 360 - 180

EA, EB = engrenage_a(), engrenage_b()
BL = {1: bras_libre(1), -1: bras_libre(-1)}
DG = {1: doigt(1), -1: doigt(-1)}
BASE, BRIDE, SERVO, AVB = base(), bride(), servo_ref(), avant_bras_ref()

if __name__ == '__main__':
    rapport = {'version': 'V3', 'validation_physique': False, 'angles_bras_deg': {'ferme': round(TH_FERME, 1), 'ouvert': round(TH_OUVERT, 1)},
               'rotation_servo_deg': round(TH_OUVERT - TH_FERME, 1), 'collisions': [], 'pieces': {}}
    fixes = {'base': BASE, 'bride': BRIDE, 'servo': SERVO, 'avant-bras': AVB}
    for nom, a, b in (('base/servo', BASE, SERVO), ('base/avant-bras', BASE, AVB), ('base/bride', BASE, BRIDE)):
        assert (a ^ b).volume() < 0.01, (nom, (a ^ b).volume())
    rapport['bride_sur_servo_mm3 (serrage voulu)'] = round((BRIDE ^ SERVO).volume(), 1)
    # accès qui doivent rester libres : tournevis des 2 vis du manchon (par le côté +Y), sortie du câble du servo (des deux côtés)
    yi = FOURCHE_EP / 2 + JEU + 3
    for dz in (-VIS_ENT_Y, VIS_ENT_Y):
        acces = mf.Manifold.cylinder(40, 3.2, 3.2, 24).rotate((-90, 0, 0)).translate((XF - ENT_B / 2, yi + 0.05, ZC + dz))
        assert (acces ^ BASE).volume() < 0.01, 'un poteau gêne le tournevis des vis du manchon'
    for y0, y1 in ((SY1 + JEU + 3.05, SY1 + 20), (SY0 - 20, SY0 - JEU - 3.05)):
        assert (box(X0S + 17.5, y0, -2.9, X0S + 28.5, y1, 15) ^ BASE).volume() < 0.01, 'la sortie du câble est bouchée'
    rapport['acces_libres'] = ['tournevis des 2 vis du manchon', 'sortie du câble des deux côtés']
    # paroi de plastique autour de chaque roulement enfoncé en force (trop fine, elle se fend à l'enfoncement)
    parois = {'bras libre': (W_LIBRE - ROUL_D) / 2, 'doigt': (14 - ROUL_D) / 2, 'engrenage B': R_PRIM - 1.25 * MOD - ROUL_D / 2}
    rapport['paroi_autour_des_roulements_mm'] = {k: round(v, 2) for k, v in parois.items()}
    assert min(parois.values()) >= PAROI_ROULEMENT_MIN, ('paroi trop fine autour d\'un roulement', parois)
    rapport['jeu_bride_piliers_mm (fermé au vissage)'] = round(H_HAUT - BRIDE_Z, 2)
    ouvertures = []
    angles = list(np.linspace(TH_FERME, TH_OUVERT, 24))
    for th in angles:
        p = pose(th); noms = list(p)
        for i, a in enumerate(noms):
            for b in noms[i + 1:]:
                v = (p[a] ^ p[b]).volume()
                if v > 0.01: rapport['collisions'].append((round(th, 1), a, b, round(v, 2)))
            for fn, f in fixes.items():
                v = (p[a] ^ f).volume()
                if v > 0.01: rapport['collisions'].append((round(th, 1), a, fn, round(v, 2)))
        y_in = AY + L_BRAS * math.sin(math.radians(th)) - E_DOIGT
        ouvertures.append((round(th, 1), round(2 * y_in, 1)))
    rapport['ouverture_mm (angle → écart des mâchoires)'] = [ouvertures[0], ouvertures[len(ouvertures) // 2], ouvertures[-1]]
    # le doigt ne doit jamais pouvoir se retourner (défaut de la V2) : détail dans verifier_cinematique.py
    # côté fermé, les bouts des mâchoires se touchent (butée mécanique) ; côté ouvert, on dépasse la butée de 15°
    th_contact = math.degrees(math.asin((PAD_FLECHE + E_DOIGT - AY) / L_BRAS))
    leviers = [bras_de_levier(t) for t in np.linspace(th_contact, TH_OUVERT + 15, 400)]
    rapport['doigt'] = {'entraxe_des_deux_trous_mm': round(ENTRAXE_DOIGT, 1), 'pivot_bras_libre': list(PIV_LIBRE),
                        'bras_de_levier_min_mm (des mâchoires en contact à 15° après la butée ouverte)': round(min(leviers), 1)}
    assert min(leviers) > 12, 'point mort trop près de la course : le doigt peut se retourner'
    rapport['largeur_hors_tout_mm'] = {f'écart {e}': round(2 * (AY + L_BRAS * math.sin(math.radians(t)) + GY + max(7, W_LIBRE / 2)))
                                       for e, t in ((14, TH_FERME), (80, math.degrees(math.asin((40 + E_DOIGT - AY) / L_BRAS))), (110, TH_OUVERT))}
    # Servo : montage à mi-ouverture quand il est à 2048 ; butées = ± la moitié de la course
    demi = (TH_OUVERT - TH_FERME) / 2 * 4096 / 360
    th_mi = (TH_FERME + TH_OUVERT) / 2
    ecart_mi = 2 * (AY + L_BRAS * math.sin(math.radians(th_mi)) - E_DOIGT)
    rapport['servo_pince'] = {'montage': f'engrenage A posé avec les mâchoires écartées de {ecart_mi:.0f} mm quand le servo est à 2048',
                              'butee_min': round(2048 - demi), 'butee_max': round(2048 + demi),
                              'sens': 'à vérifier au premier essai : le sens « ouvrir » peut être vers la butée min ou max'}
    pieces = {'pince_base': BASE, 'pince_bride': BRIDE, 'pince_engrenage_A': EA, 'pince_engrenage_B': EB,
              'pince_bras_libre_+Y': BL[1], 'pince_bras_libre_-Y': BL[-1], 'pince_doigt_+Y': DG[1], 'pince_doigt_-Y': DG[-1], 'pince_bouchon_doigt': bouchon_doigt(),
              'pince_bouchon_doigt_insert': bouchon_doigt(True),
              'pince_doigt_+Y_insert': doigt(1, True), 'pince_doigt_-Y_insert': doigt(-1, True)}
    masse = 0
    variantes = ('_insert',)
    for nom, m in pieces.items():
        t = mesh(m); assert t.is_watertight and len(t.split(only_watertight=False)) == 1, nom
        # orientation d'impression : face plane la plus large sur le plateau, sans surplomb
        if nom in ('pince_engrenage_A', 'pince_doigt_+Y', 'pince_doigt_-Y', 'pince_doigt_+Y_insert', 'pince_doigt_-Y_insert'):
            t.apply_transform(tm.transformations.rotation_matrix(math.pi, (1, 0, 0)))   # retourné : dessus sur le plateau
        t.apply_translation(-t.bounds[0]); t.export(OUT / f'{nom}.stl')
        g = t.volume / 1000 * 1.24 * 0.6                                       # PLA, ~60 % plein
        # pose d'impression : surface vraiment à plat sur le plateau, et surplombs (faces tournées vers le bas, en l'air)
        zc = t.triangles_center[:, 2]; nz = t.face_normals[:, 2]
        pose_mm2 = float(t.area_faces[(zc < 0.01) & (nz < -0.99)].sum())
        surplomb = float(t.area_faces[(zc > 0.3) & (nz < -0.7)].sum())
        assert pose_mm2 >= 40, (nom, 'pas posée à plat', pose_mm2)
        masse += 0 if nom.endswith(variantes) else g
        rapport['pieces'][nom] = {'encombrement_mm': [round(v, 1) for v in t.extents], 'masse_g_environ': round(g),
                                  'surface_sur_le_plateau_mm2': round(pose_mm2), 'plafonds_en_pont_mm2': round(surplomb)}
    # variantes de l'engrenage A pour des vis M2,5 plus courtes (celles fournies avec le servo)
    for lv in (4, 5, 6):
        t = mesh(engrenage_a(lv)); assert t.is_watertight
        t.apply_transform(tm.transformations.rotation_matrix(math.pi, (1, 0, 0)))
        t.apply_translation(-t.bounds[0]); t.export(OUT / f'pince_engrenage_A_vis{lv}mm.stl')
        rapport['pieces'][f'pince_engrenage_A_vis{lv}mm'] = {'plastique_sous_tete_mm': max(2.0, lv - 2.5),
                                                            'vis_dans_palonnier_mm': round(lv - max(2.0, lv - 2.5), 1)}
    rapport['masse_pieces_imprimees_g'] = round(masse); rapport['masse_avec_servo_g'] = round(masse + 55)
    (OUT / 'verification_pince.json').write_text(json.dumps(rapport, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in rapport.items() if k != 'pieces'}, indent=1, ensure_ascii=False))
