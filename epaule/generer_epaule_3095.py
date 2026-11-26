"""Épaule du bras de Câlin avec le gros servo Feetech STS3095 (95 kg·cm) — V1, 26/11/2026.
PROTOTYPE : dessinée et contrôlée par le calcul, jamais imprimée ni montée.

Ce qui change par rapport à l'épaule du STS3215 (generer_epaule.py) :
  - le servo est plus gros (65 × 30 × 47,8, mesuré par Nicolas le 25/11/2026) et a un disque de CHAQUE côté, à 61,4 mm l'un de
    l'autre : la fourche du haut du bras passe de 45 à 61,4 mm entre disques ;
  - il n'entre pas dans l'ancien berceau : nouveau BERCEAU, une « boîte » ouverte dessus où le servo descend par le haut. Le servo
    est tenu par la FORME (fond, mur arrière, deux joues, lèvre devant) et par une BRIDE vissée dessus ; aucune petite vis du
    boîtier n'est utilisée (leur place n'est connue qu'à 1 mm près) ;
  - nouveau BÂTI (décision de Nicolas du 25/11/2026) : même pied et mêmes 4 trous (il se revisse sur le plateau du socle
    tournant), mais le mur est reculé au bord du pied et le mât du ressort repoussé, pour laisser passer la fourche élargie.
Ce qui ne change PAS : la hauteur de l'axe (95 mm au-dessus du pied), la longueur épaule → coude (120 mm), la platine du coude et
son berceau, l'avant-bras, le poignet, la pince.

Repère : origine sur l'axe de l'épaule, X vers l'avant, Z vers le haut, Y le long de l'axe ; y = 0 est la face du mur où se visse
le berceau. Angle de l'épaule : 0° = bras horizontal vers l'avant.
Lancer : python generer_epaule_3095.py → sortie/epaule3095_*.stl, sortie/verification_epaule_3095.json"""
import json, math, sys
from pathlib import Path
import numpy as np, trimesh as tm, manifold3d as mf
import generer_epaule as E

OUT = E.OUT
box, cyl_y, mesh, tourner_y, prisme_xz, placer = E.box, E.cyl_y, E.mesh, E.tourner_y, E.prisme_xz, E.placer
def cyl_z(x, y, z0, z1, d, n=32): return mf.Manifold.cylinder(z1 - z0, d / 2, d / 2, n).translate((x, y, z0))

# ---------------- Le servo STS3095, mesuré par Nicolas le 25/11/2026 (epaule/sts3095/plan_sts3095.png, validé) ----------------
S_L, S_W, S_T = 65.0, 30.0, 47.8      # longueur, largeur (face du logo), épaisseur entre les deux faces à disque
S_AXE = 17.9                          # axe à 17,9 du bout côté palonnier (47,1 de l'autre bout)
D_DISQUE, DEP_DISQUE = 29.6, 6.8      # disques Ø 29,6 ; dessus du disque à 6,8 de la face → 61,4 entre les deux disques
ENTRE_DISQUES = S_T + 2 * DEP_DISQUE  # 61,4
CERCLE_TROUS, D_VIS_DISQUE = 23.9, 3.0     # 8 trous filetés traversants sur Ø 23,9 ; vis fournies Ø 2,6 × 9 → passage de 3,0
SOUS_TETE = 4.0                       # plastique sous la tête des vis de 9 mm (entre 3 et 5,2 : notes du 25/11/2026)
D_CENTRE = 16.0                       # trou au centre : moyeu Ø 13,8 et tête de la vis centrale (3,5 mm au-dessus du disque)
PRISE_X = (22.0 - S_AXE, 35.2 - S_AXE)     # prises SVG : de 22 à 35,2 du bout côté palonnier → de 4,1 à 17,3 derrière l'axe

# ---------------- Empilement le long de l'axe (Y) ----------------
EP_SOCLE = 5.0                        # socle du berceau, contre le mur (inserts M3 de 3,8 dedans)
JEU_SOCLE = 2.0                       # entre le socle et la moitié basse du bras
EP_BAS, EP_HAUT = 6.0, 7.0            # épaisseur des deux moitiés du bras ; amincies à 4 mm sur les disques (têtes de vis noyées)
Y_BAS0 = EP_SOCLE + JEU_SOCLE         # 7 : dessous de la moitié basse
Y_D1 = Y_BAS0 + EP_BAS                # 13 : dessus du disque côté mur
YC = Y_D1 + ENTRE_DISQUES / 2         # 43,7 : milieu du servo
Y_D2 = Y_D1 + ENTRE_DISQUES           # 74,4 : dessus du disque côté extérieur
Y_FACE = Y_D2 + EP_HAUT               # 81,4 : face extérieure du haut du bras (la platine du coude est dessus)
Y_S0, Y_S1 = YC - S_T / 2, YC + S_T / 2     # 19,8 et 67,6 : les deux faces du boîtier
DY = Y_FACE - E.Y_FACE                # tout ce qui est porté par la platine (coude, avant-bras, pince) est décalé d'autant : 26,1
Y_MILIEU_AVANT_BRAS = E.Y_MILIEU_AVANT_BRAS + DY

# ---------------- Le haut du bras ----------------
PW, R_BOUT = 33.0, 16.5               # largeur des plaques et rayon de leur bout rond autour de l'axe (disque : 14,8)
L_BRAS = E.L_BRAS                     # 120
ENT_A, ENT_A_L, ENT_B, ENT_B_L = 50.0, 12.0, 100.0, 15.0     # entretoises, comme sur l'ancien bras
VIS_ENT_Z = 9.0
L_VIS_ENT, PRISE_VIS_ENT = 30.0, 5.0  # vis M3 × 30 (les plus longues de Nicolas) ; 5 mm dans la moitié basse (insert de 3,8)
JEU_SERRAGE = 0.4
INSERT_D, INSERT_P = 4.0, 6.0         # perçage pour ses inserts M3 (Ø 4,7 × 3,8)
X_PLAT0, X_PLAT1, TROUS_PLATINE = E.X_PLAT0, E.X_PLAT1, E.TROUS_PLATINE
B_VIS = E.B_VIS

def trous_disque(m, y0, y1):
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        m -= cyl_y(CERCLE_TROUS / 2 * math.cos(a), CERCLE_TROUS / 2 * math.sin(a), y0 - 0.1, y1 + 0.1, D_VIS_DISQUE, 20)
    return m - cyl_y(0, 0, y0 - 0.1, y1 + 0.1, D_CENTRE, 48)

def bras_bas():
    """Moitié basse : côté mur, vissée sur le disque côté logo. Porte les inserts des entretoises."""
    y0, y1, yj = Y_BAS0, Y_D1, YC - JEU_SERRAGE / 2
    m = box(0, y0, -PW / 2, ENT_B + ENT_B_L, y1, PW / 2) + cyl_y(0, 0, y0, y1, 2 * R_BOUT, 96)
    m -= cyl_y(0, 0, y0 - 0.1, y1 - SOUS_TETE, D_DISQUE + 4.4, 64)                  # cuvette côté mur : 4 mm sous les têtes, têtes noyées
    m = trous_disque(m, y0, y1)
    for x, l in ((ENT_A, ENT_A_L), (ENT_B, ENT_B_L)):
        m += box(x, y1, -PW / 2, x + l, yj, PW / 2)
        for s in (1, -1): m -= cyl_y(x + l / 2, s * VIS_ENT_Z, yj - INSERT_P, yj + 0.1, INSERT_D, 24)
    return m

def bras_haut():
    """Moitié haute : côté extérieur, avec la platine du coude. Les 4 vis M3 × 30 des entretoises entrent par sa face, au fond de puits."""
    y0, y1, yj = Y_D2, Y_FACE, YC + JEU_SERRAGE / 2
    m = box(0, y0, -PW / 2, X_PLAT0 + 0.1, y1, PW / 2) + cyl_y(0, 0, y0, y1, 2 * R_BOUT, 96)
    m += box(X_PLAT0, y0, -E.B.base_W / 2, X_PLAT1, y1, E.B.base_W / 2)              # platine du berceau du coude
    m -= cyl_y(0, 0, y0 + SOUS_TETE, y1 + 0.1, D_DISQUE + 4.4, 64)                  # cuvette côté extérieur
    m = trous_disque(m, y0, y1)
    y_tete = (YC - JEU_SERRAGE / 2 - PRISE_VIS_ENT) + L_VIS_ENT                     # où s'appuie la tête d'une vis de 30
    for x, l in ((ENT_A, ENT_A_L), (ENT_B, ENT_B_L)):
        m += box(x, yj, -PW / 2, x + l, y0 + 0.1, PW / 2)
        for s in (1, -1):
            m -= cyl_y(x + l / 2, s * VIS_ENT_Z, yj - 0.1, y1 + 0.1, 3.4, 24)
            m -= cyl_y(x + l / 2, s * VIS_ENT_Z, y_tete, y1 + 0.1, 6.4, 32)         # puits de la tête
    m -= cyl_y(B_VIS, 0, y1 - INSERT_P, y1 + 0.1, INSERT_D, 24)                     # insert de la vis du ressort (facultatif)
    for x, z in TROUS_PLATINE:                                                      # 4 vis M3 × 10 du berceau du coude, par-dessous
        m -= cyl_y(x, z, y0 - 0.1, y1 + 0.1, 3.4, 24); m -= cyl_y(x, z, y0 - 0.1, y0 + 1.2, 6.2, 32)
    return m
Y_TETE_VIS_ENT = (YC - JEU_SERRAGE / 2 - PRISE_VIS_ENT) + L_VIS_ENT

# ---------------- Le servo (pour les contrôles et les dessins) ----------------
def servo():
    """Boîtier seul (fixe) : la partie que le berceau tient."""
    return box(S_AXE - S_L, Y_S0, -S_W / 2, S_AXE, Y_S1, S_W / 2)
def disques():
    """Les deux disques et leurs moyeux : ils tournent avec le bras."""
    return cyl_y(0, 0, Y_D1, Y_S0 + 0.01, D_DISQUE, 64) + cyl_y(0, 0, Y_S1 - 0.01, Y_D2, D_DISQUE, 64)

# ---------------- Le berceau ----------------
JEU = 0.2                             # autour du boîtier, de chaque côté
Z_FOND = -S_W / 2                     # le servo est posé sur le fond
Z_BAS = -30.0                         # dessous du berceau : tout descend jusque-là, pour imprimer debout sans support
X_AR, X_AV = S_AXE - S_L, S_AXE       # −47,1 et 17,9 : les deux bouts du boîtier
EP_MUR_AR, EP_LEVRE, H_LEVRE = 6.0, 3.0, 6.0
X_JOUE = -19.5                        # les joues s'arrêtent là : devant, c'est la place des disques et des plaques du bras
EP_JOUE_EXT = 8.0                     # joue extérieure : assez épaisse pour un insert M3 dans sa tranche
Z_APPUI = S_W / 2 - 0.3               # dessus des joues : 0,3 sous le dessus du servo, pour que la bride le serre
SOCLE_X, SOCLE_Z = (-58.0, 0.0), (Z_BAS, 23.0)
TROUS_MUR = [(-53.0, -25.0), (-53.0, 18.0), (-5.0, -25.0), (-24.0, 18.0)]     # 4 inserts M3 dans le socle, vis par-derrière le mur
BRIDE_X = (-45.0, -25.0); EP_BRIDE = 6.0; X_VIS_BRIDE = -35.0
Y_VIS_BRIDE = (12.0, Y_S1 + JEU + EP_JOUE_EXT / 2)
FENTE_PRISE = (-19.5, -1.0, Y_S1 - 8.5)   # échancrure du fond sous la prise SVG du dessous : de x = −19,5 à −1, à partir de y = 59,1

def berceau():
    """D'un seul bloc, imprimé debout (dessous à plat) sans support : socle contre le mur, joue côté mur (pleine jusqu'au socle),
    fond, mur arrière, joue extérieure, lèvre devant. Devant x = −19,5 il ne reste, entre le socle et le servo, qu'un talon bas :
    c'est là que passe la moitié basse du bras."""
    ya, yb = Y_S0 - JEU, Y_S1 + JEU                                                 # 19,6 et 67,8
    m = box(SOCLE_X[0], 0, SOCLE_Z[0], SOCLE_X[1], EP_SOCLE, SOCLE_Z[1])             # socle
    m += box(X_AR - JEU - EP_MUR_AR, EP_SOCLE, Z_BAS, X_JOUE, ya, Z_APPUI)           # joue côté mur (et dos du mur arrière)
    m += box(X_JOUE, EP_SOCLE, Z_BAS, -2.0, ya, -23.0)                               # talon bas sous le passage du bras
    m += box(X_AR - JEU - EP_MUR_AR, ya, Z_BAS, X_AV + JEU + EP_LEVRE, yb, Z_FOND)   # fond, sous tout le boîtier
    m += box(X_AR - JEU - EP_MUR_AR, ya, Z_BAS, X_AR - JEU, yb + EP_JOUE_EXT, Z_APPUI)      # mur arrière
    m += box(X_AR - JEU - EP_MUR_AR, yb, Z_BAS, X_JOUE, yb + EP_JOUE_EXT, Z_APPUI)   # joue extérieure
    m += box(X_AV + JEU, ya, Z_BAS, X_AV + JEU + EP_LEVRE, yb, Z_FOND + H_LEVRE)     # lèvre devant
    m -= box(FENTE_PRISE[0], FENTE_PRISE[2], Z_BAS - 1, FENTE_PRISE[1], yb + EP_JOUE_EXT + 1, Z_FOND + 1)   # prise SVG du dessous et son câble
    for ya_, yb_ in ((Y_D1 - 0.5, Y_S0 + 1.5), (Y_S1 - 1.5, Y_D2 + 0.5)):               # dégagement de 2 mm autour de chaque disque (ils frôlaient le fond)
        m -= cyl_y(0, 0, ya_, yb_, D_DISQUE + 4.0, 64)
    for x, z in TROUS_MUR: m -= cyl_y(x, z, -0.1, EP_SOCLE + 0.1, INSERT_D, 24)
    for y in Y_VIS_BRIDE: m -= cyl_z(X_VIS_BRIDE, y, Z_APPUI - INSERT_P, Z_APPUI + 0.1, INSERT_D, 24)
    return m

def bride():
    """Barre posée sur les deux joues, par-dessus le servo : 2 vis M3 × 10 dans les inserts des joues."""
    m = box(BRIDE_X[0], Y_VIS_BRIDE[0] - 6, S_W / 2, BRIDE_X[1], Y_VIS_BRIDE[1] + 6, S_W / 2 + EP_BRIDE)
    for y in Y_VIS_BRIDE: m -= cyl_z(X_VIS_BRIDE, y, S_W / 2 - 0.1, S_W / 2 + EP_BRIDE + 0.1, 3.4, 24)
    return m

# ---------------- Le bâti ----------------
H_AXE, EP_MUR, EP_PIED, R_COIN = E.H_AXE, E.EP_MUR, E.EP_PIED, E.R_COIN_PIED
DEC_PIED = 18.0                       # le pied est le même, mais posé 18 mm plus loin en Y : le mur est maintenant à son bord
PIED = (-95.0, 34.0, -24.0 + DEC_PIED, 86.0 + DEC_PIED)          # x0, x1, y0, y1 : −6 … 104
TROUS_PIED = [(x, y + DEC_PIED) for x in (-84.0, 22.0) for y in (-15.0, 78.0)]     # les 4 trous du plateau du socle, inchangés
AXE_SOCLE = (-31.0, 31.5 + DEC_PIED)  # axe de rotation du socle, au milieu des 4 trous : (−31 ; 49,5)
X_MUR = (-64.0, 6.0)                  # mur du berceau : il s'arrête avant le trou avant du pied
X_MUR_AR = -64.0
D_RESSORT = E.D_RESSORT
Y_RESSORT = Y_FACE + 2.0 + D_RESSORT / 2          # 89,4
Y_MAT = Y_RESSORT + D_RESSORT / 2 + 2.7           # 98,1 : face intérieure du mât
TROUS_RESSORT = E.TROUS_RESSORT

def bati():
    """Pied + mur du berceau + mur arrière + mât du ressort. Posé sur son pied à l'impression, sans support."""
    zp = -H_AXE; x0, x1, y0, y1 = PIED; r = R_COIN
    pied = box(x0 + r, y0, zp - EP_PIED, x1 - r, y1, zp) + box(x0, y0 + r, zp - EP_PIED, x1, y1 - r, zp)
    for cx in (x0 + r, x1 - r):
        for cy in (y0 + r, y1 - r): pied += mf.Manifold.cylinder(EP_PIED, r, r, 64).translate((cx, cy, zp - EP_PIED))
    mur = box(X_MUR[0], -EP_MUR, zp, X_MUR[1], 0, SOCLE_Z[1] + 3)
    arriere = box(X_MUR_AR - EP_MUR, -EP_MUR, zp, X_MUR_AR, Y_MAT + EP_MUR, 56)
    mat = prisme_xz([(X_MUR_AR, zp), (-40, zp), (-40, 6), (-28, 18), (-28, 56), (X_MUR_AR, 56)], Y_MAT, Y_MAT + EP_MUR)
    m = pied + mur + arriere + mat
    for ya, yb in ((0, 14), (Y_MAT - 14, Y_MAT)): m += prisme_xz([(X_MUR_AR, zp), (X_MUR_AR + 14, zp), (X_MUR_AR, zp + 14)], ya, yb)
    m += prisme_xz([(X_MUR[1], zp), (X_MUR[1] + 12, zp), (X_MUR[1], zp + 40)], -EP_MUR, 0)      # jambe de force devant le mur
    for x, z in TROUS_MUR: m -= cyl_y(x, z, -EP_MUR - 0.1, 0.1, 3.4, 24)
    for x, z in TROUS_RESSORT: m -= cyl_y(x, z, Y_MAT - 0.1, Y_MAT + EP_MUR + 0.1, 3.3, 24)
    for x, y in TROUS_PIED: m -= mf.Manifold.cylinder(EP_PIED + 0.2, 2.3, 2.3, 24).translate((x, y, zp - EP_PIED - 0.1))
    return m

BRAS_BAS, BRAS_HAUT, BERCEAU, BRIDE, BATI, SERVO, DISQUES = bras_bas(), bras_haut(), berceau(), bride(), bati(), servo(), disques()
# ce que porte la platine : pièces existantes, décalées de DY le long de l'axe
dec = lambda m: m.translate((0, DY, 0))
BERCEAU_COUDE, BRIDE_COUDE, SERVO_COUDE, AVANT_BRAS = dec(E.BERCEAU_COUDE), dec(E.BRIDE_COUDE), dec(E.SERVO_COUDE), dec(E.AVANT_BRAS)

def bras_complet(alpha, gamma=0.0, pince=None):
    p = {'bras bas': BRAS_BAS, 'bras haut': BRAS_HAUT, 'disques du servo': DISQUES, 'berceau du coude': BERCEAU_COUDE,
         'bride du coude': BRIDE_COUDE, 'servo du coude': SERVO_COUDE}
    av = AVANT_BRAS + (pince if pince is not None else mf.Manifold())
    p['avant-bras et pince'] = tourner_y(av, gamma).translate((L_BRAS, 0, 0))
    return {n: tourner_y(m, alpha) for n, m in p.items()}

if __name__ == '__main__':
    r = {'etat': 'PROTOTYPE : vérifié par le calcul, jamais imprimé ni monté', 'pieces': {}, 'controles': {}}
    v = lambda a, b: (a ^ b).volume()
    fixes = {'bâti': BATI, 'berceau': BERCEAU, 'bride': BRIDE, 'boîtier du servo': SERVO}
    # 1. le servo entre dans le berceau, par le haut, et il y est tenu dans les 6 directions
    assert v(SERVO, BERCEAU) < 0.01 and v(SERVO, BRIDE) < 0.01, 'le servo traverse le berceau ou la bride'
    assert v(DISQUES, BERCEAU) < 0.01 and v(DISQUES, BRIDE) < 0.01, 'un disque touche le berceau'
    for h in range(0, 61, 3):
        assert v((SERVO + DISQUES).translate((0, 0, h)), BERCEAU) < 0.01, f'le servo ne peut pas descendre dans le berceau (coince à {h} mm)'
    pousse = {'vers le bas': (0, 0, -0.5), 'vers l\'arrière': (-0.5, 0, 0), 'vers l\'avant': (0.5, 0, 0), 'vers le mur': (0, -0.5, 0), 'vers l\'extérieur': (0, 0.5, 0)}
    for nom, d in pousse.items(): assert v(SERVO.translate(d), BERCEAU) > 1.0, f'rien ne retient le servo {nom}'
    assert v(SERVO.translate((0, 0, 0.5)), BRIDE) > 1.0, 'la bride ne retient pas le servo vers le haut'
    r['controles']['servo dans le berceau'] = 'descend par le haut sans rien toucher ; tenu en bas, devant, derrière et des deux côtés par le berceau, en haut par la bride'
    # 2. les prises SVG restent libres : celle du dessus (à l'air) et celle du dessous (échancrure du fond)
    for nom, z0, z1 in (('du dessus', S_W / 2, S_W / 2 + 25), ('du dessous', Z_BAS - 5, -S_W / 2)):
        fiche = box(-PRISE_X[1] - 1, Y_S1 - 6.5, z0, -PRISE_X[0] + 1, Y_S1, z1)      # fiche + câble, contre la face opposée au logo
        for nf, mfix in fixes.items():
            if nf != 'boîtier du servo': assert v(fiche, mfix) < 0.01, f'la prise {nom} est bouchée par : {nf}'
    r['controles']['prises SVG'] = 'les deux restent libres (dessus à l\'air, dessous par l\'échancrure du fond) ; face OPPOSÉE au logo vers l\'extérieur'
    # 3. le bras tourne de −30° à +90° sans rien toucher (pièces fixes) ; jeu mini relevé
    def gest(m):
        c = tm.collision.CollisionManager(); c.add_object('p', mesh(m)); return c
    gf = {n: gest(m) for n, m in fixes.items()}; pire = {}
    for alpha in np.arange(E.ALPHA_MIN, E.ALPHA_MAX + 0.1, 5):
        p = bras_complet(float(alpha)); p.pop('avant-bras et pince')
        for n, m in p.items():
            g = gest(m)
            for nf, mfix in fixes.items():
                if n == 'disques du servo' and nf == 'boîtier du servo': continue
                d = float(g.min_distance_other(gf[nf])) if v(m, mfix) < 0.01 else -1.0
                if (n, nf) not in pire or d < pire[(n, nf)][0]: pire[(n, nf)] = (round(d, 2), float(alpha))
    for (a, b), (d, al) in pire.items(): assert d >= 1.5, f'{a} / {b} : {d} mm à {al}°'
    r['controles']['bras de −30° à +90°'] = {f'{a} / {b}': f'{d} mm à {al:.0f}°' for (a, b), (d, al) in sorted(pire.items(), key=lambda kv: kv[1][0])[:8]}
    # 4. avant-bras et pince grande ouverte, coude de −90° à +90° : ne touchent ni le bâti, ni le berceau, ni le haut du bras
    PINCE = dec(E.pince_ouverte()); contacts = []
    for alpha in range(int(E.ALPHA_MIN), int(E.ALPHA_MAX) + 1, 15):
        for gamma in range(-90, 91, 15):
            p = bras_complet(alpha, gamma, PINCE); av = p.pop('avant-bras et pince')
            for nf, mfix in fixes.items():
                if v(av, mfix) > 0.5: contacts.append(f'épaule {alpha}°, coude {gamma}° : {nf}')
            for n in ('bras bas', 'bras haut'):
                if v(av, p[n]) > 0.5: contacts.append(f'épaule {alpha}°, coude {gamma}° : {n}')
    assert not contacts, contacts[:6]
    r['controles']['avant-bras et pince ouverte'] = 'épaule −30…90°, coude −90…90° : aucun contact avec le bâti, le berceau ni le haut du bras'
    # 5. visserie : longueurs et prises
    prise_ent = (YC - JEU_SERRAGE / 2) - (Y_TETE_VIS_ENT - L_VIS_ENT)
    r['controles']['visserie'] = {'vis M3 × 30 des entretoises : puits de la tête (mm de profondeur)': round(Y_FACE - Y_TETE_VIS_ENT, 1),
                                  'vis M3 × 30 : prise dans la moitié basse (mm ; insert de 3,8)': round(prise_ent, 1),
                                  'vis Ø 2,6 × 9 des disques : plastique sous la tête (mm)': SOUS_TETE, 'pointe sous le disque (mm ; 3 de vide)': round(9 - SOUS_TETE - 3.8, 1),
                                  'vis M3 × 10 du berceau, par-derrière le mur (6 mm) : prise dans l\'insert (mm)': 10 - EP_MUR,
                                  'vis M3 × 10 de la bride (6 mm) : prise dans l\'insert (mm)': 10 - EP_BRIDE}
    assert Y_TETE_VIS_ENT - (YC + JEU_SERRAGE / 2) >= 5.0 and Y_FACE - Y_TETE_VIS_ENT >= 3.0, 'vis d\'entretoise : tête mal placée'
    # 6. cotes utiles aux programmes
    y_av = Y_MILIEU_AVANT_BRAS
    r['cotes'] = {'axe au-dessus du pied': H_AXE, 'entre les disques': ENTRE_DISQUES, 'milieu du servo (y)': YC, 'face extérieure du bras (y)': Y_FACE,
                  'milieu de l\'avant-bras (y)': round(y_av, 1), 'axe du socle (x, y)': AXE_SOCLE,
                  'DECALAGE_BRAS à mettre dans bras/geometrie.py (mm)': round(-(y_av - AXE_SOCLE[1]), 1), 'ancien DECALAGE_BRAS': -53.5,
                  'trous du mur (x, z)': TROUS_MUR, 'trous du pied (x, y)': TROUS_PIED}
    # 7. pièces à imprimer : fermées, d'un seul bloc, posées à plat, sans grand porte-à-faux
    Rx = lambda a: tm.transformations.rotation_matrix(a, (1, 0, 0))
    a_imprimer = [('epaule3095_bati', BATI, None), ('epaule3095_berceau', BERCEAU, None), ('epaule3095_bride', BRIDE, None),
                  ('epaule3095_bras_bas', BRAS_BAS, Rx(math.pi / 2)), ('epaule3095_bras_haut', BRAS_HAUT, Rx(-math.pi / 2))]
    for nom, m, R in a_imprimer:
        t = mesh(m)
        if R is not None: t.apply_transform(R)
        t.apply_translation(-t.bounds[0]); t.export(OUT / f'{nom}.stl')
        zc, nz = t.triangles_center[:, 2], t.face_normals[:, 2]
        pose = float(t.area_faces[(zc < 0.01) & (nz < -0.99)].sum()); pont = float(t.area_faces[(zc > 0.3) & (nz < -0.7)].sum())
        d = {'fermée': bool(t.is_watertight), 'blocs': len(t.split(only_watertight=False)), 'encombrement (mm)': [round(float(x), 1) for x in t.extents],
             'masse environ (g)': round(t.volume / 1000 * 0.98), 'surface sur le plateau (mm²)': round(pose), 'plafonds en pont (mm²)': round(pont)}
        r['pieces'][nom] = d
        assert d['fermée'] and d['blocs'] == 1 and pose > 40, (nom, d)
    json.dump(r, open(OUT / 'verification_epaule_3095.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False, indent=1))
