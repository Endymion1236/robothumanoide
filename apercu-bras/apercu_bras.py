"""Maquette du futur bras de table (4 servos STS3215) : images, animation et STL pour Fusion.

Maquette de principe, PAS une pièce à imprimer : les servos sont des pavés aux vraies cotes
(45,2 x 24,4 x 32,9, axe à 8,1 du bout, disques Ø19,7), les segments sont des plaques simples.
Le coude reprend le principe de la fourche V1 (deux plaques vissées sur les deux disques).
Axes : 1 = socle tournant (vertical), 2 = épaule, 3 = coude (horizontaux), 4 = pince.
"""
from pathlib import Path
import math, numpy as np, manifold3d as mf, trimesh as tm
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image

OUT = Path(__file__).resolve().parent
L_BRAS, L_AVANT = 120.0, 120.0           # épaule → coude, coude → pince (mm)
H_EPAULE = 95.0                          # hauteur de l'axe d'épaule au-dessus de la table
SL, SW, SH, AXE, DISQ = 45.2, 24.4, 32.9, 8.1, 19.7
Y_PLAQUE = 22.1                          # plaques de fourche : 20,1 (disques) + 2

def T(R=np.eye(3), t=(0, 0, 0)):
    m = np.eye(4); m[:3, :3] = R; m[:3, 3] = t; return m
def Rz(a): c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def Ry(a): c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def place(m, M): return m.transform(M[:3, :].tolist())
def box(x, y, z, l, w, h): return mf.Manifold.cube((l, w, h)).translate((x, y, z))
def cyl(d, h, z=0.0): return mf.Manifold.cylinder(h, d/2, d/2, 48).translate((0, 0, z))

def servo_local():
    """Servo, axe de sortie = axe z local passant par l'origine, corps vers +x, disques compris."""
    b = box(-AXE, -SW/2, -SH/2, SL, SW, SH)
    return b + cyl(DISQ, 4.3, SH/2) + cyl(DISQ, 3, -SH/2 - 3)
# Axe du servo horizontal (le long de Y), corps vers le bas (-Z) : x_local -> -Z, z_local -> +Y.
R_HORIZ = np.column_stack([(0, 0, -1), (-1, 0, 0), (0, 1, 0)])

def fourche(longueur):
    """Segment en fourche : deux plaques de part et d'autre du servo + entretoise, le long de +Z."""
    f = mf.Manifold()
    for s in (1, -1):
        y0 = Y_PLAQUE if s > 0 else -Y_PLAQUE - 4
        f += box(-12, y0, -12, 24, 4, longueur + 12)
        f += mf.Manifold.cylinder(4, 12, 12, 48).rotate((-90, 0, 0)).translate((0, y0, 0))
    f += box(-12, -Y_PLAQUE - 4, 50, 24, 2*Y_PLAQUE + 8, 12)       # entretoise A
    return f

def scene(q1, q2, q3, ouverture):
    """Renvoie [(nom, solide, couleur)] pour les angles en degrés (0,0,0 = bras tendu vers le haut)."""
    q1, q2, q3 = map(math.radians, (q1, q2, q3))
    parts = []
    socle = cyl(110, 8) + cyl(56, 30, 8)                                   # pied + logement servo 1
    parts.append(('socle', socle, '#9e9e9e'))
    M1 = T(Rz(q1), (0, 0, 46))
    parts.append(('servo 1 (socle)', place(servo_local().transform([[0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 0]]), T(np.eye(3), (0, 0, 46 - SH/2 - 4.3))), '#333333'))
    plateau = cyl(80, 6)
    support = box(-16, -12.5, 6, 32, 25, H_EPAULE - 46 - (SL - AXE))       # tient le corps du servo d'épaule
    parts.append(('plateau tournant', place(plateau + support, M1), '#7aa6c2'))
    M2 = M1 @ T(np.eye(3), (0, 0, H_EPAULE - 46))
    parts.append(('servo 2 (épaule)', place(servo_local(), M2 @ T(R_HORIZ)), '#333333'))
    M2r = M2 @ T(Ry(q2))
    bras = fourche(L_BRAS) + box(-12, -12.2, 62, 24, 24.4, L_BRAS - (SL - AXE) - 62)  # poutre jusqu'au servo du coude
    parts.append(('bras', place(bras, M2r), '#9ccc8c'))
    M3 = M2r @ T(np.eye(3), (0, 0, L_BRAS))
    parts.append(('servo 3 (coude)', place(servo_local(), M3 @ T(R_HORIZ)), '#333333'))
    M3r = M3 @ T(Ry(q3))
    parts.append(('avant-bras = coude V1', place(fourche(L_AVANT), M3r), '#397c92'))
    M4 = M3r @ T(np.eye(3), (0, 0, L_AVANT))
    pince = box(-14, -14, 0, 28, 28, 14)
    parts.append(('servo 4 (pince)', place(servo_local().transform([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]]).translate((0, 0, 14 + SL - AXE)), M4), '#333333'))
    e = 4 + ouverture/2
    doigts = box(e, -8, 14 + SL, 4, 16, 45) + box(-e - 4, -8, 14 + SL, 4, 16, 45)
    parts.append(('pince', place(pince.translate((0, 0, SL - AXE)) + doigts, M4), '#e1a64a'))
    return parts

def mesh(m):
    a = m.to_mesh(); return tm.Trimesh(vertices=a.vert_properties[:, :3], faces=a.tri_verts, process=True)
LUMIERE = np.array([0.4, -0.5, 0.75]); LUMIERE /= np.linalg.norm(LUMIERE)
def dessiner(ax, parts, titre):
    for nom, solide, c in parts:
        t = mesh(solide)
        if len(t.faces) == 0: continue
        base = np.array(matplotlib.colors.to_rgb(c))
        k = 0.45 + 0.55*np.clip(t.face_normals @ LUMIERE, 0, 1)
        ax.add_collection3d(Poly3DCollection(t.vertices[t.faces], facecolors=np.clip(base*k[:, None], 0, 1), linewidth=0))
    ax.set(xlim=(-200, 200), ylim=(-200, 200), zlim=(0, 400)); ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off(); ax.set_title(titre, fontsize=11); ax.view_init(elev=18, azim=-55)
    xx, yy = np.meshgrid([-200, 200], [-200, 200]); ax.plot_surface(xx, yy, np.zeros_like(xx), color='#e8e2d6', alpha=.5)

POSES = [('Au repos, bras tendu', (0, 0, 0, 30)),
         ('Penché pour attraper', (35, 55, 75, 40)),
         ('Objet saisi, levé et tourné', (-110, 25, 55, 12))]
if __name__ == '__main__':
    fig = plt.figure(figsize=(15, 6.2)); fig.patch.set_facecolor('#f5f5f2')
    for k, (titre, q) in enumerate(POSES):
        dessiner(fig.add_subplot(1, 3, k+1, projection='3d'), scene(*q), titre)
    fig.text(.5, .03, 'Gris : servos STS3215 · gris clair : socle · bleu ciel : plateau tournant · vert : bras · '
             'bleu : avant-bras (= ton coude V1) · orange : pince — maquette de principe, pas une pièce à imprimer', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .06, 1, 1)); fig.savefig(OUT/'apercu_bras_complet.png', dpi=130)
    # Animation : prendre à droite, poser à gauche
    cles = [(0, 0, 0, 40), (35, 0, 0, 40), (35, 55, 75, 40), (35, 55, 75, 10), (35, 20, 60, 10),
            (-110, 20, 60, 10), (-110, 55, 75, 10), (-110, 55, 75, 40), (-110, 0, 0, 40), (0, 0, 0, 40)]
    images = []
    for a, b in zip(cles, cles[1:]):
        for i in range(6):
            u = (1 - math.cos(math.pi*i/6))/2
            q = [x + (y - x)*u for x, y in zip(a, b)]
            f = plt.figure(figsize=(5.5, 5.5)); f.patch.set_facecolor('#f5f5f2')
            ax = f.add_subplot(projection='3d'); dessiner(ax, scene(*q), 'Prendre à droite, poser à gauche')
            f.tight_layout(); f.canvas.draw()
            images.append(Image.fromarray(np.asarray(f.canvas.buffer_rgba())[..., :3])); plt.close(f)
    images[0].save(OUT/'animation_bras.gif', save_all=True, append_images=images[1:], duration=110, loop=0)
    # STL de la pose « penché » pour Fusion (Insérer → Insérer un maillage)
    tout = mf.Manifold()
    for _, s, _ in scene(*POSES[1][1]): tout += s
    mesh(tout).export(OUT/'maquette_bras_complet.stl')
    print('ok', len(images), 'images')
