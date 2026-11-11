"""Plan de montage illustré de la pince (8 étapes). À lancer après generer_pince.py.
À chaque étape : pièces déjà montées en gris, pièces ajoutées en couleur, et repères :
inserts M3 (rouge), roulements 623 (bleu), vis (noir, dessinées au-dessus de leur trou)."""
import math
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import generer_pince as G

LUM = np.array([0.4, -0.5, 0.75]); LUM /= np.linalg.norm(LUM)
TH = (G.TH_FERME + G.TH_OUVERT) / 2                    # montage à mi-ouverture (servo à 2048)
P = G.pose(TH)
c, s_ = math.cos(math.radians(TH)), math.sin(math.radians(TH))
Q1 = {1: (G.AX + G.L_BRAS * c, G.AY + G.L_BRAS * s_), -1: (G.AX + G.L_BRAS * c, -(G.AY + G.L_BRAS * s_))}
Q2 = {k: (v[0] - G.DECAL, v[1]) for k, v in Q1.items()}
P2 = {1: (G.AX - G.DECAL + 0, G.AY), -1: (G.AX - G.DECAL, -G.AY)}
cyl = G.cyl

def insert(x, y, z): return cyl(x, y, z + 8, z + 13.7, 4.6, 24)   # dessiné au-dessus de son trou
def roulement(x, y, z, h=12): return cyl(x, y, z + h, z + h + 4, 10, 32) - cyl(x, y, z + h - 0.1, z + h + 4.1, 3, 16)  # au-dessus
def vis(x, y, z, longueur, d=3.0):
    """Vis dessinée AU-DESSUS de son trou (tête en haut), pour montrer où elle va."""
    return cyl(x, y, z + 6, z + 6 + longueur, d, 16) + cyl(x, y, z + 6 + longueur, z + 8.5 + longueur, d * 1.8, 20)

y_pil = (G.SY0 - G.JEU - 3 - 4, G.SY1 + G.JEU + 3 + 4)
INSERTS_BASE = [insert(G.BRIDE_X0 + 5, y, G.BRIDE_Z) for y in y_pil] + \
               [insert(G.AX, -G.AY, G.Z0), insert(*P2[-1], G.Z_LIBRE)]
INSERT_BRIDE = insert(*P2[1], G.Z_LIBRE)
VIS_BRIDE = [vis(G.BRIDE_X0 + 5, y, G.H_HAUT + 4, 10) for y in y_pil]
VIS_A = [vis(G.AX + G.CERCLE_TROUS / 2 * math.cos(math.radians(45 + 90 * k + TH)),
             G.AY + G.CERCLE_TROUS / 2 * math.sin(math.radians(45 + 90 * k + TH)), G.Z0 + G.EP_ENG, 8, 2.5) for k in range(4)]
ROUL_B = roulement(G.AX, -G.AY, G.Z0); VIS_B = vis(G.AX, -G.AY, G.Z0 + G.EP_ENG, 10)
ROUL_LIBRES = [roulement(*P2[k], G.Z_LIBRE) for k in (1, -1)]; VIS_LIBRES = [vis(*P2[k], G.Z_LIBRE + G.EP_LIBRE, 10) for k in (1, -1)]
ROUL_DOIGTS = [roulement(*q[k], G.Z_DOIGT) for q in (Q1, Q2) for k in (1, -1)]
VIS_DOIGTS = [vis(*Q2[k], G.Z_LIBRE + G.EP_LIBRE, 12) for k in (1, -1)] + [vis(*Q1[k], G.Z_DOIGT + G.EP_DOIGT, 12) for k in (1, -1)]

GRIS, VERT, ORANGE, VIOLET, ROUGE, NOIR, BLEU, ROSE = '#cfcfcf', '#7fbf6a', '#e1a64a', '#b57cc4', '#d0473c', '#2b2b2b', '#3b7dd8', '#e6403a'
ETAPES = [
 ('1. Inserts M3 à chaud', 'Base : 4 inserts (2 piliers, poteau de l\'engrenage B,\npoteau du bras libre −Y). Bride : 1 insert sur son pivot.\nFer à 200 °C (PLA) / 230 °C (PETG), bien droit.',
  [('base', G.BASE, VERT), ('bride (à côté)', G.BRIDE.translate((0, 0, 35)), VERT)] + [('i', m, ROSE) for m in INSERTS_BASE] + [('i', INSERT_BRIDE.translate((0, 0, 35)), ROSE)]),
 ('2. Servo dans la base', 'Servo DÉJÀ réglé seul sur la carte : n° 4,\nbutées 1663 / 2433, laissé à 2048.\nCâble par une des fenêtres latérales.',
  [('base', G.BASE, GRIS), ('servo', G.SERVO, NOIR)]),
 ('3. Bride', '2 vis M3 × 10. Serrer à tour de rôle :\nelle appuie sur le servo avant de toucher\nles piliers (0,5 mm de serrage).',
  [('base', G.BASE, GRIS), ('servo', G.SERVO, '#555'), ('bride', G.BRIDE, VERT)] + [('v', m, NOIR) for m in VIS_BRIDE]),
 ('4. Roulements 623', 'Enfoncer au doigt (serré) : 1 sous l\'engrenage B,\n1 sous chaque bras libre, 2 dans chaque doigt.\nPièces écartées ; chaque roulement est au-dessus de son logement.',
  [('base', G.BASE, GRIS), ('servo', G.SERVO, '#555'), ('bride', G.BRIDE, GRIS),
   ('B', P['engrenage B'].translate((0, 0, 40)), ORANGE), ('rb', ROUL_B.translate((0, 0, 40)), BLEU)]
  + [(n, P[n].translate((0, 0, 55)), VIOLET) for n in ('bras libre +Y', 'bras libre -Y')] + [('r', m.translate((0, 0, 55)), BLEU) for m in ROUL_LIBRES]
  + [(n, P[n].translate((0, 0, 70)), ROUGE) for n in ('doigt +Y', 'doigt -Y')] + [('r', m.translate((0, 0, 70)), BLEU) for m in ROUL_DOIGTS]),
 ('5. Engrenages', 'A sur le palonnier : 4 vis M2,5 × 8, mâchoires\nécartées de 71 mm (servo à 2048). B sur son poteau :\nrondelle + M3 × 10. Bras bien symétriques.',
  [('base', G.BASE, GRIS), ('servo', G.SERVO, '#555'), ('bride', G.BRIDE, GRIS), ('A', P['engrenage A'], ORANGE), ('B', P['engrenage B'], ORANGE)]
  + [('v', m, NOIR) for m in VIS_A + [VIS_B]]),
 ('6. Bras libres', 'Côté +Y sur le pivot de la bride, côté −Y sur\nle poteau de la base : rondelle + M3 × 10.\nIls doivent tourner librement.',
  [('base', G.BASE, GRIS), ('servo', G.SERVO, '#555'), ('bride', G.BRIDE, GRIS), ('A', P['engrenage A'], GRIS), ('B', P['engrenage B'], GRIS),
   ('l1', P['bras libre +Y'], VIOLET), ('l2', P['bras libre -Y'], VIOLET)] + [('v', m, NOIR) for m in VIS_LIBRES]),
 ('7. Doigts', 'Chaque doigt relie le bout du bras moteur (dessous)\net le bout du bras libre (dessus) : 2 vis M3 × 12\n+ écrou frein par doigt, rondelles entre les couches.',
  [('base', G.BASE, GRIS), ('servo', G.SERVO, '#555'), ('bride', G.BRIDE, GRIS)] + [(n, P[n], GRIS) for n in ('engrenage A', 'engrenage B', 'bras libre +Y', 'bras libre -Y')]
  + [(n, P[n], ROUGE) for n in ('doigt +Y', 'doigt -Y')] + [('v', m, NOIR) for m in VIS_DOIGTS]),
 ('8. Essai à la main, puis sur l\'avant-bras', 'Hors tension : ouvrir et fermer à la main, sans point dur.\nPuis enfiler le manchon sur le bout de l\'avant-bras :\nles 2 vis M3 × 30 de l\'entretoise traversent le manchon.',
  [('base', G.BASE, VERT), ('servo', G.SERVO, '#555'), ('bride', G.BRIDE, VERT)] + [(n, m, c_) for (n, m), c_ in zip(P.items(), (ORANGE, ORANGE, VIOLET, VIOLET, ROUGE, ROUGE))]
  + [('avant-bras', G.AVB, '#397c92')]),
]

def dessiner(ax, pieces, titre, texte):
    for _, m, coul in pieces:
        t = G.mesh(m); base = np.array(matplotlib.colors.to_rgb(coul))
        k = 0.5 + 0.5 * np.clip(t.face_normals @ LUM, 0, 1)
        ax.add_collection3d(Poly3DCollection(t.vertices[t.faces], facecolors=np.clip(base * k[:, None], 0, 1), linewidth=0))
    tout = np.vstack([G.mesh(m).vertices for _, m, _ in pieces]); mi, ma = tout.min(0), tout.max(0)
    centre, demi = (mi + ma) / 2, (ma - mi).max() / 2 * 1.0
    ax.set(xlim=(centre[0] - demi, centre[0] + demi), ylim=(centre[1] - demi, centre[1] + demi), zlim=(centre[2] - demi, centre[2] + demi))
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off()
    ax.view_init(elev=30, azim=-48); ax.set_title(titre, fontsize=14, weight='bold', loc='left', pad=62)
    ax.text2D(0.0, 1.0, texte, transform=ax.transAxes, fontsize=11, va='bottom')

if __name__ == '__main__':
    for n_fig, morceau in enumerate((ETAPES[:4], ETAPES[4:])):
        fig = plt.figure(figsize=(14, 14)); fig.patch.set_facecolor('#f7f6f2')
        fig.suptitle(f'Pince V2 — plan de montage ({n_fig + 1}/2)', fontsize=15, weight='bold')
        for k, (titre, texte, pieces) in enumerate(morceau):
            dessiner(fig.add_subplot(2, 2, k + 1, projection='3d'), pieces, titre, texte)
        fig.text(0.5, 0.012, 'Couleur : ce qu\'on monte à cette étape · gris : déjà monté · rouge vif : inserts M3 · bleu : roulements 623 · '
                 'noir : vis · inserts, roulements et vis sont dessinés juste au-dessus de leur trou', ha='center', fontsize=10)
        fig.subplots_adjust(left=0.0, right=1.0, top=0.88, bottom=0.04, wspace=0.0, hspace=0.22)
        fig.savefig(G.OUT / f'plan_montage_{n_fig + 1}.png', dpi=110)
    print('ok')
