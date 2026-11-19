"""Aperçu du poignet : monté (pince droite, pince tournée de 90°) et pièces à imprimer. → sortie/apercu_poignet.png"""
import sys, os
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import generer_poignet as P, plan_montage_epaule_outils as PM
from generer_pince import box
C = {'support': '#5b8bd6', 'barre': '#e0602a', 'base': '#c9a35a', 'servo': '#3a3a3a', 'avb': '#bdbdbd', 'pince': '#7fb069'}
AVB = box(-70, -P.FOURCHE_EP / 2, -P.FOURCHE_L / 2, 0, P.FOURCHE_EP / 2, P.FOURCHE_L / 2)
def monte(a):
    pcs = [(AVB, C['avb']), (P.SUPPORT, C['support']), (P.BARRE, C['barre']), (P.SERVO, C['servo']), (P.rouler(P.BASE, a), C['base'])]
    return pcs + [(P.rouler(x, a), c) for x, c in zip(P.pince_complete(-13.1), (C['base'], C['servo'], C['pince'], C['pince'], C['pince'], C['pince']))]
fig = plt.figure(figsize=(18, 11)); fig.patch.set_facecolor('white')
for k, (titre, pcs, vue) in enumerate([('Monté, pince droite', monte(0), (22, -62)), ('Pince tournée de 90°', monte(90), (22, -62)),
                                       ('Support + servo + barre', [(P.SUPPORT, C['support']), (P.BARRE.translate((0, 0, 12)), C['barre']), (P.SERVO.translate((0, 0, 0)), C['servo'])], (25, -40)),
                                       ('Base de la pince, vue de derrière', [(P.BASE, C['base'])], (20, -150))]):
    ax = fig.add_subplot(2, 2, k + 1, projection='3d'); PM.dessiner(ax, pcs, vue=vue, marge=0.6); ax.set_title(titre, fontsize=15, weight='bold')
fig.subplots_adjust(left=0, right=1, top=0.95, bottom=0, hspace=0.05, wspace=0)
fig.savefig(P.OUT / 'apercu_poignet.png', dpi=80); print('ok')
