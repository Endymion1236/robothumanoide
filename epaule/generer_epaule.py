"""Épaule du bras de Câlin (STS3215 + ressort de traction) — V1, 14/11/2026. Prototype, aucune validation physique.

Principe : on reprend ce qui marche déjà au coude.
  - Le servo d'épaule est couché dans un BERCEAU identique à celui du coude (bras V1), vissé sur le mur du BÂTI.
  - Le HAUT DU BRAS est une fourche comme l'avant-bras (deux moitiés vissées sur les deux disques du servo),
    prolongée par une PLATINE où se visse le berceau du coude.
  - Un RESSORT de traction relie une vis du haut du bras (à 56 mm de l'axe) à l'un des 12 trous du MÂT du bâti.
Repère : origine sur l'axe de l'épaule, X vers l'avant, Z vers le haut, Y le long de l'axe (0 = face du mur
où se visse le berceau, positif vers l'extérieur). Angle de l'épaule : 0° = bras horizontal vers l'avant.

Lancer : python generer_epaule.py   → sortie/*.stl, sortie/verification_epaule.json
Il faut : pip install numpy trimesh manifold3d python-fcl"""
import math, json, ast, sys
from pathlib import Path
import numpy as np, trimesh as tm, manifold3d as mf

ICI = Path(__file__).resolve().parent; RACINE = ICI.parent
OUT = ICI / 'sortie'; OUT.mkdir(exist_ok=True)

def box(x0, y0, z0, x1, y1, z1): return mf.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))
def cyl_y(x, z, y0, y1, d, n=48):
    """Cylindre d'axe Y (le long de l'axe de l'épaule)."""
    return mf.Manifold.cylinder(y1 - y0, d / 2, d / 2, n).rotate((-90, 0, 0)).translate((x, y0, z))
def mesh(m):
    a = m.to_mesh(); return tm.Trimesh(vertices=a.vert_properties[:, :3], faces=a.tri_verts, process=True)
def placer(m, R, t): return m.transform([[*R[0], t[0]], [*R[1], t[1]], [*R[2], t[2]]])
def tourner_y(m, angle, centre=(0.0, 0.0)):
    """Tourne autour d'un axe parallèle à Y passant par (x, z) = centre ; angle positif = vers le haut."""
    return m.translate((-centre[0], 0, -centre[1])).rotate((0, -angle, 0)).translate((centre[0], 0, centre[1]))
def prisme_xz(points, y0, y1):
    """Extrude un contour (x, z) le long de Y."""
    pts = [(x, -z) for x, z in points]
    aire = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    cs = mf.CrossSection([pts if aire > 0 else pts[::-1]])
    return mf.Manifold.extrude(cs, y1 - y0).rotate((-90, 0, 0)).translate((0, y0, 0))

# ---------------- Paramètres repris du coude (mêmes tableaux que les scripts Fusion) ----------------
def lire_specs(fichier, nom):
    arbre = ast.parse(Path(fichier).read_text(encoding='utf-8-sig'))
    specs = next(ast.literal_eval(n.value) for n in ast.walk(arbre) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == nom for t in n.targets))
    p = {}
    for n, e in specs: p[n] = eval(e.replace(' mm', ''), {'__builtins__': {}}, p)
    return type('P', (), p)
F = lire_specs(RACINE / 'coude-sts3215' / 'CoudeV1_2' / 'CoudeV1_2.py', 'SPECS')      # fourche du coude V1.2 (validée ± 90°)
# le berceau : on exécute seulement la fonction build() de verify_bras.py (pas ses exports)
_src = (RACINE / 'coude-sts3215' / 'BrasV1' / 'verify_bras.py').read_text(encoding='utf-8')
_ns = {'__file__': str(RACINE / 'coude-sts3215' / 'BrasV1' / 'verify_bras.py')}
exec(_src[:_src.index('p,b,brace,servo,cable=build()')], _ns)
# berceau « à inserts » : les 4 trous de fixation passent de 4,5 à 4,0 mm pour recevoir des inserts M3. Les vis
# viennent par-derrière : aucune tête de vis sur le socle, donc rien sous la fourche qui passe 2 mm au-dessus.
B, BERCEAU_C, BRIDE_C, SERVO_C, CABLE_C = _ns['build']({'mount_D': '4.0 mm'})
B = type('P', (), B)

# ---------------- Cotes de l'épaule ----------------
H_AXE = 95.0                    # hauteur de l'axe au-dessus du pied du bâti
EP_MUR, EP_PIED = 6.0, 6.0
Y_FOURCHE = B.base_T + 2.0      # la fourche passe 2 mm au-dessus du socle du berceau (comme au coude) : 7
EP_HAUT = 7.0                   # plaque haute du bras, platine comprise (4 au coude) : une seule face plane pour l'impression
Y_PL_HAUT = Y_FOURCHE + F.z_haut                 # dessous de la plaque haute : 48,3
Y_FACE = Y_PL_HAUT + EP_HAUT                     # face extérieure du haut du bras : 55,3
L_BRAS = 120.0                  # axe d'épaule → axe du coude
ENT_A, ENT_A_L = F.entretoise_A_X, F.entretoise_A_L      # entretoise A : 50 à 62 (dégage le servo, comme au coude)
ENT_B, ENT_B_L = 100.0, 15.0    # entretoise B : 100 à 115
VIS_ENT_Z = 7.5                 # vis M3 x 30 des entretoises, de part et d'autre de l'axe du bras
B_VIS = 56.0                    # vis d'accroche du ressort sur le bras
AXE_BERCEAU = B.sx + B.cyl_offset                # axe du servo dans son berceau : à 25,5 du bout du socle
X_PLAT0, X_PLAT1 = 62.0, L_BRAS + AXE_BERCEAU + 2.0      # platine du coude : de 62 à 147,5
TROUS_PLATINE = [(L_BRAS + AXE_BERCEAU - x, s * (B.base_W / 2 - B.mount_offset)) for x in (B.mount_offset, B.base_L - B.mount_offset) for s in (1, -1)]
TROUS_MUR = [(AXE_BERCEAU - x, s * (B.base_W / 2 - B.mount_offset)) for x in (B.mount_offset, B.base_L - B.mount_offset) for s in (1, -1)]
D_RESSORT = 12.0                # place réservée au ressort (Ø 10 conseillé, 12 possible)
Y_RESSORT = Y_FACE + 2.0 + D_RESSORT / 2         # milieu du ressort : 63,3
Y_MAT = Y_RESSORT + D_RESSORT / 2 + 2.7          # face intérieure du mât : 72
TROUS_RESSORT = [(x, z) for x in (-46.0, -40.0, -34.0) for z in (32.0, 38.0, 44.0, 50.0)]
X_MUR_AR = -62.0                # le mur arrière commence 7,5 mm derrière le berceau
ALPHA_MIN, ALPHA_MAX = -30.0, 90.0

# ---------------- Le haut du bras (fourche + platine), bras à l'horizontale ----------------
def bras_bas():
    """Moitié basse : contre le mur, vissée sur le disque libre du servo. Porte les inserts des entretoises."""
    y0 = Y_FOURCHE
    m = box(0, y0, -F.plaque_W / 2, ENT_B + ENT_B_L, y0 + F.plaque_T, F.plaque_W / 2) + cyl_y(0, 0, y0, y0 + F.plaque_T, 2 * F.bout_R, 96)
    for x, l in ((ENT_A, ENT_A_L), (ENT_B, ENT_B_L)):
        m += box(x, y0 + F.plaque_T, -F.plaque_W / 2, x + l, y0 + F.plaque_T + F.demi_H, F.plaque_W / 2)
        for s in (1, -1): m -= cyl_y(x + l / 2, s * VIS_ENT_Z, y0 + F.plaque_T + F.demi_H - F.insert_P, y0 + F.plaque_T + F.demi_H + 0.1, F.insert_D, 24)
    for sx in (1, -1):
        for sz in (1, -1):
            m -= cyl_y(sx * F.trou_d, sz * F.trou_d, y0 - 0.1, y0 + F.plaque_T + 0.1, F.vis_disque_D, 24)
            m -= cyl_y(sx * F.trou_d, sz * F.trou_d, y0 - 0.1, y0 + F.lamage_P, F.lamage_D, 24)
    return m - cyl_y(0, 0, y0 - 0.1, y0 + F.plaque_T + 0.1, F.centre_D, 32)

def bras_haut():
    """Moitié haute : côté palonnier. Plaque de 7 mm, platine du coude, insert de la vis du ressort."""
    y0, y1 = Y_PL_HAUT, Y_FACE
    m = box(0, y0, -F.plaque_W / 2, X_PLAT0 + 0.1, y1, F.plaque_W / 2) + cyl_y(0, 0, y0, y1, 2 * F.bout_R, 96)
    m += cyl_y(0, 0, y0 - F.surelev, y0, 2 * F.patin_R, 64)                                   # patin : seul en appui sur le palonnier
    m += box(X_PLAT0, y0, -B.base_W / 2, X_PLAT1, y1, B.base_W / 2)                           # platine du berceau du coude
    yb = Y_FOURCHE + F.plaque_T + F.demi_H + F.jeu_serrage
    for x, l in ((ENT_A, ENT_A_L), (ENT_B, ENT_B_L)):
        m += box(x, yb, -F.plaque_W / 2, x + l, y0 + 0.1, F.plaque_W / 2)
        for s in (1, -1):
            m -= cyl_y(x + l / 2, s * VIS_ENT_Z, yb - 0.1, y1 + 0.1, F.vis_M3_D, 24)
            m -= cyl_y(x + l / 2, s * VIS_ENT_Z, y1 - 3.0, y1 + 0.1, 6.2, 32)                  # têtes noyées : rien ne dépasse de la face
    prof_lamage = EP_HAUT - (F.plaque_T - F.lamage_P)                                          # même épaisseur sous les têtes M2,5 qu'au coude
    for sx in (1, -1):
        for sz in (1, -1):
            m -= cyl_y(sx * F.trou_d, sz * F.trou_d, y0 - F.surelev - 0.1, y1 + 0.1, F.vis_disque_D, 24)
            m -= cyl_y(sx * F.trou_d, sz * F.trou_d, y1 - prof_lamage, y1 + 0.1, F.lamage_D, 24)
    m -= cyl_y(0, 0, y0 - F.surelev - 0.1, y1 + 0.1, F.centre_D, 32)
    m -= cyl_y(B_VIS, 0, y1 - F.insert_P, y1 + 0.1, F.insert_D, 24)                            # insert M3 de la vis du ressort
    for x, z in TROUS_PLATINE:                                                                 # 4 vis M3 x 10 du berceau du coude, par-dessous
        m -= cyl_y(x, z, y0 - 0.1, y1 + 0.1, 3.4, 24)
        m -= cyl_y(x, z, y0 - 0.1, y0 + 1.2, 6.2, 32)
    return m

# ---------------- Berceau, servo, fourche de l'avant-bras : pièces existantes, placées dans le repère de l'épaule ----------------
R_BERCEAU = [[-1, 0, 0], [0, 0, 1], [0, 1, 0]]          # berceau couché : son socle contre le mur, le servo vers l'arrière
def berceau_sur_mur(m): return placer(m, R_BERCEAU, (AXE_BERCEAU, 0, -B.base_W / 2))
def berceau_sur_platine(m): return placer(m, R_BERCEAU, (L_BRAS + AXE_BERCEAU, Y_FACE, -B.base_W / 2))

def fourche_avant_bras():
    """Avant-bras V1.2 (les deux moitiés d'un bloc, pour les contrôles), axe du coude à l'origine, vers +X."""
    g = F; m = mf.Manifold()
    for haut in (True, False):
        zp = g.z_haut if haut else 0
        d = box(0, zp, -g.plaque_W / 2, g.avant_bras_L, zp + g.plaque_T, g.plaque_W / 2) + cyl_y(0, 0, zp, zp + g.plaque_T, 2 * g.bout_R)
        zb = g.plaque_T + g.demi_H + g.jeu_serrage if haut else g.plaque_T
        for x, l in ((g.entretoise_A_X, g.entretoise_A_L), (g.ent_B_X, g.entretoise_B_L)): d += box(x, zb, -g.plaque_W / 2, x + l, zb + g.demi_H, g.plaque_W / 2)
        m += d
    return m
Y_AVANT_BRAS = Y_FACE + B.base_T + 2.0                   # dessous de la fourche de l'avant-bras : 62,3
Y_MILIEU_AVANT_BRAS = Y_AVANT_BRAS + (F.z_haut + F.plaque_T) / 2

def pince_ouverte():
    """Pince V3 grande ouverte (le cas le plus encombrant), dans le repère de l'avant-bras (axe du coude à l'origine)."""
    sys.path.insert(0, str(RACINE / 'pince'))
    import generer_pince as P
    m = P.BASE + P.BRIDE + P.SERVO
    for piece in P.pose(P.TH_OUVERT).values(): m += piece
    return m.translate((F.avant_bras_L - P.XF, Y_MILIEU_AVANT_BRAS, -P.ZC))

# ---------------- Le bâti ----------------
def bati():
    """Pied + mur du berceau + mur arrière + mât du ressort, d'un seul bloc. S'imprime posé sur son pied, sans support."""
    zp = -H_AXE
    pied = box(-95, -24, zp - EP_PIED, 34, Y_MAT + EP_MUR + 8, zp)
    mur = box(X_MUR_AR, -EP_MUR, zp, 30, 0, 36)                                                # mur du berceau
    arriere = box(X_MUR_AR - EP_MUR, -EP_MUR, zp, X_MUR_AR, Y_MAT + EP_MUR, 56)                # mur arrière : relie le mur et le mât
    # mât : jusqu'à x = -40 sur toute la hauteur (le servo s'enfile devant), drapeau jusqu'à -28 au-dessus, dessous en pente à 45°
    mat = prisme_xz([(X_MUR_AR, zp), (-40, zp), (-40, 6), (-28, 18), (-28, 56), (X_MUR_AR, 56)], Y_MAT, Y_MAT + EP_MUR)
    m = pied + mur + arriere + mat
    # renforts à 45° dans les deux angles avec le mur arrière (ils raidissent le mur du berceau et le mât)
    for y0, y1 in ((0, 14), (Y_MAT - 14, Y_MAT)):
        m += prisme_xz([(X_MUR_AR, zp), (X_MUR_AR + 14, zp), (X_MUR_AR, zp + 14)], y0, y1)
    for (x, z) in TROUS_MUR: m -= cyl_y(x, z, -EP_MUR - 0.1, 0.1, 3.4, 24)                     # 4 vis M3 x 10 du berceau, par-derrière
    for (x, z) in TROUS_RESSORT: m -= cyl_y(x, z, Y_MAT - 0.1, Y_MAT + EP_MUR + 0.1, 3.3, 24)  # 12 trous d'accroche du ressort
    for x, y in ((-84, -15), (-84, Y_MAT + EP_MUR), (22, -15), (22, Y_MAT + EP_MUR)):          # 4 trous pour visser le pied sur une planche (hors des murs)
        m -= mf.Manifold.cylinder(EP_PIED + 0.2, 2.3, 2.3, 24).translate((x, y, zp - EP_PIED - 0.1))
    return m

BRAS_BAS, BRAS_HAUT, BATI = bras_bas(), bras_haut(), bati()
BERCEAU_E, BRIDE_E, SERVO_E = berceau_sur_mur(BERCEAU_C), berceau_sur_mur(BRIDE_C), berceau_sur_mur(SERVO_C)
BERCEAU_COUDE, BRIDE_COUDE, SERVO_COUDE = berceau_sur_platine(BERCEAU_C), berceau_sur_platine(BRIDE_C), berceau_sur_platine(SERVO_C)
AVANT_BRAS = fourche_avant_bras().translate((0, Y_AVANT_BRAS, 0))

def bras_complet(alpha, gamma=0.0, avec_pince=True):
    """Tout ce qui bouge avec l'épaule, pour un angle d'épaule alpha et un angle de coude gamma (degrés)."""
    p = {'bras bas': BRAS_BAS, 'bras haut': BRAS_HAUT, 'berceau du coude': BERCEAU_COUDE, 'bride du coude': BRIDE_COUDE, 'servo du coude': SERVO_COUDE}
    av = AVANT_BRAS + (PINCE if avec_pince else mf.Manifold())
    p['avant-bras et pince'] = tourner_y(av, gamma).translate((L_BRAS, 0, 0))
    return {n: tourner_y(m, alpha) for n, m in p.items()}

def ressort(alpha, trou, d=D_RESSORT):
    """Le ressort tendu entre son trou du mât et la vis du bras : un cylindre, pour les contrôles."""
    a = np.array([trou[0], Y_RESSORT, trou[1]]); r = math.radians(alpha)
    b = np.array([B_VIS * math.cos(r), Y_RESSORT, B_VIS * math.sin(r)]); v = b - a; l = float(np.linalg.norm(v))
    ang = math.degrees(math.atan2(v[2], v[0]))
    c = mf.Manifold.cylinder(max(l - 12, 1), d / 2, d / 2, 32).rotate((0, 90, 0)).translate((6, 0, 0))     # 6 mm de crochet à chaque bout
    return tourner_y(c, ang).translate(tuple(a)), l

PINCE = None
if __name__ == '__main__':
    PINCE = pince_ouverte()
    fixes = {'bâti': BATI, 'berceau de l\'épaule': BERCEAU_E, 'bride de l\'épaule': BRIDE_E, 'servo de l\'épaule': SERVO_E}
    rapport = {'version': 'épaule V1', 'validation_physique': False, 'pieces': {}, 'cotes': {}}
    # 1. pièces à imprimer : fermées, d'un seul bloc, posées à plat
    R_PLAT = tm.transformations.rotation_matrix(math.pi / 2, (1, 0, 0))          # Y (axe de l'épaule) vers le haut du plateau
    a_imprimer = [('epaule_bati', BATI, None), ('epaule_bras_bas', BRAS_BAS, R_PLAT),
                  ('epaule_bras_haut', BRAS_HAUT, tm.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0))),
                  ('berceau_a_inserts', BERCEAU_C, None), ('bride_berceau', BRIDE_C, tm.transformations.rotation_matrix(math.pi, (1, 0, 0)))]
    for nom, m, R in a_imprimer:
        t = mesh(m)
        if R is not None: t.apply_transform(R)
        t.apply_translation(-t.bounds[0]); t.export(OUT / f'{nom}.stl')
        zc, nz = t.triangles_center[:, 2], t.face_normals[:, 2]
        pose = float(t.area_faces[(zc < 0.01) & (nz < -0.99)].sum()); pont = float(t.area_faces[(zc > 0.3) & (nz < -0.7)].sum())
        d = {'fermee': bool(t.is_watertight), 'blocs': len(t.split(only_watertight=False)), 'encombrement_mm': [round(float(v), 1) for v in t.extents],
             'masse_g_environ': round(t.volume / 1000 * 0.98), 'surface_sur_le_plateau_mm2': round(pose), 'plafonds_en_pont_mm2': round(pont)}
        rapport['pieces'][nom] = d
        assert d['fermee'] and d['blocs'] == 1 and pose > 40, (nom, d)
    rapport['cotes'] = {'axe_au_dessus_du_pied': H_AXE, 'face_exterieure_du_bras_y': Y_FACE, 'milieu_du_ressort_y': Y_RESSORT, 'face_interieure_du_mat_y': Y_MAT,
                        'milieu_de_l_avant_bras_y': Y_MILIEU_AVANT_BRAS, 'trous_du_mur': TROUS_MUR, 'trous_de_la_platine': TROUS_PLATINE, 'trous_du_ressort': TROUS_RESSORT}
    json.dump(rapport, open(OUT / 'verification_epaule.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(rapport['pieces'], ensure_ascii=False, indent=1))
