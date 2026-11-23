"""Illustration de principe : le bras actuel monté sur un buste, avec la tête de poney. → sortie/apercu_buste.png
CE N'EST PAS UN PLAN : le buste n'est pas dessiné. Les longueurs du bras sont les vraies (haut du bras 120 mm, avant-bras 161 mm,
poignet et pince 200 mm) ; l'ossature reprend l'estimation de la feuille de route (profilés 20 × 20, boîte de 20 × 15 cm), mais plus
boîte de 40 cm de haut). Épaule à 34,5 cm de la table : assez bas pour que la pince atteigne la table à plat, donc le bras ne peut
pas pendre tout droit (il fait 48 cm) : au repos, le coude reste plié."""
import sys, os, math
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import numpy as np, manifold3d as mf
import plan_montage_epaule_outils as PM
from pathlib import Path
OUT = Path(ICI) / 'sortie'; OUT.mkdir(exist_ok=True)
# la tête de poney : on reprend ses formes dans tete-poney/apercu_tete_poney.py (seulement les définitions, pas le dessin)
_src = Path(ICI, '..', 'tete-poney', 'apercu_tete_poney.py').read_text(encoding='utf-8'); _ns = {'__file__': str(Path(ICI, '..', 'tete-poney', 'apercu_tete_poney.py'))}
exec(_src[:_src.index('def dessiner(')], _ns)
T = _ns

def boite(x0, y0, z0, x1, y1, z1): return mf.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))
def barre(p, q, w=24.0, h=40.0):
    """Un segment de bras entre deux points (section w × h)."""
    c = lambda r: mf.Manifold.cube((w, h, w), True).translate(r)
    return mf.Manifold.batch_hull([c(p), c(q)])
C = {'alu': '#b8bcc4', 'pied': '#8d9199', 'imprime': '#5b8bd6', 'servo': '#3a3a3a', 'bras': '#7fb069', 'avb': '#9ccc65', 'poignet': '#8e6bbf', 'pince': '#e0602a',
     'tete': '#d9b36c', 'crin': '#f3e6c0', 'fantome': '#dddddd', 'table': '#e9dcc3'}
L, P, H = 200.0, 150.0, 400.0                        # largeur, profondeur, hauteur de l'ossature (mm) : l'estimation de la feuille de route
Z_EP = 345.0                                         # hauteur de l'axe de l'épaule au-dessus de la table

def ossature():
    m = mf.Manifold()
    for x in (-P / 2, P / 2 - 20):
        for y in (-L / 2, L / 2 - 20): m += boite(x, y, 20, x + 20, y + 20, H)                      # 4 montants
    for z in (20, H / 2, H - 20):
        for x in (-P / 2, P / 2 - 20): m += boite(x, -L / 2, z, x + 20, L / 2, z + 20)              # traverses de largeur
        for y in (-L / 2, L / 2 - 20): m += boite(-P / 2, y, z, P / 2, y + 20, z + 20)              # traverses de profondeur
    pied = boite(-175, -10, 0, 175, 10, 20) + boite(-10, -175, 0, 10, 175, 20)                       # pied en croix
    return m, pied

def bras(cote, epaule, coude, flexion, couleurs=True):
    """Un bras : cote = +1 (droit du robot, y négatif) ou −1. Angles en degrés : épaule (0 = bras à l'horizontale vers l'avant,
    −90 = pend), coude et flexion comme dans les programmes."""
    y = -cote * (L / 2 + 75)
    a, ag, t = math.radians(epaule), math.radians(epaule + coude), math.radians(epaule + coude + flexion)
    e = np.array([0.0, y, Z_EP]); c = e + 120 * np.array([math.cos(a), 0, math.sin(a)]); w = c + 161 * np.array([math.cos(ag), 0, math.sin(ag)])
    u = np.array([math.cos(t), 0, math.sin(t)]); n = np.array([-math.sin(t), 0, math.cos(t)]); p = w + 110 * u; bout = w + 200 * u
    col = (lambda k: C[k]) if couleurs else (lambda k: C['fantome'])
    pcs = [(boite(-45, y - 40 if cote > 0 else y - 30, Z_EP + 30, 45, y + 30 if cote > 0 else y + 40, Z_EP + 42) + boite(-45, -cote * L / 2 - (60 if cote > 0 else 0), Z_EP + 30, 45, -cote * L / 2 + (0 if cote > 0 else 60), Z_EP + 42), col('imprime')),   # tablette d'épaule
           (mf.Manifold.cylinder(34, 27, 27, 32).translate((0, y, Z_EP - 4)), col('imprime')),                          # socle tournant, tête en bas
           (boite(-22, y - 14, Z_EP - 16, 22, y + 14, Z_EP + 16), col('servo')),                                         # servo d'épaule
           (barre(e, c), col('bras')), (boite(-18, -14, -14, 18, 14, 14).translate(c), col('servo')),
           (barre(c, w), col('avb')), (boite(-16, -14, -14, 16, 14, 14).translate(w), col('servo')),
           (barre(w + 25 * u, p, 26, 30), col('poignet'))]
    for s in (1, -1):                                                                                                    # les deux mâchoires
        d = np.array([0, s * 42.0, 0]); pcs.append((barre(p + d * 0.4, bout + d, 8, 8), col('pince')))
        pcs.append((mf.Manifold.batch_hull([mf.Manifold.cube((8, 8, 8), True).translate(bout + d + 20 * u + k * 30 * n) for k in (-1, 1)] + [mf.Manifold.cube((8, 8, 8), True).translate(bout + d - 20 * u + k * 30 * n) for k in (-1, 1)]), col('pince')))
    return pcs

def tete():
    place = lambda m: m.translate((35, 0, H + 110))
    return [(place(T['coque'](*[T['boule'](*b) for b in T['CRANE'] + T['CHANFREIN'] + T['BOUT_NEZ'] + T['GANACHE']])), C['tete']), (place(T['COU']), C['tete']),
            (place(T['CRINIERE']), C['crin'])] + [(place(o), C['tete']) for o in T['OREILLES']]

def scene(angles_d, angles_g=None):
    os_, pied = ossature()
    pcs = [(boite(-200, -330, -10, 520, 330, 0), C['table']), (os_, C['alu']), (pied, C['pied'])] + tete() + bras(1, *angles_d)
    return pcs + (bras(-1, *angles_g, couleurs=False) if angles_g else [])

if __name__ == '__main__':
    fig = plt.figure(figsize=(18, 11)); fig.patch.set_facecolor('white')
    vues = [('Au repos : le haut du bras pend, l\'avant-bras à l\'horizontale', scene((-90, 90, 0), (-90, 90, 0)), (14, -52)),
            ('Il prend un objet sur la table, pince à plat', scene((-60, -20, 80), (-90, 90, 0)), (14, -52)),
            ('Vu de face', scene((-90, 90, 0), (-90, 90, 0)), (6, 0)),
            ('Il tend un objet à quelqu\'un', scene((-15, 25, -10), (-90, 90, 0)), (14, -52))]
    for k, (titre, pcs, vue) in enumerate(vues):
        ax = fig.add_subplot(2, 2, k + 1, projection='3d'); PM.dessiner(ax, pcs, vue=vue, cadre=(-200, 520, -360, 360, -10, 720), marge=0.6); ax.set_title(titre, fontsize=15, weight='bold')
    fig.text(0.5, 0.012, 'Illustration de principe, pas un plan. En couleur : le bras actuel (haut du bras 12 cm, avant-bras 16 cm, poignet et pince 20 cm). En gris clair : le deuxième bras, plus tard.',
             ha='center', fontsize=12)
    fig.subplots_adjust(left=0, right=1, top=0.95, bottom=0.03, hspace=0.06, wspace=0)
    fig.savefig(OUT / 'apercu_buste.png', dpi=80); print('ok')
