"""Aperçu de la tête de poney de Câlin (palomino) : forme générale, AVANT de dessiner les pièces.
Gauche : habillée (tissu doré, crinière crème). Droite : dedans (crâne transparent).
Repère : X vers l'avant (le bout du nez), Y vers la gauche, Z vers le haut, en mm ; origine = axe du cou."""
import math, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import manifold3d as mf, trimesh as tm
from pathlib import Path
OUT = Path(__file__).resolve().parent / 'sortie'; OUT.mkdir(exist_ok=True)

def boule(x, y, z, r, n=48): return mf.Manifold.sphere(r, n).translate((x, y, z))
def cyl(p, q, r, n=32):
    p, q = np.array(p, float), np.array(q, float); v = q - p; L = float(np.linalg.norm(v))
    m = mf.Manifold.cylinder(L, r, r, n); v /= L
    ax = np.cross([0, 0, 1], v); s = np.linalg.norm(ax); ang = math.degrees(math.atan2(s, v[2]))
    if s > 1e-9:
        R = tm.transformations.rotation_matrix(math.radians(ang), ax / s)[:3, :3]
        m = m.transform([[*R[0], 0], [*R[1], 0], [*R[2], 0]])
    return m.translate(tuple(p))
def boite(c, d): return mf.Manifold.cube(d, True).translate(c)
def coque(*boules): return mf.Manifold.batch_hull(list(boules))
def mesh(m):
    g = m.to_mesh(); return tm.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts))

# --- forme de la tête (≈ 23 cm du chignon au bout du nez), un peu inclinée nez vers le bas ---
CRANE = [(0, 0, 75, 52), (25, 0, 95, 42)]                 # front et chignon
CHANFREIN = [(95, 0, 70, 34), (125, 0, 52, 33)]           # le long du nez
BOUT_NEZ = [(170, 0, 30, 30), (165, 0, 10, 26)]           # bout du nez, menton
GANACHE = [(20, 0, 30, 46)]                               # joues (ganaches)
tete = coque(*[boule(*b) for b in CRANE + CHANFREIN + BOUT_NEZ + GANACHE])
def oreille(s, angle_av=15):
    base = (0, s * 28, 118)
    m = coque(boule(base[0], base[1], base[2], 13), boule(base[0] + 8, base[1] + s * 6, base[2] + 48, 3))
    return m
OREILLES = [oreille(1), oreille(-1)]
COU = coque(boule(-30, 0, 40, 40), boule(-55, 0, -80, 45), boule(-20, 0, -80, 45))
CRINIERE = coque(*[boule(-10 - 12 * k, 0, 128 - 25 * k, 9) for k in range(8)]) + coque(boule(15, 0, 125, 10), boule(40, 0, 118, 6))   # crinière + toupet
OEIL_POS = [(58, s * 44, 92) for s in (1, -1)]
NASEAUX = [boule(193, s * 12, 20, 6) for s in (1, -1)]

PALOMINO, CREME, SOMBRE = '#d9a441', '#f3e6c4', '#3a2a1a'
def dessiner(ax, pieces, vue=(12, -60), titre=''):
    faces, coul = [], []
    L = np.array([0.4, -0.6, 0.7]); L /= np.linalg.norm(L)
    for m, c, a in pieces:
        t = mesh(m); base = np.array(matplotlib.colors.to_rgb(c))
        k = 0.45 + 0.55 * np.clip(t.face_normals @ L, 0, 1)
        rgb = np.clip(base * k[:, None], 0, 1); faces.append(t.vertices[t.faces])
        coul.append(np.hstack([rgb, np.full((len(rgb), 1), a)]))
    ax.add_collection3d(Poly3DCollection(np.concatenate(faces), facecolors=np.concatenate(coul), linewidth=0))
    ax.set(xlim=(-110, 200), ylim=(-155, 155), zlim=(-130, 180)); ax.set_box_aspect((1, 1, 1)); ax.set_axis_off()
    ax.view_init(*vue); ax.set_title(titre, fontsize=15, weight='bold')

def etiq(ax, xyz, txt, d):
    from mpl_toolkits.mplot3d import proj3d
    x2, y2, _ = proj3d.proj_transform(*xyz, ax.get_proj())
    ax.annotate(txt, xy=(x2, y2), xytext=d, textcoords='offset points', fontsize=10.5, weight='bold', ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#333'), arrowprops=dict(arrowstyle='-|>', color='#333', lw=1.3), zorder=50)

fig = plt.figure(figsize=(17, 9)); fig.patch.set_facecolor('white')
fig.suptitle('Câlin, tête de poney palomino : aperçu de la forme (rien n\'est encore dessiné en pièces)', fontsize=17, weight='bold')

# 1. habillée
ax = fig.add_subplot(1, 2, 1, projection='3d')
anneaux = [cyl((x, y - 4 * np.sign(y), z), (x, y + 3 * np.sign(y), z), 13) for x, y, z in OEIL_POS]
pieces = [(tete, PALOMINO, 1), (COU, PALOMINO, 1), (CRINIERE, CREME, 1)] + [(o, PALOMINO, 1) for o in OREILLES]
pieces += [(a, '#5ad1ff', 1) for a in anneaux] + [(n, SOMBRE, 1) for n in NASEAUX]
pieces += [(coque(boule(100, 0, 103, 8), boule(150, 0, 81, 7), boule(185, 0, 57, 6)), CREME, 1)]          # liste blanche sur le chanfrein
pieces += [(boule(56, 0, 124, 6), '#222', 1)]                                        # caméra discrète dans le front
dessiner(ax, pieces, vue=(22, -38), titre='Habillée : tissu doré, crinière crème')
etiq(ax, (58, 47, 92), 'yeux lumineux\n(anneaux de LED)', (-100, -60))
etiq(ax, (56, 0, 128), 'caméra\n(dans le front)', (60, 90))
etiq(ax, (4, 34, 160), 'oreilles mobiles', (-60, 60))
etiq(ax, (150, 0, 86), 'liste blanche', (110, 50))
etiq(ax, (-40, 0, 105), 'crinière crème', (-90, 40))
etiq(ax, (193, 12, 20), 'naseaux', (90, -50))

# 2. dedans
ax = fig.add_subplot(1, 2, 2, projection='3d')
pieces = [(tete, '#cfcfcf', 0.18), (COU, '#cfcfcf', 0.12)] + [(o, '#cfcfcf', 0.25) for o in OREILLES]
pieces += [(boite((-35, 0, -60), (24, 45, 33)), '#222', 1)]                          # servo du cou : tourner (axe vertical)
pieces += [(boite((-20, 0, 0), (45, 33, 24)), '#333', 1)]                            # servo du cou : hocher (axe gauche-droite)
pieces += [(boite((0, s * 26, 105), (23, 12, 29)), '#3f86d6', 1) for s in (1, -1)]  # 2 MG90S des oreilles
pieces += [(boite((48, 0, 107), (10, 26, 26)), '#e2783a', 1)]                        # caméra
pieces += [(cyl((x, y - 4 * np.sign(y), z), (x, y, z), 11), '#5ad1ff', 1) for x, y, z in OEIL_POS]
pieces += [(cyl((60, 0, 30), (60, 0, 50), 22), '#7fbf6a', 1)]                         # haut-parleur (sous la tête, vers le bas)
pieces += [(boule(130, 0, 15, 5), '#b57cc4', 1)]                                      # micro
dessiner(ax, pieces, titre='Dedans : ce que porte le crâne imprimé')
etiq(ax, (-35, 0, -60), 'cou : tourner\n(STS3215)', (-100, -40))
etiq(ax, (-20, 0, 0), 'cou : hocher\n(STS3215)', (-110, 30))
etiq(ax, (0, 26, 105), 'servos des oreilles\n(MG90S)', (-80, 80))
etiq(ax, (48, 0, 112), 'caméra', (40, 90))
etiq(ax, (58, 44, 92), 'yeux LED', (100, 60))
etiq(ax, (60, 0, 40), 'haut-parleur', (120, -40))
etiq(ax, (130, 0, 15), 'micro', (90, -70))
fig.subplots_adjust(left=0, right=1, top=0.9, bottom=0, wspace=0)
fig.savefig(OUT / 'apercu_tete_poney.png', dpi=100)
print('ok')
