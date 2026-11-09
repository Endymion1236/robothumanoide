"""Feuille de route illustrée : les 6 étapes après la carte neuve (maquette de principe)."""
from pathlib import Path
import math, numpy as np, manifold3d as mf
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import apercu_bras as A

OUT = Path(__file__).resolve().parent
GRIS = '#c9c9c9'

def scene6(q1, q2, q3, q5, q6, ouverture):
    """Bras à 6 axes : comme la maquette à 4 axes, avec un poignet (2 servos) avant la pince."""
    parts = [p for p in A.scene(q1, q2, q3, ouverture) if p[0] not in ('servo 4 (pince)', 'pince')]
    q1r, q2r, q3r, q5r, q6r = map(math.radians, (q1, q2, q3, q5, q6))
    M1 = A.T(A.Rz(q1r), (0, 0, 46)); M2 = M1 @ A.T(np.eye(3), (0, 0, A.H_EPAULE - 46))
    M3 = M2 @ A.T(A.Ry(q2r)) @ A.T(np.eye(3), (0, 0, A.L_BRAS))
    M4 = M3 @ A.T(A.Ry(q3r)) @ A.T(np.eye(3), (0, 0, A.L_AVANT))
    parts.append(('servo 5 (poignet)', A.place(A.servo_local(), M4 @ A.T(A.R_HORIZ)), '#333333'))
    M5 = M4 @ A.T(A.Ry(q5r))
    parts.append(('chape du poignet', A.place(A.fourche(30).translate((0, 0, 0)) - A.box(-20, -40, 50, 40, 80, 20), M5), '#c58fd1'))
    M6 = M5 @ A.T(A.Rz(q6r), (0, 0, 42))
    parts.append(('servo 6 (rotation)', A.place(A.servo_local().transform([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]]).translate((0, 0, A.SL - A.AXE)), M6), '#333333'))
    pince = A.box(-14, -14, 0, 28, 28, 10); e = 4 + ouverture/2
    doigts = A.box(e, -8, 10, 4, 16, 40) + A.box(-e - 4, -8, 10, 4, 16, 40)
    parts.append(('pince', A.place((pince + doigts).translate((0, 0, A.SL + 4)), M6), '#e1a64a'))
    return parts

def griser(parts, garder):
    return [(n, s, c if any(k in n for k in garder) else GRIS) for n, s, c in parts]

from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def dessiner(ax, parts, sol=True, elev=18, azim=-55, marge=1.15):
    """Rendu ombré, cadré automatiquement sur les pièces ; sol facultatif."""
    mins, maxs = [], []
    for nom, solide, c in parts:
        t = A.mesh(solide)
        if len(t.faces) == 0: continue
        base = np.array(matplotlib.colors.to_rgb(c))
        k = 0.45 + 0.55*np.clip(t.face_normals @ A.LUMIERE, 0, 1)
        ax.add_collection3d(Poly3DCollection(t.vertices[t.faces], facecolors=np.clip(base*k[:, None], 0, 1), linewidth=0))
        mins.append(t.bounds[0]); maxs.append(t.bounds[1])
    lo, hi = np.min(mins, axis=0), np.max(maxs, axis=0)
    if sol: lo[2] = 0
    c, r = (lo + hi)/2, (hi - lo).max()/2*marge
    if sol:
        xx, yy = np.meshgrid([c[0] - r, c[0] + r], [c[1] - r, c[1] + r])
        ax.plot_surface(xx, yy, np.zeros_like(xx), color='#e8e2d6', alpha=.5)
    ax.set(xlim=(c[0] - r, c[0] + r), ylim=(c[1] - r, c[1] + r), zlim=(c[2] - r, c[2] + r))
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.view_init(elev=elev, azim=azim)

def carte(ax, titre, lignes, couleur):
    ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(FancyBboxPatch((.04, .04), .92, .92, boxstyle='round,pad=0.02', fc='white', ec=couleur, lw=2))
    ax.text(.5, .88, titre, ha='center', va='center', fontsize=11, weight='bold', color=couleur)
    for i, l in enumerate(lignes):
        ax.text(.1, .74 - i*.12, l, ha='left', va='center', fontsize=9.5)

fig = plt.figure(figsize=(18, 11.5)); fig.patch.set_facecolor('#f5f5f2')
fig.suptitle('La suite du bras, étape par étape (après la carte neuve)', fontsize=17, weight='bold', y=.985)
TITRES = [
 ('1. Préparer chaque servo', 'Seul sur la carte, rien dessus :\nnuméro (ID), milieu à 2048,\nbutées 908 / 3188, protection.'),
 ('2. Valider le coude', 'Fourche V1.2 + bras V1 + bride à cale.\nÀ la main hors tension, puis lent\ndans FD (vitesse 300).'),
 ('3. La pince', 'Un 2e servo au bout de l\'avant-bras :\ndeux doigts qui s\'ouvrent\net se ferment.'),
 ('4. Épaule et socle tournant', 'Socle sur 2 roulements 6807,\népaule qui lève le bras :\nil prend et pose un objet (4 axes).'),
 ('5. Le poignet', '2 servos de plus : la pince s\'incline\net tourne. Bras complet à 6 axes.'),
 ('6. Le faire bouger tout seul', 'Positions enregistrées enchaînées\npar l\'ordinateur, puis par l\'ESP32.'),
]
for k, (t, legende) in enumerate(TITRES):
    if k == 0:
        ax = fig.add_subplot(2, 3, 1)
        ax.set_axis_off(); ax.set_xlim(0, 10); ax.set_ylim(0, 10)
        # carte + un seul servo, liste à cocher
        ax.add_patch(FancyBboxPatch((.4, 5.6), 3.4, 2.4, boxstyle='round,pad=0.1', fc='#20262b', ec='k'))
        ax.text(2.1, 6.8, 'carte\nWaveshare', color='w', ha='center', va='center', fontsize=10)
        ax.add_patch(FancyBboxPatch((6.2, 5.8), 3.0, 2.0, boxstyle='round,pad=0.1', fc='#333', ec='k'))
        ax.add_patch(plt.Circle((6.9, 7.3), .45, color='#bbb'))
        ax.text(7.9, 6.5, 'servo', color='w', ha='center', fontsize=10)
        ax.plot([3.9, 6.1], [6.8, 6.8], color='#d0473c', lw=3); ax.plot([3.9, 6.1], [6.6, 6.6], color='k', lw=2); ax.plot([3.9, 6.1], [7.0, 7.0], color='#eee', lw=2)
        ax.text(5, 8.6, 'un seul servo à la fois', ha='center', fontsize=10, style='italic')
        for i, l in enumerate(['☐  numéro : coude = 3, pince = 4…', '☐  milieu : position 2048',
                               '☐  butées : 908 et 3188 (± 100°)', '☐  protection couple / courant',
                               '☐  vérifier qu\'il refuse d\'aller au-delà']):
            ax.text(.6, 4.6 - i*.95, l, fontsize=10.5)
    elif k == 5:
        ax = fig.add_subplot(2, 3, 6)
        ax.set_axis_off(); ax.set_xlim(0, 10); ax.set_ylim(0, 10)
        def boite(x, y, w, h, txt, c):
            ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.1', fc=c, ec='k'))
            ax.text(x + w/2, y + h/2, txt, ha='center', va='center', fontsize=10, color='w' if c != '#f0d9a8' else 'k')
        boite(.3, 7.0, 2.6, 1.6, 'ordinateur\n(Python)', '#397c92'); boite(.3, 3.6, 2.6, 1.6, 'ESP32\n(plus tard)', '#5b8c4e')
        boite(4.0, 5.3, 2.4, 1.6, 'carte\nservos', '#20262b')
        ax.annotate('', xy=(4.0, 6.5), xytext=(2.9, 7.7), arrowprops=dict(arrowstyle='->', lw=2))
        ax.annotate('', xy=(4.0, 5.7), xytext=(2.9, 4.4), arrowprops=dict(arrowstyle='->', lw=2, ls='--'))
        for i, n in enumerate(['1', '2', '3', '4', '5', '6']):
            ax.add_patch(plt.Circle((7.3 + (i % 2)*1.3, 8.0 - (i // 2)*1.5), .45, color='#333'))
            ax.text(7.3 + (i % 2)*1.3, 8.0 - (i // 2)*1.5, n, color='w', ha='center', va='center', fontsize=10)
        ax.annotate('', xy=(6.9, 6.5), xytext=(6.4, 6.1), arrowprops=dict(arrowstyle='->', lw=2))
        for i, l in enumerate(['« au-dessus de l\'objet »', '« pince fermée »', '« au-dessus de la boîte »', '« pince ouverte »']):
            boite(.3 + (i % 2)*4.8, 1.3 - (i // 2)*1.1, 4.4, .75, l, '#f0d9a8')
    else:
        ax = fig.add_subplot(2, 3, k + 1, projection='3d')
        if k == 1:
            p = griser(A.scene(0, 90, 0, 30), ('coude', 'avant-bras'))
            p = [x for x in p if x[0] in ('servo 3 (coude)', 'avant-bras = coude V1')]
            dessiner(ax, p, sol=False, elev=22, azim=-60, marge=.72)
        elif k == 2:
            p = A.scene(0, 90, 0, 40)
            p = griser([x for x in p if x[0] in ('servo 3 (coude)', 'avant-bras = coude V1', 'servo 4 (pince)', 'pince')], ('pince',))
            dessiner(ax, p, sol=False, elev=22, azim=-60, marge=.72)
        elif k == 3:
            dessiner(ax, griser(A.scene(35, 55, 75, 40), ('socle', 'plateau', 'servo 1', 'servo 2', 'bras')))
        elif k == 4:
            dessiner(ax, griser(scene6(35, 50, 70, 50, 45, 30), ('poignet', 'servo 5', 'servo 6', 'pince')))
    ax.set_title(t, fontsize=13, weight='bold', loc='left', pad=4)
    if k: fig.text([.05, .385, .72][k % 3], [.515, .04][k // 3], legende, fontsize=10.5, va='bottom', color='#333')
fig.text(.5, .008, 'En couleur : ce qu\'on fait à cette étape · en gris clair : ce qui est déjà fait · maquette de principe, pas des pièces à imprimer',
         ha='center', fontsize=10, color='#555')
fig.tight_layout(rect=(0, .07, 1, .96), h_pad=6)
fig.savefig(OUT/'etapes_suivantes.png', dpi=120)
print('ok')
