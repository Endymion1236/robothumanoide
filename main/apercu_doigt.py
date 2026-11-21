"""Aperçu du doigt d'essai : tendu, à moitié plié, plié, et une charnière vue de près. → sortie/apercu_doigt.png"""
import sys, os
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import generer_doigt as D, plan_montage_epaule_outils as PM
C = ['#c9a35a', '#5b8bd6', '#3aa6a6', '#e0602a']
fig = plt.figure(figsize=(18, 11)); fig.patch.set_facecolor('white')
vues = [('Doigt tendu', D.doigt([0, 0, 0]), (20, -65)), ('À moitié plié (45° par charnière)', D.doigt([45, 45, 45]), (12, -80)),
        ('Plié à fond (85° par charnière)', D.doigt([85, 85, 85]), (12, -80)), ('Les 4 pièces, vues de dessous (côté paume)', [D.BASE] + [p.translate((40 + 8 * k + sum(D.LONGUEURS[:k]), 0, 0)) for k, p in enumerate(D.PHALANGES)], (-35, -60))]
for k, (titre, pcs, vue) in enumerate(vues):
    ax = fig.add_subplot(2, 2, k + 1, projection='3d'); PM.dessiner(ax, list(zip(pcs, C)), vue=vue, marge=0.62); ax.set_title(titre, fontsize=15, weight='bold')
fig.subplots_adjust(left=0, right=1, top=0.95, bottom=0, hspace=0.05, wspace=0)
fig.savefig(D.OUT / 'apercu_doigt.png', dpi=80); print('ok')
