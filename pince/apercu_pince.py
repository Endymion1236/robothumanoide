"""Images et animation de la pince (à lancer après generer_pince.py)."""
import math
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
import generer_pince as G

COUL = {'gobelet': '#f2efe6', 'base': '#9ccc8c', 'bride': '#7fb26d', 'servo': '#333333', 'avant-bras': '#397c92', 'engrenage A': '#e1a64a',
        'engrenage B': '#e1a64a', 'bras libre +Y': '#c58fd1', 'bras libre -Y': '#c58fd1', 'doigt +Y': '#d0473c', 'doigt -Y': '#d0473c'}
LUM = np.array([0.4, -0.5, 0.75]); LUM /= np.linalg.norm(LUM)

def dessiner(ax, th, titre, gobelet=None):
    pieces = {'base': G.BASE, 'bride': G.BRIDE, 'servo': G.SERVO, 'avant-bras': G.AVB} | G.pose(th)
    if gobelet:
        D = gobelet; q1x = G.AX + G.L_BRAS * math.cos(math.radians(th))
        pieces['gobelet'] = G.mf.Manifold.cylinder(110, D / 2, D / 2 * 0.75, 64).translate((q1x + G.PAD_DEVANT + G.PAD_LONG / 2, 0, -50))
    for nom, m in pieces.items():
        t = G.mesh(m); base = np.array(matplotlib.colors.to_rgb(COUL[nom]))
        k = 0.45 + 0.55 * np.clip(t.face_normals @ LUM, 0, 1)
        ax.add_collection3d(Poly3DCollection(t.vertices[t.faces], facecolors=np.clip(base * k[:, None], 0, 1), linewidth=0))
    ax.set(xlim=(-25, 145), ylim=(-85, 85), zlim=(-60, 110)); ax.set_box_aspect((1, 1, 1)); ax.set_axis_off()
    ax.view_init(elev=28, azim=-40); ax.set_title(titre, fontsize=12)

if __name__ == '__main__':
    fig = plt.figure(figsize=(15, 6)); fig.patch.set_facecolor('#f5f5f2')
    th80 = math.degrees(math.asin((40 + G.E_DOIGT - G.AY) / G.L_BRAS))
    for k, (th, t, gob) in enumerate([(G.TH_OUVERT, 'ouverte (110 mm)', None), (th80, 'serre un gobelet de 80 mm', 80.0),
                                      (G.TH_FERME, 'fermée (14 mm au creux)', None)]):
        dessiner(fig.add_subplot(1, 3, k + 1, projection='3d'), th, 'Pince V2 ' + t, gob)
    fig.text(.5, .03, 'Vert : base et bride · noir : servo · bleu : bout de l\'avant-bras · orange : engrenages · violet : bras libres · '
             'rouge : doigts (creusés en arrondi) · blanc : gobelet — prototype non validé', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .06, 1, 1)); fig.savefig(G.OUT / 'apercu_pince.png', dpi=120)
    images = []
    angles = list(np.linspace(G.TH_OUVERT, G.TH_FERME, 12)) + list(np.linspace(G.TH_FERME, G.TH_OUVERT, 12))
    for th in angles:
        f = plt.figure(figsize=(5, 5)); f.patch.set_facecolor('#f5f5f2')
        dessiner(f.add_subplot(projection='3d'), th, f'écart {2 * (G.AY + G.L_BRAS * math.sin(math.radians(th)) - G.E_DOIGT):.0f} mm')
        f.tight_layout(); f.canvas.draw(); images.append(Image.fromarray(np.asarray(f.canvas.buffer_rgba())[..., :3])); plt.close(f)
    images[0].save(G.OUT / 'animation_pince.gif', save_all=True, append_images=images[1:], duration=120, loop=0)
    print('ok')
