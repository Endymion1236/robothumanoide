"""Vue de dessus de la pince bien montée, avec les trous de chaque articulation (à lancer après generer_pince.py)."""
import sys; import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import plan_montage as PM, generer_pince as G
fig = plt.figure(figsize=(13, 11)); fig.patch.set_facecolor('white')
ax = fig.add_axes([0, 0, 1, 0.9], projection='3d')
P = PM.P
pcs = [(PM.BASE, PM.pale(PM.COUL['base'])), (PM.SERVO, '#777'), (PM.BRIDE, PM.pale(PM.COUL['bride']))]
pcs += [(P[n], PM.COUL[n]) for n in ('engrenage A', 'engrenage B', 'doigt +Y', 'doigt -Y', 'bras libre +Y', 'bras libre -Y')]
PM.dessiner(ax, pcs, vue=(90, -90), cadre=(-20, 150, -95, 95, -20, 60), marge=0.58)
z = G.Z_LIBRE + 10
for k in (1, -1):
    PM.etiquette(ax, (*PM.Q1[k], z), 'trou AVANT du doigt\n= bout du bras de l\'engrenage\n(M3×16 + écrou dessous)', (150, 70 * k), '#c0392b')
    PM.etiquette(ax, (*PM.Q2[k], z), 'trou ARRIÈRE du doigt\n= bout du bras libre\n(M3×8 dans le bouchon)', (60, 95 * k), '#6a2c91')
    PM.etiquette(ax, (*PM.PIV[k], z), 'poteau du\nbras libre', (-80, 50 * k), '#333')
PM.etiquette(ax, (G.AX, G.AY, z), 'A', (0, 60), '#1f4f8a'); PM.etiquette(ax, (G.AX, -G.AY, z), 'B', (0, -60), '#1f4f8a')
fig.text(0.03, 0.95, 'Pince V3 vue de dessus, bien montée (mi-ouverture)', fontsize=20, weight='bold')
fig.text(0.03, 0.915, 'De chaque côté : bras de l\'engrenage et bras libre PARALLÈLES, le bras libre DÉCALÉ vers l\'arrière et l\'extérieur → les mâchoires restent parallèles.', fontsize=13)
fig.savefig(G.OUT / 'vue_dessus_montee.png', dpi=100)
print('ok')
