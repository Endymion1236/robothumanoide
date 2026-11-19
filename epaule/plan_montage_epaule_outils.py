"""Outils de dessin des plans de montage (repris de plan_montage.py de l'épaule), pour les autres plans."""

import math, textwrap, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import generer_epaule as E
E.PINCE = E.pince_ouverte()
import textwrap

# ---------------- couleurs : UNE par pièce, gardée dans tout le plan ----------------
C = {'bati': '#7fb069', 'berceau': '#5b8bd6', 'bride': '#9b6fd0', 'bas': '#f0a030', 'haut': '#e0602a', 'servo': '#3a3a3a',
     'coude': '#2f9fae', 'ressort': '#d0302a'}
GRIS, GRIS_SERVO = '#dcdcdc', '#a8a8a8'
LAITON, NOIR = '#d6a62e', '#151515'
CABLE = '#f2d21b'
TROU_CONSEILLE = (-46.0, 50.0)

def cy(x, z, y0, y1, d, n=24): return E.cyl_y(x, z, min(y0, y1), max(y0, y1), d, n)
def insert(x, z, y, sens=1): return cy(x, z, y, y + sens * 5.7, 4.8, 20) - cy(x, z, y - sens * 0.1, y + sens * 5.8, 2.6, 12)
def vis(x, z, y_tete, longueur, sens, d=3.0):
    """Vis d'axe Y : tête en y_tete (côté opposé à sens), tige de longueur `longueur` dans le sens `sens`."""
    return cy(x, z, y_tete, y_tete - sens * d, d * 1.8, 20) + cy(x, z, y_tete, y_tete + sens * longueur, d, 12)
def ecrou(x, z, y): return cy(x, z, y, y + 2.4, 6.2, 6)
def rot_y_vers_z(m): return m.rotate((90, 0, 0))                 # pour montrer une pièce « face Y vers le haut »
def p_y_vers_z(p): return (p[0], -p[2], p[1])

# ---------------- rendu : faces ombrées + arêtes vives en noir ----------------
LUM = np.array([0.35, -0.55, 0.75]); LUM /= np.linalg.norm(LUM)
def dessiner(ax, pieces, vue=(24, 48), marge=1.0, cadre=None):
    """pieces : (manifold, couleur). Arêtes vives (> 25°) dessinées en noir, seulement celles tournées vers nous."""
    e, a = map(math.radians, vue)
    cam = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    polys, fc, ec, lw, pts = [], [], [], [], []
    for m, c in pieces:
        t = E.mesh(m); base = np.array(matplotlib.colors.to_rgb(c)); pts.append(t.vertices)
        k = 0.55 + 0.45 * np.clip(t.face_normals @ LUM, 0, 1)
        col = np.clip(base * k[:, None], 0, 1)
        for tri, cc in zip(t.vertices[t.faces], col):
            polys.append(tri); fc.append((*cc, 1)); ec.append((*cc, 1)); lw.append(0.25)
        vif = t.face_adjacency_angles > math.radians(25)
        vu = (t.face_normals[t.face_adjacency] @ cam).max(axis=1) > -0.05
        for i, j in t.face_adjacency_edges[vif & vu]:
            p, q = t.vertices[i] + cam * 0.4, t.vertices[j] + cam * 0.4
            polys.append(np.array([p, q, p])); fc.append((0, 0, 0, 0)); ec.append((0.08, 0.08, 0.08, 1)); lw.append(0.9)
    ax.add_collection3d(Poly3DCollection(polys, facecolors=fc, edgecolors=ec, linewidths=lw))
    if cadre is None:
        v = np.vstack(pts); mi, ma = v.min(0), v.max(0)
    else:
        mi, ma = np.array(cadre[::2], float), np.array(cadre[1::2], float)
    c0, d = (mi + ma) / 2, (ma - mi).max() / 2 * marge
    ax.set(xlim=(c0[0] - d, c0[0] + d), ylim=(c0[1] - d, c0[1] + d), zlim=(c0[2] - d, c0[2] + d))
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.view_init(*vue)

def etiquette(ax, xyz, texte, decal, coul='#111', taille=12):
    x2, y2, _ = proj3d.proj_transform(*xyz, ax.get_proj())
    ax.annotate(texte, xy=(x2, y2), xytext=decal, textcoords='offset points', fontsize=taille, color=coul, weight='bold', ha='center',
                va='center', bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=coul, lw=1.4),
                arrowprops=dict(arrowstyle='-|>', color=coul, lw=1.6, shrinkA=2, shrinkB=1), zorder=50)
def guide(ax, p, q):
    ax.plot(*zip(p, q), ls=(0, (4, 3)), color='#c0392b', lw=1.4, zorder=40)

def panneaux(fig, n, titres=None):
    """n vues dans la partie gauche de la page."""
    axes = []
    for k in range(n):
        if n == 1: r = [0.0, 0.1, 0.6, 0.78]
        elif n == 2: r = [0.0, 0.1 + 0.4 * (1 - k), 0.6, 0.39]
        else: r = [0.0 + 0.3 * (k % 2), 0.1 + 0.4 * (1 - k // 2), 0.3, 0.39]
        ax = fig.add_axes(r, projection='3d'); axes.append(ax)
        if titres: ax.text2D(0.03, 0.97, titres[k], transform=ax.transAxes, fontsize=14, weight='bold', va='top')
    return axes

def legende(fig, elements):
    x = 0.02
    for coul, texte in elements:
        fig.add_artist(Rectangle((x, 0.035), 0.016, 0.022, transform=fig.transFigure, fc=coul, ec='#222', lw=0.8))
        fig.text(x + 0.021, 0.046, texte, fontsize=11.5, va='center'); x += 0.03 + 0.0072 * len(texte)


def mise_en_page(fig, n, total, titre, il_faut, faire, attention, leg):
    fig.text(0.03, 0.94, f'Étape {n} / {total} — {titre}', fontsize=24, weight='bold')
    legende(fig, list(leg) + [(GRIS, 'déjà monté'), (NOIR, 'vis'), (LAITON, 'insert M3')] + [('#c0392b', '- - - où va la vis')])
    nl = len(il_faut) + sum(len(textwrap.wrap(l, 48)) for l in faire) + len(faire) * 0.45 + (4 if attention else 0)
    k = min(1.0, 24 / nl); fs, pas, y = 14 * max(k, 0.8), 0.03 * k, 0.86
    fig.text(0.61, y, 'Il te faut :', fontsize=16, weight='bold'); y -= 0.035
    for l in il_faut: fig.text(0.62, y, '•  ' + l, fontsize=fs); y -= pas
    y -= 0.025 * k; fig.text(0.61, y, 'Ce qu\'il faut faire :', fontsize=16, weight='bold'); y -= 0.035
    for i, l in enumerate(faire, 1):
        fig.text(0.62, y, f'{i}.', fontsize=fs, weight='bold')
        for li in textwrap.wrap(l, 48): fig.text(0.645, y, li, fontsize=fs); y -= 0.028 * k
        y -= 0.012 * k
    if attention:
        y -= 0.02; fig.text(0.61, y, '\n'.join(textwrap.wrap('⚠ ' + attention, 50)), fontsize=13.5, va='top', color='#8a3b00',
                            bbox=dict(boxstyle='round,pad=0.6', fc='#fff3e0', ec='#e2783a'))
