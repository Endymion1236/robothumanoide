"""Fabrique la feuille des 4 marqueurs à imprimer (A4) : sortie/marqueurs_table.pdf.
À imprimer À 100 % (« taille réelle », sans « ajuster à la page ») : le trait de contrôle doit mesurer 100 mm."""
from pathlib import Path
import cv2, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import table as T

OUT = Path(__file__).with_name('sortie'); OUT.mkdir(exist_ok=True)
COTE = 60.0                                            # côté du carré noir, en mm
NOMS = {0: 'PRÈS, À GAUCHE', 1: 'PRÈS, À DROITE', 2: 'AU FOND, À DROITE', 3: 'AU FOND, À GAUCHE'}
fig = plt.figure(figsize=(210 / 25.4, 297 / 25.4)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 210); ax.set_ylim(0, 297); ax.axis('off')
ax.text(105, 285, 'Marqueurs de la table de Câlin', ha='center', fontsize=16, weight='bold')
ax.text(105, 277, 'Imprimer à 100 % (taille réelle). Découper chaque carré en gardant sa marge blanche.', ha='center', fontsize=10)
for k, i in enumerate(T.IDS):
    x, y = 30 + (k % 2) * 95, 175 - (k // 2) * 105
    img = cv2.aruco.generateImageMarker(T.DICO, i, 600)
    ax.add_patch(Rectangle((x - 12, y - 22), COTE + 24, COTE + 36, fill=False, ls='--', lw=0.6, ec='#888'))       # trait de coupe
    ax.imshow(img, cmap='gray', extent=(x, x + COTE, y, y + COTE), interpolation='nearest', zorder=3)
    ax.text(x + COTE / 2, y - 8, f'n° {i} — {NOMS[i]}', ha='center', fontsize=10, weight='bold')
    ax.text(x + COTE / 2, y - 15, 'vu de derrière le bras · ce texte vers le robot', ha='center', fontsize=7)
ax.plot([55, 155], [28, 28], color='k', lw=1.5); [ax.plot([v, v], [25, 31], color='k', lw=1.5) for v in (55, 155)]
ax.text(105, 20, 'Contrôle : ce trait doit mesurer exactement 100 mm à la règle.', ha='center', fontsize=10)
ax.set_aspect('equal'); fig.savefig(OUT / 'marqueurs_table.pdf'); fig.savefig(OUT / 'marqueurs_table.png', dpi=100); print('ok')
