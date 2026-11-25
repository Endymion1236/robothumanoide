"""Aperçu du banc d'essai du doigt motorisé → sortie/apercu_banc_doigt.png"""
import sys, os
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import generer_banc_doigt as B, plan_montage_epaule_outils as PM
C = {'banc': '#7fb069', 'console': '#2f9fae', 'etrier': '#9b6fd0', 'servo': '#3a3a3a', 'pal': '#f2f2f2', 'poulie': '#e0602a',
     'doigt': ['#c9a35a', '#5b8bd6', '#3aa6a6', '#d6a62e'], 'fil': '#d0302a'}
def scene(angles, rot_poulie=0.0, eclate=0.0):
    pcs = [(B.BANC, C['banc']), (B.CONSOLE.translate((0, 0, 1.6 * eclate)), C['console']), (B.ETRIER.translate((0, -eclate, 0)), C['etrier']),
           (B.SERVO.translate((0, 0.8 * eclate, 0)), C['servo']), (B.PAL.translate((0, 1.2 * eclate, 0)), C['pal']),
           (B.poulie_a(rot_poulie).translate((0, 1.8 * eclate, 0)), C['poulie'])]
    pcs += [(p.translate((0, 0, 1.6 * eclate)), c) for p, c in zip(B.doigt_a(angles), C['doigt'])]
    if not eclate: pcs += [(B.tige(a, b, 0.8), C['fil']) for a, b in B.fils()]
    return pcs
fig = plt.figure(figsize=(18, 11)); fig.patch.set_facecolor('white')
vues = [('Doigt tendu', scene([0, 0, 0]), (24, 62)), ('Doigt plié : le fil du dessous s\'enroule, celui du dessus se déroule', scene([60, 60, 60], 150), (12, 78)),
        ('Les pièces écartées', scene([0, 0, 0], eclate=22), (28, -50)), ('Vu de dessus : les deux fils', scene([0, 0, 0]), (88, -90))]
for k, (titre, pcs, vue) in enumerate(vues):
    ax = fig.add_subplot(2, 2, k + 1, projection='3d'); PM.dessiner(ax, pcs, vue=vue, marge=0.62); ax.set_title(titre, fontsize=14, weight='bold')
fig.text(0.5, 0.01, 'Vert : banc · bleu-vert : console · violet : étrier · noir : servo SCS0009 · orange : poulie · rouge : les deux fils. Prototype, rien n\'est imprimé.',
         ha='center', fontsize=12)
fig.subplots_adjust(left=0, right=1, top=0.95, bottom=0.03, hspace=0.06, wspace=0)
fig.savefig(B.OUT / 'apercu_banc_doigt.png', dpi=80); print('ok')
