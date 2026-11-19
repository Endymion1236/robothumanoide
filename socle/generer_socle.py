"""Socle tournant du bras (servo n° 1) — V1, 17/11/2026. Prototype : aucune validation physique.

De bas en haut (Z vers le haut, table à z = 0, axe de rotation = axe Z) :
  BASE      serrée sur la table ; le servo y est debout, palonnier en haut ; 4 poteaux à inserts.
  PALIER    plaque vissée sur les poteaux : elle appuie sur le servo (comme une bride) et porte un tube
            où logent les 2 roulements 6807 (47 × 35 × 6,8 mesurés), séparés par une ENTRETOISE.
  PLATEAU   plaque de la taille du pied du bâti + moyeu creux (Ø 34,9) qui descend dans les 2 roulements
            et se visse sur le palonnier (4 vis M2,5 par le creux du moyeu).
Le servo ne fait que tourner et porter le poids (moins d'1 kg) ; les 2 roulements, écartés de 20 mm,
reprennent le basculement du bras tendu. Le bâti se visse sur le plateau par les 4 trous de son pied.
Lancer : python generer_socle.py → sortie/*.stl, sortie/verification_socle.json"""
import math, json
from pathlib import Path
import numpy as np, manifold3d as mf, trimesh as tm
OUT = Path(__file__).resolve().parent / 'sortie'; OUT.mkdir(exist_ok=True)

# ---------------- Mesures (servo du 08/11/2026, roulements du 16/11/2026, pied du bâti) ----------------
SL, SW = 45.2, 24.4; H_BAS, H_HAUT = 28.8, 33.0; HAUT_DEBUT, HAUT_ARC = 15.6, 10.0
AXE_BOUT = 8.1; PAL_D, PAL_H = 19.7, 4.3; CERCLE_TROUS = 13.45
BOSS_L, BOSS_W, BOSS_BORD, RELIEF = 11.9, 18.3, 5.0, 2.0
ROUL_DE, ROUL_DI, ROUL_EP = 47.0, 35.0, 6.8
PIED_X0, PIED_X1, PIED_Y0, PIED_Y1, PIED_R = -95.0, 34.0, -24.0, 86.0, 12.0     # pied du bâti, repère de l'épaule
TROUS_PIED = [(-84.0, -15.0), (-84.0, 78.0), (22.0, -15.0), (22.0, 78.0)]
# ---------------- Choix ----------------
JEU = 0.2; M3, INSERT, M2_5 = 3.4, 4.0, 2.9
AXE_DANS_PIED = (0.0, 31.5)        # l'axe de rotation passe sous l'axe de l'épaule (x = 0), au milieu des 4 trous en y
EP_SOL = 5.0; Z_SERVO = EP_SOL + RELIEF                      # dessous du servo : 7
Z_HAUT = Z_SERVO + H_HAUT; Z_PAL = Z_SERVO + H_BAS + PAL_H   # dessus de la partie haute : 40 ; dessus du palonnier : 40,1
MUR = 3.0; SERRAGE = 0.5                                     # les murs s'arrêtent 0,5 sous le dessus du servo
EP_PLAQUE, LEVRE = 4.0, 2.0                                  # plaque du palier ; lèvre sous le roulement du bas
ECART = 20.0                                                 # entre les milieux des 2 roulements
Z_RA = Z_HAUT + LEVRE; Z_RB = Z_RA + ECART; Z_TUBE = Z_RB + ROUL_EP + 0.2
TUBE_DE = 55.0; MOYEU_DE, MOYEU_DI = ROUL_DI - 0.1, 19.0     # creux de 19 : passage du tournevis, pont plus court à l'impression
PEAU = 0.4                                                   # peau pleine au fond du creux : le pont s'imprime sans trou, on la perce ensuite
PATIN, VOILE = 1.0, 1.5        # 2,5 mm de plastique sous les têtes : une vis M2,5 x 5 (celles du servo) entre de 2,5 mm dans le palonnier (2,4 jusqu'au 19/11/2026 : 1,6 mm de prise seulement)
_ANCIEN = 1.0, 2.4                                      # sous le moyeu : patin Ø 18 sur le palonnier + voile
Z_PLATEAU = Z_TUBE + 1.0; EP_PLATEAU = 8.0
POTEAUX = [(-42.0, 28.0), (-42.0, -28.0), (26.0, 28.0), (26.0, -28.0)]
X0S = AXE_BOUT - SL                                          # arrière du servo : -37,1

def box(x0, y0, z0, x1, y1, z1): return mf.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))
def cyl(x, y, z0, z1, d, n=64): return mf.Manifold.cylinder(z1 - z0, d / 2, d / 2, n).translate((x, y, z0))
def anneau(z0, z1, de, di, n=96): return cyl(0, 0, z0, z1, de, n) - cyl(0, 0, z0 - 0.1, z1 + 0.1, di, n)
def arrondi(x0, y0, x1, y1, r, z0, z1):
    m = box(x0 + r, y0, z0, x1 - r, y1, z1) + box(x0, y0 + r, z0, x1, y1 - r, z1)
    for cx in (x0 + r, x1 - r):
        for cy in (y0 + r, y1 - r): m += cyl(cx, cy, z0, z1, 2 * r)
    return m
def mesh(m):
    g = m.to_mesh(); return tm.Trimesh(vertices=np.asarray(g.vert_properties)[:, :3], faces=np.asarray(g.tri_verts), process=True)

def servo_ref():
    s = box(X0S, -SW / 2, Z_SERVO, AXE_BOUT, SW / 2, Z_SERVO + H_BAS)
    s += box(X0S, -SW / 2, Z_SERVO + H_BAS, AXE_BOUT - HAUT_DEBUT, SW / 2, Z_HAUT) - cyl(0, 0, Z_SERVO + H_BAS - 0.1, Z_HAUT + 0.1, 2 * HAUT_ARC)
    s += cyl(0, 0, Z_SERVO + H_BAS, Z_PAL, PAL_D)
    s += box(AXE_BOUT - BOSS_BORD - BOSS_L, -BOSS_W / 2, Z_SERVO - RELIEF, AXE_BOUT - BOSS_BORD, BOSS_W / 2, Z_SERVO) + cyl(0, 0, Z_SERVO - RELIEF, Z_SERVO, 5.5)
    return s

def base():
    """Sol + logement du servo + 4 poteaux à inserts reliés au logement par des nervures."""
    b = arrondi(-62, -52, 48, 52, 10, 0, EP_SOL)
    zt = Z_HAUT - SERRAGE
    b += box(X0S - JEU - MUR, -SW / 2 - JEU - MUR, EP_SOL, AXE_BOUT + JEU + MUR, SW / 2 + JEU + MUR, zt)
    b -= box(X0S - JEU, -SW / 2 - JEU, EP_SOL - 0.01, AXE_BOUT + JEU, SW / 2 + JEU, zt + 0.1)
    for y0, y1 in ((-SW / 2 - JEU, -SW / 2 + 2), (SW / 2 - 2, SW / 2 + JEU)):                    # rails sous les bords du servo
        b += box(X0S - JEU, y0, EP_SOL, AXE_BOUT + JEU, y1, Z_SERVO)
    b -= box(X0S + 17, -SW / 2 - JEU - MUR - 1, Z_SERVO - 1, X0S + 29, SW / 2 + JEU + MUR + 1, Z_SERVO + 14)   # fenêtres du câble, des 2 côtés
    for x, y in POTEAUX:
        xm = min(max(x, X0S - JEU - MUR + 1.5), AXE_BOUT + JEU + MUR - 1.5); ym = math.copysign(SW / 2 + JEU + MUR - 1.5, y)
        b += cyl(x, y, EP_SOL, zt, 10)
        b += mf.Manifold.batch_hull([cyl(x, y, EP_SOL, zt, 5, 24), cyl(xm, ym, EP_SOL, zt, 3, 24)])
        b -= cyl(x, y, zt - 8, zt + 0.1, INSERT, 24)
    b -= box(X0S + 17, -SW / 2 - JEU - MUR - 1, Z_SERVO - 1, X0S + 29, SW / 2 + JEU + MUR + 1, Z_SERVO + 14)
    b -= cyl(0, 0, Z_SERVO + H_BAS - 0.5, zt + 1, PAL_D + 2.0)        # le palonnier (Ø 19,7) déborde de 1,75 mm du bout du servo : mur abaissé dessous
    for x, y in ((-54, -44), (-54, 44), (40, -44), (40, 44)): b -= cyl(x, y, -0.1, EP_SOL + 0.1, 4.6, 24)        # 4 trous pour vis à bois
    return b

def palier():
    """Plaque posée sur le servo (0,5 mm de serrage sur les poteaux) + tube des 2 roulements."""
    p = arrondi(-49, -35, 33, 35, 6, Z_HAUT, Z_HAUT + EP_PLAQUE) + cyl(0, 0, Z_HAUT, Z_TUBE, TUBE_DE, 128)
    p -= cyl(0, 0, Z_HAUT - 0.1, Z_RA, 42.0, 96)                                 # lèvre : le roulement du bas repose dessus
    p -= cyl(0, 0, Z_RA, Z_TUBE + 0.1, ROUL_DE + 0.1, 128)                       # logement des 2 roulements et de l'entretoise
    for x, y in POTEAUX: p -= cyl(x, y, Z_HAUT - 0.1, Z_HAUT + EP_PLAQUE + 0.1, M3, 24)
    return p

def entretoise(): return anneau(Z_RA + ROUL_EP + 0.05, Z_RB - 0.05, ROUL_DE - 0.3, 42.0)
def roulements(): return anneau(Z_RA, Z_RA + ROUL_EP, ROUL_DE, ROUL_DI) + anneau(Z_RB, Z_RB + ROUL_EP, ROUL_DE, ROUL_DI)

def plateau():
    """Plaque (contour du pied du bâti) + moyeu creux vissé sur le palonnier. S'imprime retourné, plaque sur le plateau."""
    ax, ay = AXE_DANS_PIED
    m = arrondi(PIED_X0 - ax, PIED_Y0 - ay, PIED_X1 - ax, PIED_Y1 - ay, PIED_R, Z_PLATEAU, Z_PLATEAU + EP_PLATEAU)
    m += cyl(0, 0, Z_PAL + PATIN, Z_PLATEAU, MOYEU_DE, 128) + cyl(0, 0, Z_PAL, Z_PAL + PATIN, 18.0)
    m -= cyl(0, 0, Z_PAL + PATIN + VOILE, Z_PLATEAU + EP_PLATEAU + 0.1, MOYEU_DI, 96)          # creux : passage du tournevis
    for k in range(4):
        a = math.radians(45 + 90 * k); m -= cyl(CERCLE_TROUS / 2 * math.cos(a), CERCLE_TROUS / 2 * math.sin(a), Z_PAL - 0.1, Z_PAL + PATIN + VOILE - PEAU, M2_5, 24)
    m -= cyl(0, 0, Z_PAL - 0.1, Z_PAL + PATIN + VOILE - PEAU, 7.0, 32)                           # vis centrale du palonnier (trou borgne : la peau reste)
    for x, y in TROUS_PIED: m -= cyl(x - ax, y - ay, Z_PLATEAU - 0.1, Z_PLATEAU + EP_PLATEAU + 0.1, INSERT, 24)   # 4 inserts M3 : le bâti se visse dessus
    return m

SERVO, BASE, PALIER, ENTRETOISE, ROULEMENTS, PLATEAU = servo_ref(), base(), palier(), entretoise(), roulements(), plateau()
def tourner(m, deg): return m.rotate((0, 0, deg))

if __name__ == '__main__':
    r = {'version': 'socle V1', 'validation_physique': False, 'hauteurs_mm': {}, 'pieces': {}, 'contacts_mm3': {}, 'vis': {}}
    r['hauteurs_mm'] = {'dessus du servo (partie haute)': Z_HAUT, 'dessus du palonnier': round(Z_PAL, 1), 'roulement du bas': [Z_RA, Z_RA + ROUL_EP],
                        'roulement du haut': [Z_RB, round(Z_RB + ROUL_EP, 1)], 'dessus du plateau (le pied du bâti se pose là)': Z_PLATEAU + EP_PLATEAU,
                        'axe de l\'épaule au-dessus de la table': Z_PLATEAU + EP_PLATEAU + 6 + 95}
    # 1. rien ne se touche, sauf les appuis voulus ; plateau tourné de -90 à +90°
    paires = [('base / servo', BASE, SERVO), ('palier / base', PALIER, BASE), ('palier / roulements', PALIER, ROULEMENTS), ('entretoise / roulements', ENTRETOISE, ROULEMENTS),
              ('entretoise / palier', ENTRETOISE, PALIER)]
    for nom, a, b in paires:
        v = (a ^ b).volume(); r['contacts_mm3'][nom] = round(v, 2); assert v < 0.01, (nom, v)
    r['contacts_mm3']['palier / servo (appui voulu, sans pénétration)'] = round((PALIER ^ SERVO).volume(), 2)
    pire = 0.0
    for deg in range(-90, 91, 15):
        pl = tourner(PLATEAU, deg)
        for nom, f in (('base', BASE), ('palier', PALIER), ('entretoise', ENTRETOISE), ('roulements', ROULEMENTS), ('servo', SERVO)):
            v = (pl ^ f).volume(); pire = max(pire, v); assert v < 0.01, (deg, nom, v)
    r['contacts_mm3']['plateau tourné de -90 à +90° contre tout le reste'] = round(pire, 2)
    # 2. jeux et vis
    r['vis'] = {'M2,5 du palonnier : plastique traversé (mm)': PATIN + VOILE, 'vis M2,5 x 5 : prise dans le palonnier (mm)': 5 - PATIN - VOILE, 'M3 × 10 du palier : prise dans l\'insert (mm)': 10 - EP_PLAQUE,
                'M3 × 12 du pied du bâti (6 mm) : prise dans l\'insert du plateau (mm)': 12 - 6,
                'jeu du moyeu dans les roulements (mm, au diamètre)': round(ROUL_DI - MOYEU_DE, 2), 'jeu des roulements dans le tube (mm, au diamètre)': 0.1,
                'jour plaque du palier / poteaux avant serrage (mm)': SERRAGE, 'jour plateau / tube (mm)': Z_PLATEAU - Z_TUBE}
    # 3. export, pièces orientées pour l'impression
    R180 = tm.transformations.rotation_matrix(math.pi, (1, 0, 0))
    for nom, m, R in (('socle_base', BASE, None), ('socle_palier', PALIER, None), ('socle_entretoise', ENTRETOISE, None), ('socle_plateau', PLATEAU, R180)):
        t = mesh(m)
        if R is not None: t.apply_transform(R)
        t.apply_translation(-t.bounds[0]); t.export(OUT / f'{nom}.stl')
        d = {'fermee': bool(t.is_watertight), 'blocs': len(t.split(only_watertight=False)), 'encombrement_mm': [round(float(v), 1) for v in t.extents],
             'masse_g_environ': round(t.volume / 1000 * 0.98)}
        r['pieces'][nom] = d; assert d['fermee'] and d['blocs'] == 1, (nom, d)
    # pièce d'essai : une bague au diamètre du moyeu (34,9), pour vérifier l'ajustement dans un roulement avant d'imprimer le plateau
    t = mesh(anneau(0, 12, MOYEU_DE, MOYEU_DI)); t.export(OUT / 'socle_essai_moyeu.stl')
    # trois bagues d'essai d'un coup : 34,8 (basse, 6 mm), 34,7 (moyenne, 9 mm), 34,6 (haute, 12 mm), reliées par une languette
    essai = mf.Manifold()
    for k, (d, h) in enumerate(((34.8, 6.0), (34.7, 9.0), (34.6, 12.0))):
        essai += (cyl(0, 0, 0, h, d, 128) - cyl(0, 0, -0.1, h + 0.1, MOYEU_DI, 64)).translate((k * 38.0, 0, 0))
    essai += box(0, -3, 0, 76, 3, 1.2) - cyl(0, 0, -0.1, 2, MOYEU_DI, 64) - cyl(38, 0, -0.1, 2, MOYEU_DI, 64) - cyl(76, 0, -0.1, 2, MOYEU_DI, 64)
    t = mesh(essai); assert t.is_watertight; t.export(OUT / 'socle_essai_moyeu_3_tailles.stl')
    json.dump(r, open(OUT / 'verification_socle.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False, indent=1))
