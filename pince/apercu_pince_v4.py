"""Image de la pince V4 : sortie/apercu_pince_v4.png (vue de dessus à 3 ouvertures + vue en perspective)."""
import sys, os, math
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import generer_pince as G, generer_pince_v4 as V, plan_montage_epaule_outils as PM
C = {'base': '#dcdcdc', 'servo': '#777', 'mobile': '#e0602a', 'fixe': '#5b8bd6', 'mach': '#7fb069', 'tapis': '#222'}
def scene(d, objet=None):
    pm, mm, tm_ = V.mobile(d)
    s = [(G.BASE, C['base']), (G.SERVO, C['servo']), (G.BRIDE, C['base']), (V.PF, C['fixe']), (V.MACH_F, C['mach']), (V.TAPIS_F, C['tapis']), (pm, C['mobile']), (mm, C['mach']), (tm_, C['tapis'])]
    if objet: s.append((G.cyl(V.XC, V.YF + V.TAPIS + objet / 2, -15, 30, objet, 96), '#f2d21b'))
    return s
fig = plt.figure(figsize=(18, 9.5)); fig.patch.set_facecolor('white')
fig.suptitle('Pince V4, sans engrenages — prototype (bleu : plaque fixe · orange : plaque mobile · vert : les mâchoires de la V3, gardées)', fontsize=15, weight='bold')
for k, (w, titre) in enumerate([(None, 'Fermée à vide : les bouts se touchent'), (53, 'Bas du gobelet : 53 mm'), (72, 'Parallèles : 72 mm'), (90, 'Grande ouverte : 90 mm')]):
    d = V.angle_contact() + 0.3 if w is None else next(x / 10 for x in range(-600, 600) if V.ouverture(x / 10) >= w)
    ax = fig.add_subplot(2, 3, k + 1 if k < 3 else 5, projection='3d'); PM.dessiner(ax, scene(d, w), vue=(90, -90), cadre=(-30, 170, -85, 85, -20, 60), marge=0.56); ax.set_proj_type('ortho'); ax.set_title(titre, fontsize=13)
ax = fig.add_subplot(2, 3, 4, projection='3d'); PM.dessiner(ax, scene(0, 72), vue=(28, -55), cadre=(-30, 170, -85, 85, -25, 60), marge=0.6); ax.set_title('Vue d\'ensemble, gobelet de 72 mm', fontsize=13)
ax = fig.add_subplot(2, 3, 6, projection='3d'); PM.dessiner(ax, [(V.PM.rotate((180, 0, 0)), C['mobile']), (V.PF.rotate((180, 0, 0)).translate((0, 90, 0)), C['fixe'])], vue=(35, -60), marge=0.7); ax.set_title('Les 2 pièces à imprimer (retournées, à plat)', fontsize=13)
fig.subplots_adjust(left=0, right=1, top=0.92, bottom=0.01, wspace=0, hspace=0.08); fig.savefig(G.OUT / 'apercu_pince_v4.png', dpi=95); print('ok')
