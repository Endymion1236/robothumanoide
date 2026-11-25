"""Plan coté du servo Feetech STS3095 (ST-3095-C002) tel que Nicolas l'a mesuré le 25/11/2026, pour qu'il le vérifie AVANT
qu'on dessine le berceau de l'épaule. → sortie/plan_sts3095.png
Les valeurs précédées de « ≈ » sont lues sur ses photos avec réglet (± 1 mm) : elles servent à placer des trous OBLONGS."""
from pathlib import Path
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

OUT = Path(__file__).parent / 'sortie'; OUT.mkdir(exist_ok=True)
L, W, T = 65.0, 30.0, 47.8            # longueur, largeur des faces à palonnier, épaisseur entre ces faces (mesurés)
AXE = 17.9                            # axe depuis le bout côté palonnier (65 − 47,1 mesuré)
D_DISQUE, E_DISQUE, DEP = 29.6, 3.8, 6.8   # disque : diamètre, épaisseur, dessus du disque au-dessus de la face (61,4 hors tout)
D_MOYEU, CERCLE, D_TROU = 13.8, 23.9, 2.7
COIN, RETRAIT = 6.6, 1.0              # logements des têtes de vis côté logo : carrés de 6,6 ; 47,8 − 45,8 = 2 → 1 par face ? (voir texte)
NOIR, ALU, ROUGE, TROU = '#2b2b2b', '#c9ccd1', '#b3262b', '#ffffff'

def cote(ax, x0, y0, x1, y1, texte, decal=0.0, vertical=False, taille=9):
    """Une cote : flèche double entre deux points et texte au milieu."""
    ax.annotate('', (x0, y0), (x1, y1), arrowprops=dict(arrowstyle='<->', color='#1f5fbf', lw=0.9, shrinkA=0, shrinkB=0))
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    ax.text(xm + (decal if vertical else 0), ym + (0 if vertical else decal), texte, color='#1f5fbf', fontsize=taille,
            ha='center', va='center', rotation=90 if vertical else 0, bbox=dict(fc='white', ec='none', pad=0.6))

def face(ax, titre, trous, logo):
    """Une face à palonnier vue de face. x = le long du servo (0 = bout côté palonnier), y = la largeur."""
    ax.add_patch(Rectangle((0, 0), L, W, fc=NOIR, ec='black'))
    if logo:
        for x in (0, L - COIN):
            for y in (0, W - COIN): ax.add_patch(Rectangle((x, y), COIN, COIN, fc='#555555', ec='#888888', lw=0.6)); ax.add_patch(Circle((x + COIN / 2, y + COIN / 2), 1.5, fc='#bbbbbb'))
    ax.add_patch(Circle((AXE, W / 2), D_DISQUE / 2, fc=ALU, ec='#777777', alpha=0.9)); ax.add_patch(Circle((AXE, W / 2), D_MOYEU / 2, fc='#dfe2e6', ec='#777777'))
    for k in range(8):
        import math; a = math.radians(22.5 + 45 * k); ax.add_patch(Circle((AXE + CERCLE / 2 * math.cos(a), W / 2 + CERCLE / 2 * math.sin(a)), D_TROU / 2, fc='#555555'))
    for x, y in trous: ax.add_patch(Circle((x, y), 1.0, fc=TROU, ec='black', lw=0.5))
    cote(ax, 0, -4, L, -4, f'{L:.0f}', decal=0)
    cote(ax, 0, -9, AXE, -9, f'axe à {AXE:.1f}'); cote(ax, AXE, -9, L, -9, '47,1')
    cote(ax, -4, 0, -4, W, f'{W:.0f}', vertical=True)
    cote(ax, AXE - D_DISQUE / 2, W + 4, AXE + D_DISQUE / 2, W + 4, f'disque Ø {D_DISQUE}')
    ax.set_title(titre, fontsize=12, weight='bold'); ax.set_xlim(-10, L + 6); ax.set_ylim(-13, W + 9); ax.set_aspect('equal'); ax.axis('off')

# Côté logo : 2 trous sous l'étiquette (14 du bout à languette, 3,3 des bords), 1 au milieu près du bout (≈ 2,5)
LOGO = [(L - 14.0, 3.3), (L - 14.0, W - 3.3), (L - 2.5, W / 2)]
# Côté opposé : 3 paires à ≈ 2,5 des bords : ≈ 3 du bout côté palonnier (sous le disque), ≈ 39 de ce bout, ≈ 2,5 du bout à languette
OPP = [(x, y) for x in (3.0, 39.0, L - 2.5) for y in (2.5, W - 2.5)]

fig = plt.figure(figsize=(16, 11)); fig.patch.set_facecolor('white')
ax1 = fig.add_axes([0.02, 0.52, 0.47, 0.44]); face(ax1, 'Face du LOGO (palonnier vu de face)', LOGO, True)
ax1.text(L - 14.0, W / 2, '14\ndu bout', color='white', fontsize=8, ha='center', va='center')
ax2 = fig.add_axes([0.52, 0.52, 0.47, 0.44]); face(ax2, 'Face OPPOSÉE au logo (ST-3095-C002)', OPP, False)
ax2.text(39.0, W / 2, '≈ 39', color='white', fontsize=8, ha='center', va='center')

# Côté à bande rouge : x le long du servo, y l'épaisseur (logo en haut)
ax3 = fig.add_axes([0.02, 0.04, 0.6, 0.44])
ax3.add_patch(Rectangle((0, 0), L, T, fc=NOIR, ec='black')); ax3.add_patch(Rectangle((0, T * 0.35), L, T * 0.3, fc=ROUGE))
for x in (0, L - COIN): ax3.add_patch(Rectangle((x, T - 2.0), COIN, 2.0, fc='white', ec='#888888', lw=0.6))
for y0, sens, moyeu in ((T, 1, 1.0), (0, -1, 0.5)):
    base = y0 + sens * (DEP - E_DISQUE)
    ax3.add_patch(Rectangle((AXE - 7, min(y0, base)), 14, abs(base - y0), fc='#9a9da3'))
    ax3.add_patch(Rectangle((AXE - D_DISQUE / 2, min(base, base + sens * E_DISQUE)), D_DISQUE, E_DISQUE, fc=ALU, ec='#777777'))
    top = base + sens * E_DISQUE; ax3.add_patch(Rectangle((AXE - D_MOYEU / 2, min(top, top + sens * moyeu)), D_MOYEU, moyeu, fc='#dfe2e6', ec='#777777'))
ax3.add_patch(Rectangle((22.0, 1.5), 13.2, 3.5, fc='white', ec='black')); ax3.text(28.6, 8.5, 'SVG', color='white', fontsize=9, ha='center')
cote(ax3, L + 4, 0, L + 4, T, '47,8 (45,8 aux 4 coins côté logo)', vertical=True, decal=2.5)
cote(ax3, AXE + 19, -DEP, AXE + 19, T + DEP, '61,4 entre les disques', vertical=True, decal=2.5)
cote(ax3, 0, -11, 22.0, -11, '22'); cote(ax3, 22.0, -11, 35.2, -11, 'prise'); cote(ax3, 35.2, -11, L, -11, '29,8')
ax3.text(AXE, T + DEP + 2.5, 'côté LOGO', ha='center', fontsize=10, weight='bold'); ax3.text(AXE, -DEP - 3.5, 'côté opposé', ha='center', fontsize=10, weight='bold')
ax3.set_title('Côté à BANDE ROUGE (la prise est contre la face opposée au logo)', fontsize=12, weight='bold')
ax3.set_xlim(-6, L + 16); ax3.set_ylim(-15, T + 13); ax3.set_aspect('equal'); ax3.axis('off')

ax4 = fig.add_axes([0.64, 0.04, 0.35, 0.44]); ax4.axis('off')
ax4.text(0, 1, """STS3095, version 12 V — mesures de Nicolas (25/11/2026)

Boîtier 65 × 30 × 47,8 mm · poids 199 g
Axe : 17,9 du bout côté palonnier, centré
Disques Ø 29,6 × 3,8, dessus à 6,8 de la face
  (61,4 entre les deux) ; moyeu Ø 13,8 qui
  dépasse de 1 (logo) et 0,5 (opposé)
8 trous filetés traversants, cercle ≈ Ø 23,9 :
  vis fournies Ø 2,6 × 9 → 4 mm de plastique
  sous la tête (3 mm de vide sous le disque)
Trous du boîtier : vis fournies Ø 2,1 × 4,3
  « ≈ » = lu sur photo, ± 1 mm → trous oblongs
Prises SVG : sur les 2 côtés rouges
Câble fourni : 15 cm

À VÉRIFIER PAR NICOLAS : que tout ressemble
à son servo, surtout la place des trous.""", va='top', fontsize=11.5, family='DejaVu Sans')
fig.savefig(OUT / 'plan_sts3095.png', dpi=90); print('ok')
