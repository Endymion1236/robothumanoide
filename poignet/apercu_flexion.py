"""Aperçu de la flexion du poignet : bras droit, fléchi vers le bas, vers le haut, et pièces à imprimer. → sortie/apercu_flexion.png"""
import sys, os
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import generer_flexion as X, plan_montage_epaule_outils as PM
from generer_epaule import box
C = {'support': '#8e6bbf', 'fourche': '#3aa6a6', 'servo': '#3a3a3a', 'bride': '#e0602a', 'avb': '#bdbdbd', 'suite': '#c9c9c9', 'pince': '#7fb069'}
AVB = box(-70, -X.EP_F / 2, -12, 0, X.EP_F / 2, 12)
def monte(a):
    pcs = [(AVB, C['avb']), (X.SUPPORT, C['support']), (X.BRIDE, C['bride']), (X.SERVO, C['servo'])]
    pcs += [(X.flechir(m, a), C['fourche']) for m in (X.BASSE, X.HAUTE)]
    return pcs + [(X.flechir(m, a), c) for m, c in zip(X.suite(), ['#5b8bd6', '#e0602a', C['servo'], '#c9a35a', '#c9a35a', C['servo']] + [C['pince']] * 4)]
fig = plt.figure(figsize=(18, 11)); fig.patch.set_facecolor('white')
vues = [('Poignet droit', monte(0), (18, -70)), ('Fléchi de 60° vers le bas', monte(-60), (18, -70)), ('Fléchi de 60° vers le haut', monte(60), (18, -70)),
        ('À imprimer : support (violet) et fourche courte (bleu-vert)', [(X.SUPPORT, C['support']), (X.BASSE.translate((25, 0, 0)), C['fourche']), (X.HAUTE.translate((25, 14, 0)), C['fourche']), (X.SERVO, C['servo']), (X.BRIDE, C['bride'])], (28, -60))]
for k, (titre, pcs, vue) in enumerate(vues):
    ax = fig.add_subplot(2, 2, k + 1, projection='3d'); PM.dessiner(ax, pcs, vue=vue, marge=0.6); ax.set_title(titre, fontsize=15, weight='bold')
fig.subplots_adjust(left=0, right=1, top=0.95, bottom=0, hspace=0.05, wspace=0)
fig.savefig(X.OUT / 'apercu_flexion.png', dpi=80); print('ok')
