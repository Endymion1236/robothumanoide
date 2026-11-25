"""Objets d'essai à imprimer, pour mettre au point la reconnaissance à la caméra et le tri par le bras.
Lancer : python generer_objets.py → sortie/objet_*.stl, sortie/apercu_objets.png

Pourquoi ces cotes :
  - 60 mm de HAUT pour tous : la pince saisit bas (le bas des mâchoires est à 2 cm de la table), il lui faut de la matière à serrer ;
    un objet de 3 cm passerait sous les mâchoires dès que la pince est inclinée.
  - 26 à 40 mm de LARGE : la pince V4 serre de 14 à 110 mm (cote du dessin) ; au milieu de cette plage, elle ne force ni
    grande ouverte ni presque fermée.
  - des formes bien différentes VUES DE DESSUS (c'est ce que voit la caméra) : rond, carré, hexagone, allongé ; et deux
    diamètres de rond, pour trier par taille avec la largeur que mesure la pince en serrant.
Aucune pièce du robot n'est concernée : ce sont des objets libres, rien à mesurer avant."""
import math
from pathlib import Path
import manifold3d as mf, numpy as np, trimesh as tm

OUT = Path(__file__).parent / 'sortie'; OUT.mkdir(exist_ok=True)
H, CHANFREIN = 60.0, 1.0

def prisme(contour):
    """Un contour CONVEXE (liste de points, mm) monté sur 60 mm, avec un petit chanfrein en bas (première couche) et en haut.
    Construit comme l'enveloppe de quatre anneaux de points : un seul volume propre, sans facettes minuscules."""
    petit = mf.CrossSection([contour]).offset(-CHANFREIN, mf.JoinType.Miter).to_polygons()[0]
    pts = [(x, y, z) for anneau, z in ((petit, 0.0), (contour, CHANFREIN), (contour, H - CHANFREIN), (petit, H)) for x, y in anneau]
    return mf.Manifold.hull_points(pts)
def rond(d, n=96): return [(d / 2 * math.cos(2 * math.pi * k / n), d / 2 * math.sin(2 * math.pi * k / n)) for k in range(n)]
def polygone(n, sur_plats): r = sur_plats / 2 / math.cos(math.pi / n); return [(r * math.cos(2 * math.pi * k / n + math.pi / n), r * math.sin(2 * math.pi * k / n + math.pi / n)) for k in range(n)]
def rectangle(l, w): return [(-l / 2, -w / 2), (l / 2, -w / 2), (l / 2, w / 2), (-l / 2, w / 2)]

OBJETS = {   # nom du fichier : (contour, ce que c'est, largeur que la pince doit trouver en serrant)
    'objet_rond_grand':  (rond(40.0),            'cylindre Ø 40',                   '40'),
    'objet_rond_petit':  (rond(28.0),            'cylindre Ø 28',                   '28'),
    'objet_carre':       (rectangle(36.0, 36.0), 'pavé carré 36 × 36',              '36 (51 pris par les coins)'),
    'objet_hexagone':    (polygone(6, 38.0),     'hexagone, 38 entre deux plats',   '38 à 44'),
    'objet_allonge':     (rectangle(64.0, 26.0), 'barre 64 × 26',                   '26 en travers, 64 en long'),
}

if __name__ == '__main__':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(15, 4.6)); fig.patch.set_facecolor('white')
    for k, (nom, (contour, quoi, serre)) in enumerate(OBJETS.items()):
        m = prisme(contour); me = m.to_mesh(); t = tm.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts))
        assert m.status() == mf.Error.NoError and len(m.decompose()) == 1 and abs(t.extents[2] - H) < 0.01, nom
        t.export(OUT / f'{nom}.stl'); assert tm.load(OUT / f'{nom}.stl').is_watertight, nom     # relu comme le fera le trancheur
        g = t.volume * 1.25e-3; print(f'{nom:20s} {quoi:32s} {t.extents[0]:.0f} × {t.extents[1]:.0f} × {t.extents[2]:.0f} mm   plein : {g:.0f} g   (2 périmètres, 10 % : environ {g * 0.3:.0f} g)')
        ax = fig.add_subplot(1, 5, k + 1, projection='3d')
        ax.add_collection3d(Poly3DCollection(t.vertices[t.faces], facecolor='#5b8bd6', edgecolor='#2d4f8a', linewidth=0.15, alpha=1.0))
        ax.set_xlim(-36, 36); ax.set_ylim(-36, 36); ax.set_zlim(0, 72); ax.set_box_aspect((1, 1, 1)); ax.view_init(28, -55); ax.set_axis_off()
        ax.set_title(f'{quoi}\n60 mm de haut', fontsize=11)
    fig.subplots_adjust(left=0, right=1, top=0.9, bottom=0, wspace=0); fig.savefig(OUT / 'apercu_objets.png', dpi=90); print('ok')
