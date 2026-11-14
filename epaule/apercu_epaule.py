"""Images de l'épaule montée : sortie/apercu_epaule.png (3 positions) et sortie/apercu_epaule_cote.png (vue de côté)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import generer_epaule as E
E.PINCE = E.pince_ouverte()
COUL = {'bâti': '#9fb7a0', 'berceau': '#c8d6c9', 'servo': '#3a3a3a', 'bras': '#e1a64a', 'avant-bras': '#397c92', 'pince': '#7fa87f', 'ressort': '#c0392b'}
def scene(alpha, gamma, trou=(-40.0, 44.0)):
    p = E.bras_complet(alpha, gamma)
    return [(E.BATI, COUL['bâti'], .55), (E.BERCEAU_E + E.BRIDE_E, COUL['berceau'], .8), (E.SERVO_E, COUL['servo'], .9),
            (p['bras bas'] + p['bras haut'], COUL['bras'], .9), (p['berceau du coude'] + p['bride du coude'], COUL['berceau'], .85),
            (p['servo du coude'], COUL['servo'], .9), (p['avant-bras et pince'], COUL['avant-bras'], .75), (E.ressort(alpha, trou, 10)[0], COUL['ressort'], 1)]
def dessiner(ax, pcs, vue, cadre):
    for m, c, a in pcs:
        t = E.mesh(m); ax.add_collection3d(Poly3DCollection(t.vertices[t.faces], facecolor=c, edgecolor='#222', linewidth=.05, alpha=a))
    x0, x1, y0, y1, z0, z1 = cadre
    ax.set(xlim=(x0, x1), ylim=(y0, y1), zlim=(z0, z1)); ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0)); ax.view_init(elev=vue[0], azim=vue[1]); ax.set_axis_off()
if __name__ == '__main__':
    cadre = (-100, 400, -60, 200, -110, 260)
    fig = plt.figure(figsize=(18, 7)); fig.patch.set_facecolor('#f5f5f2')
    for k, (titre, a, g) in enumerate([('Bras horizontal, tendu', 0, 0), ('Épaule à 45°, avant-bras horizontal', 45, -45), ('Épaule à 90°, coude plié à 90°', 90, -90)]):
        ax = fig.add_subplot(1, 3, k + 1, projection='3d'); dessiner(ax, scene(a, g), (18, -62), cadre); ax.set_title(titre, fontsize=14)
    fig.text(.5, .03, 'Vert : bâti · orange : haut du bras · bleu : avant-bras et pince · rouge : ressort · Prototype, aucune validation physique', ha='center', fontsize=12)
    fig.tight_layout(rect=(0, .05, 1, 1)); fig.savefig(E.OUT / 'apercu_epaule.png', dpi=110)
    fig = plt.figure(figsize=(16, 8)); fig.patch.set_facecolor('#f5f5f2')
    ax = fig.add_subplot(1, 2, 1, projection='3d'); ax.set_proj_type('ortho'); dessiner(ax, scene(0, 0), (0, -90), (-100, 180, -60, 200, -110, 120)); ax.set_title('Vue de côté (bras horizontal)', fontsize=14)
    ax = fig.add_subplot(1, 2, 2, projection='3d'); ax.set_proj_type('ortho'); dessiner(ax, scene(0, 0), (90, -90), (-100, 180, -30, 200, -110, 120)); ax.set_title('Vue de dessus', fontsize=14)
    fig.tight_layout(); fig.savefig(E.OUT / 'apercu_epaule_cote.png', dpi=110)
    print('ok')
