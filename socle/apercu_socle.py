"""Images du socle tournant : sortie/apercu_socle.png (vue éclatée, coupe, monté sous le bâti)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'epaule'))
import numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import generer_socle as S, generer_epaule as E
C = {'base': '#c9a35a', 'palier': '#5b8bd6', 'entretoise': '#9b6fd0', 'roulement': '#9aa7b3', 'plateau': '#e0602a', 'servo': '#3a3a3a', 'bati': '#7fb069'}
LUM = np.array([0.35, -0.55, 0.75]); LUM /= np.linalg.norm(LUM)
def dessiner(ax, pieces, vue, cadre, marge=0.6):
    e, a = map(math.radians, vue); cam = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    polys, fc, ec, lw = [], [], [], []
    for m, c in pieces:
        t = S.mesh(m); base = np.array(matplotlib.colors.to_rgb(c)); k = 0.55 + 0.45 * np.clip(t.face_normals @ LUM, 0, 1)
        for tri, cc in zip(t.vertices[t.faces], np.clip(base * k[:, None], 0, 1)):
            polys.append(tri); fc.append((*cc, 1)); ec.append((*cc, 1)); lw.append(0.25)
        vif = t.face_adjacency_angles > math.radians(25); vu = (t.face_normals[t.face_adjacency] @ cam).max(axis=1) > -0.05
        for i, j in t.face_adjacency_edges[vif & vu]:
            p, q = t.vertices[i] + cam * 0.4, t.vertices[j] + cam * 0.4
            polys.append(np.array([p, q, p])); fc.append((0, 0, 0, 0)); ec.append((0.08, 0.08, 0.08, 1)); lw.append(0.8)
    ax.add_collection3d(Poly3DCollection(polys, facecolors=fc, edgecolors=ec, linewidths=lw))
    mi, ma = np.array(cadre[::2], float), np.array(cadre[1::2], float); c0, d = (mi + ma) / 2, (ma - mi).max() / 2 * marge
    ax.set(xlim=(c0[0] - d, c0[0] + d), ylim=(c0[1] - d, c0[1] + d), zlim=(c0[2] - d, c0[2] + d)); ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.view_init(*vue)
def etiq(ax, xyz, txt, d, coul='#111'):
    x2, y2, _ = proj3d.proj_transform(*xyz, ax.get_proj())
    ax.annotate(txt, xy=(x2, y2), xytext=d, textcoords='offset points', fontsize=11.5, weight='bold', color=coul, ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=coul, lw=1.3), arrowprops=dict(arrowstyle='-|>', color=coul, lw=1.5), zorder=50)
T = lambda m, dz: m.translate((0, 0, dz))
fig = plt.figure(figsize=(18, 9)); fig.patch.set_facecolor('white')
fig.suptitle('Socle tournant (servo n° 1) — V1, prototype sans validation physique', fontsize=17, weight='bold')
# 1. éclaté
ax = fig.add_subplot(1, 3, 1, projection='3d'); ax.set_title('Vue éclatée', fontsize=14)
pcs = [(S.BASE, C['base']), (T(S.SERVO, 25), C['servo']), (T(S.PALIER, 60), C['palier']), (T(S.anneau(S.Z_RA, S.Z_RA + S.ROUL_EP, 47, 35), 95), C['roulement']),
       (T(S.ENTRETOISE, 105), C['entretoise']), (T(S.anneau(S.Z_RB, S.Z_RB + S.ROUL_EP, 47, 35), 115), C['roulement']), (T(S.PLATEAU, 150), C['plateau'])]
dessiner(ax, pcs, (20, -60), (-100, 60, -70, 70, 0, 240), 0.62)
etiq(ax, (45, -50, 3), 'base\n(serrée sur la table)', (60, -30), '#8a6a20'); etiq(ax, (-30, -12, 45), 'servo n° 1,\npalonnier en haut', (-110, 10))
etiq(ax, (-45, -33, 102), 'palier', (-90, 10), C['palier']); etiq(ax, (23, 0, 140), '2 roulements 6807\n+ entretoise', (-130, 0), '#55606b')
etiq(ax, (-90, -50, 228), 'plateau tournant', (60, 60), C['plateau']); etiq(ax, (0, 0, 195), 'moyeu creux', (110, -20), C['plateau'])
# 2. coupe
ax = fig.add_subplot(1, 3, 2, projection='3d'); ax.set_title('Monté, coupé par le milieu', fontsize=14)
demi = S.box(-200, -200, -10, 200, 0, 300)
pcs = [(S.BASE - demi, C['base']), (S.SERVO, C['servo']), (S.PALIER - demi, C['palier']), (S.ROULEMENTS - demi, C['roulement']), (S.ENTRETOISE - demi, C['entretoise']), (S.PLATEAU - demi, C['plateau'])]
dessiner(ax, pcs, (12, -90), (-100, 60, -10, 70, 0, 85), 0.55); ax.set_proj_type('ortho')
etiq(ax, (0, 0, 42), 'palonnier vissé\nau moyeu (4 vis M2,5)', (-150, 60)); etiq(ax, (23, 0, 65), 'roulement\ndu haut', (60, 110), '#55606b'); etiq(ax, (23, 0, 45), 'roulement\ndu bas', (60, -90), '#55606b')
etiq(ax, (-30, 0, 41), 'le palier appuie\nsur le servo', (-150, -40), C['palier'])
# 3. sous le bâti
ax = fig.add_subplot(1, 3, 3, projection='3d'); ax.set_title('Le bâti vissé sur le plateau (4 vis M3 × 12)', fontsize=14)
axx, ayy = S.AXE_DANS_PIED; dz = S.Z_PLATEAU + S.EP_PLATEAU + E.H_AXE + E.EP_PIED
place = lambda m: m.translate((-axx, -ayy, dz))
pcs = [(S.BASE, C['base']), (S.PALIER, C['palier']), (S.PLATEAU, C['plateau']), (place(E.BATI), C['bati']), (place(E.BERCEAU_E + E.BRIDE_E), '#dcdcdc'), (place(E.SERVO_E), '#888'),
       (place(E.BRAS_BAS + E.BRAS_HAUT), '#dcdcdc')]
dessiner(ax, pcs, (18, -55), (-100, 150, -70, 70, 0, 240), 0.6)
etiq(ax, (0, -31, dz), 'axe de l\'épaule\nà 179 mm de la table', (120, 40)); etiq(ax, (-95, -55, 74), 'plateau', (-70, -20), C['plateau'])
fig.text(0.5, 0.03, 'Rotation prévue : ± 90°. Le poids (moins d\'1 kg) descend par le servo ; les 2 roulements empêchent le bras de pencher.', ha='center', fontsize=12.5)
fig.subplots_adjust(left=0, right=1, top=0.9, bottom=0.06, wspace=0); fig.savefig(S.OUT / 'apercu_socle.png', dpi=100); print('ok')
