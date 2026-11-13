"""Plan de montage illustré de la pince : une page par étape (PDF + PNG), à lancer après generer_pince.py.
Chaque page : grand dessin à gauche avec étiquettes fléchées, à droite « Il te faut » et « Ce qu'il faut faire ».
Les pièces déjà montées sont pâles ; la visserie est dessinée écartée, au-dessus (ou au-dessous) de sa place."""
import math, textwrap
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import manifold3d as mf
import generer_pince as G

cyl = G.cyl
LUM = np.array([0.4, -0.5, 0.75]); LUM /= np.linalg.norm(LUM)
TH = (G.TH_FERME + G.TH_OUVERT) / 2                       # servo à 2048
P = G.pose(TH)
c, s_ = math.cos(math.radians(TH)), math.sin(math.radians(TH))
Q1 = {k: (G.AX + G.L_BRAS * c, k * (G.AY + G.L_BRAS * s_)) for k in (1, -1)}     # bout des bras des engrenages
Q2 = {k: (Q1[k][0] - G.DECAL, Q1[k][1]) for k in (1, -1)}                         # bout des bras libres
PIV = {1: G.P_LIBRE[0], -1: G.P_LIBRE[1]}                                          # pivots des bras libres
ENTRE_TROUS = 2 * Q1[1][1]
ECART = ENTRE_TROUS - 2 * G.E_DOIGT
Y_PIL = (G.SY0 - G.JEU - 3 - 4, G.SY1 + G.JEU + 3 + 4)

# ---- couleurs : une par pièce, gardée d'un bout à l'autre ----
COUL = {'base': '#6fae5c', 'bride': '#9fd08f', 'servo': '#3a3a3a', 'engrenage A': '#3f86d6', 'engrenage B': '#2a5ea8',
        'bras libre +Y': '#a86cc0', 'bras libre -Y': '#a86cc0', 'doigt +Y': '#e2783a', 'doigt -Y': '#e2783a', 'avant-bras': '#4f8fa3'}
LAITON, ACIER, NOIR, RONDELLE = '#d1a23a', '#9aa7b3', '#1e1e1e', '#c9c9c9'

# ---- visserie (dessinée) ----
def insert(x, y, z):   return cyl(x, y, z, z + 5.7, 4.6, 24) - cyl(x, y, z - .1, z + 5.8, 2.6, 12)
def roulement(x, y, z): return cyl(x, y, z, z + 4, 10, 32) - cyl(x, y, z - .1, z + 4.1, 3, 16)
def rondelle(x, y, z):  return cyl(x, y, z, z + 0.6, 7, 24) - cyl(x, y, z - .1, z + .7, 3.2, 12)
def ecrou(x, y, z):     return cyl(x, y, z, z + 4, 6.4, 6) - cyl(x, y, z - .1, z + 4.1, 3, 12)
def vis(x, y, z_pointe, longueur, d=3.0):
    """Vis verticale, tête en haut ; z_pointe = bas de la tige."""
    return cyl(x, y, z_pointe, z_pointe + longueur, d, 16) + cyl(x, y, z_pointe + longueur, z_pointe + longueur + d, d * 1.8, 20)

def pale(coul, k=0.62):
    r = np.array(matplotlib.colors.to_rgb(coul)); return tuple(r + (1 - r) * k)

def dessiner(ax, pieces, vue=(28, -50), cadre=None, marge=1.08):
    """pieces : liste (manifold, couleur). cadre : (xmin,xmax,ymin,ymax,zmin,zmax) sinon automatique."""
    tout, faces, couleurs = [], [], []
    for m, coul in pieces:                       # UNE seule collection : chaque face est rangée en profondeur
        t = G.mesh(m); base = np.array(matplotlib.colors.to_rgb(coul)); tout.append(t.vertices)
        k = 0.45 + 0.55 * np.clip(t.face_normals @ LUM, 0, 1)
        faces.append(t.vertices[t.faces]); couleurs.append(np.clip(base * k[:, None], 0, 1))
    ax.add_collection3d(Poly3DCollection(np.concatenate(faces), facecolors=np.concatenate(couleurs), linewidth=0))
    if cadre is None:
        v = np.vstack(tout); mi, ma = v.min(0), v.max(0)
    else:
        mi, ma = np.array(cadre[::2], float), np.array(cadre[1::2], float)
    centre, demi = (mi + ma) / 2, (ma - mi).max() / 2 * marge
    ax.set(xlim=(centre[0] - demi, centre[0] + demi), ylim=(centre[1] - demi, centre[1] + demi), zlim=(centre[2] - demi, centre[2] + demi))
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.view_init(elev=vue[0], azim=vue[1])
    if vue[0] == 90: ax.set_proj_type('ortho')

def etiquette(ax, xyz, texte, decal, coul='#111'):
    """Flèche depuis le texte (décalé de `decal` points) vers le point 3D xyz."""
    x2, y2, _ = proj3d.proj_transform(*xyz, ax.get_proj())
    ax.annotate(texte, xy=(x2, y2), xytext=decal, textcoords='offset points', fontsize=12, color=coul, weight='bold',
                ha='center', va='center', bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=coul, lw=1.2),
                arrowprops=dict(arrowstyle='-|>', color=coul, lw=1.6, shrinkA=2, shrinkB=1), zorder=50)

# ---- pièces fixes (positions de montage) ----
BASE, BRIDE, SERVO, AVB = G.BASE, G.BRIDE, G.SERVO, G.AVB
def fixe(pales=('base', 'servo', 'bride')):
    d = {'base': BASE, 'servo': SERVO, 'bride': BRIDE}
    return [(d[n], pale(COUL[n], 0.55 if n == 'servo' else 0.62)) for n in pales]
def mobile(noms, pales=True): return [(P[n], pale(COUL[n]) if pales else COUL[n]) for n in noms]

ETAPES = []
def etape(titre, il_faut, faire, attention=None):
    def deco(f): ETAPES.append((titre, il_faut, faire, attention, f)); return f
    return deco

# ===================== page 0 : les pièces =====================
def page_pieces(pdf, n):
    fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
    fig.suptitle('Pince V2 — les pièces (regarde-les bien avant de commencer)', fontsize=20, weight='bold', y=0.985)
    liste = [('Base', BASE, COUL['base'], '× 1'), ('Bride', BRIDE, COUL['bride'], '× 1'),
             ('Engrenage A\n(sur le servo)', G.EA, COUL['engrenage A'], '× 1'), ('Engrenage B', G.EB, COUL['engrenage B'], '× 1'),
             ('Bras libres', G.BL[1] + G.BL[-1].translate((0, -8, 0)), COUL['bras libre +Y'], '× 2'),
             ('Doigts + 2 bouchons', G.DG[1] + G.DG[-1].translate((0, -20, 0)), COUL['doigt +Y'], '× 2')]
    for k, (nom, m, coul, qte) in enumerate(liste):
        ax = fig.add_subplot(3, 4, k + 1, projection='3d'); dessiner(ax, [(m, coul)], marge=0.75)
        ax.set_title(f'{nom}  {qte}', fontsize=15, weight='bold', color=coul)
    vis_liste = [
        ('Inserts M3\n(laiton)', insert(0, 0, 0), LAITON, '× 5'),
        ('Roulements 623', roulement(0, 0, 0), ACIER, '× 7'),
        ('Vis M3 × 10  × 5\n+ vis M3 × 8', vis(0, 0, 0, 10) + vis(9, 0, 0, 8), NOIR, '× 2'),
        ('Vis M3 × 16\n(14 à 20 ok)', vis(0, 0, 0, 16), NOIR, '× 2'),
        ('Écrous frein M3', ecrou(0, 0, 0), '#555', '× 2'),
        ('Rondelles M3', rondelle(0, 0, 0), RONDELLE, '× 4'),
    ]
    for k, (nom, m, coul, qte) in enumerate(vis_liste):
        ax = fig.add_subplot(3, 4, 7 + k, projection='3d'); dessiner(ax, [(m, coul)], cadre=(-8, 8, -8, 8, -2, 22), marge=0.9)
        ax.set_title(f'{nom}  {qte}', fontsize=14, weight='bold')
    fig.text(0.04, 0.035, 'Et aussi : les 4 petites vis M2,5 × 8 fournies avec le servo, et les 2 vis M3 × 30 du bout de l\'avant-bras (déjà en place).\n'
             'Couleurs : chaque pièce garde la même couleur dans tout le plan. Une pièce pâle = déjà montée aux étapes d\'avant.',
             fontsize=13)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.09, hspace=0.3, wspace=0.02)
    fig.savefig(G.OUT / f'plan_montage_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)

# ===================== les étapes =====================
@etape('Régler le servo, tout seul', ['le servo de la pince', 'la carte Waveshare + l\'alimentation 12 V', 'le logiciel FD'],
       ['Branche UN SEUL servo sur la carte (rien d\'autre sur le bus).',
        'Dans FD : change son numéro (ID) de 1 à 4.',
        'Butée mini (Min Angle Limit) = 1663, butée maxi (Max Angle Limit) = 2433. Enregistre.',
        'Mets-le en position 2048 (le milieu). Laisse-le là.',
        'Coupe l\'alimentation et débranche-le.'],
       'Toujours régler AVANT de visser quoi que ce soit dessus : un servo sans butées peut casser la pince.')
def e_servo(ax):
    dessiner(ax, [(SERVO, COUL['servo'])], vue=(30, -50), marge=0.8)
    etiquette(ax, (G.AX, G.AY, G.H_BAS + G.PAL_H), 'palonnier\n(le disque qui tourne)', (110, 60))
    etiquette(ax, (G.X0S + 5, G.SY1, 14), 'câble', (-90, -40))

@etape('Les inserts à chaud', ['la base', 'la bride', '5 inserts M3', 'le fer à souder'],
       ['Fer à 200 °C pour du PLA (230 °C pour du PETG).',
        'Pose l\'insert debout sur son trou (côté le plus étroit en bas).',
        'Appuie doucement avec la pointe du fer : il s\'enfonce tout seul en 5 à 10 s.',
        'Arrête quand il est au ras du dessus. Garde-le bien droit.',
        '4 dans la base (rouges ici), 1 dans la bride.'],
       'Si un insert part de travers, ressors-le tout de suite au fer et recommence.')
def e_inserts(ax):
    dz = 22
    pcs = [(BASE, COUL['base']), (BRIDE.translate((0, 0, dz)), COUL['bride'])]
    trous = [(G.BRIDE_X0 + 5, y, G.BRIDE_Z) for y in Y_PIL] + [(G.AX, -G.AY, G.Z0), (*PIV[-1], G.Z_LIBRE)]
    pcs += [(insert(x, y, z + 7), LAITON) for x, y, z in trous] + [(insert(*PIV[1], G.Z_LIBRE + dz + 7), LAITON)]
    dessiner(ax, pcs, vue=(32, -55), marge=0.9)
    for x, y, z in trous: ax.plot([x, x], [y, y], [z, z + 7], ls=':', color='#7a5a00', lw=2, zorder=40)
    ax.plot([PIV[1][0]] * 2, [PIV[1][1]] * 2, [G.Z_LIBRE + dz, G.Z_LIBRE + dz + 7], ls=':', color='#7a5a00', lw=2, zorder=40)
    etiquette(ax, (G.AX, -G.AY, G.Z0 + 12), 'poteau de\nl\'engrenage B', (120, -10))
    etiquette(ax, (*PIV[-1], G.Z_LIBRE + 12), 'poteau du\nbras libre', (60, -95))
    etiquette(ax, (G.BRIDE_X0 + 5, Y_PIL[0], G.BRIDE_Z + 12), 'pilier', (-80, -60))
    etiquette(ax, (G.BRIDE_X0 + 5, Y_PIL[1], G.BRIDE_Z + 12), 'pilier', (-110, 0))
    etiquette(ax, (*PIV[1], G.Z_LIBRE + dz + 12), 'bride : 1 insert\nsur son pivot', (-60, 70))

@etape('Le servo dans la base', ['la base', 'le servo réglé'],
       ['Le palonnier (le disque) va côté pinces, vers l\'avant, et en haut.',
        'Fais passer le câble par une des deux fenêtres sur les côtés.',
        'Pose le servo au fond de son logement : il doit être bien à plat.',
        'Ne tourne pas le palonnier : il doit rester à 2048.'])
def e_servo_base(ax):
    dessiner(ax, [(BASE, pale(COUL['base'])), (SERVO.translate((0, 0, 30)), COUL['servo'])], vue=(28, -50), marge=0.9)
    etiquette(ax, (G.AX, G.AY, G.H_BAS + G.PAL_H + 30), 'palonnier vers l\'avant', (100, 50))
    etiquette(ax, (G.X0S + 23, G.SY1 + 3, 8), 'fenêtre\npour le câble', (-110, -40))

@etape('La bride', ['la bride (avec son insert)', '2 vis M3 × 10'],
       ['Pose la bride sur le dessus du servo : vu de dessus, son pivot rond est aligné avec le palonnier.',
        'Ses 2 trous tombent sur les 2 piliers.',
        'Visse les 2 vis M3 × 10 un peu chacune, à tour de rôle.',
        'Serre jusqu\'à ce que le servo ne bouge plus. Pas plus : c\'est du plastique.'],
       'C\'est normal qu\'il reste un tout petit jour (0,5 mm) sous la bride : c\'est ce qui serre le servo.')
def e_bride(ax):
    dz = 18
    pcs = fixe(('base', 'servo')) + [(BRIDE.translate((0, 0, dz)), COUL['bride'])]
    pcs += [(vis(G.BRIDE_X0 + 5, y, G.H_HAUT + 4 + dz + 8, 10), NOIR) for y in Y_PIL]
    dessiner(ax, pcs, vue=(30, -50), marge=0.9)
    etiquette(ax, (G.BRIDE_X0 + 5, Y_PIL[1], G.H_HAUT + dz + 26), 'vis M3 × 10', (-90, 40))
    etiquette(ax, (G.BRIDE_X0 + 5, Y_PIL[0], G.H_HAUT + dz + 26), 'vis M3 × 10', (90, 50))
    etiquette(ax, (*PIV[1], G.Z_LIBRE + dz), 'pivot', (90, -10))

@etape('Les 7 roulements et les 2 bouchons', ['l\'engrenage B', 'les 2 bras libres', 'les 2 doigts', '7 roulements 623', '2 bouchons imprimés (pince_bouchon_doigt)'],
       ['Ils s\'enfoncent en force, à la main ou en appuyant sur la table.',
        'Engrenage B : 1 roulement, par-DESSOUS, au fond de son logement.',
        'Bras libres : 2 roulements chacun, un à CHAQUE bout, par-DESSOUS.',
        'Doigts : 1 roulement dans le trou AVANT (près de la mâchoire), au ras des deux faces.',
        'Doigts, trou ARRIÈRE : le bouchon imprimé, au ras des deux faces (une goutte de colle s\'il est lâche).',
        'Le roulement doit être bien à plat, pas de travers.'],
       'Trop dur ? Un coup de lime ou de papier de verre dans le trou. Trop lâche ? Une goutte de colle cyanoacrylate sur le bord extérieur (jamais dedans).')
def e_roulements(ax):
    pcs, rang = [], 0
    def place(m, x, y): return m.translate((x, y, 0))
    eb = G.EB.translate((-G.AX, G.AY, -G.Z0))                  # engrenage B ramené vers l'origine
    pcs += [(place(eb, 0, 0), COUL['engrenage B']), (roulement(G.AX - G.AX, -G.AY + G.AY, -14), ACIER)]
    for k, s in enumerate((1, -1)):
        bl = G.BL[s].translate((-PIV[s][0], -PIV[s][1], -G.Z_LIBRE)).translate((0, 45 + 22 * k, 0))
        pcs += [(bl, COUL['bras libre +Y']), (roulement(0, 45 + 22 * k, -14), ACIER), (roulement(G.L_BRAS, 45 + 22 * k, -14), ACIER)]
    for k, s in enumerate((1, -1)):
        q1 = (G.AX + G.L_BRAS, s * G.AY); dg = G.DG[s].translate((-q1[0], -q1[1], -G.Z_DOIGT)).translate((95, 10 + 55 * k, 0))
        pcs += [(dg, COUL['doigt +Y']), (roulement(95, 10 + 55 * k, 12), ACIER),
                (G.bouchon_doigt().translate((95 - G.DECAL, 10 + 55 * k, 12)), COUL['bride'])]
    dessiner(ax, pcs, vue=(35, -60), marge=0.75)
    etiquette(ax, (0, 0, -12), 'par-dessous', (-80, -50))
    etiquette(ax, (0, 45, -12), 'par-dessous', (-90, -40))
    etiquette(ax, (95, 10, 16), '1 roulement\nau trou avant', (80, -70))
    etiquette(ax, (95 - G.DECAL, 10, 16), 'bouchon au\ntrou arrière', (-30, -90))
    etiquette(ax, (15, 0, 6), 'engrenage B', (-40, 80))
    etiquette(ax, (30, 67, 5), 'bras libres', (-10, 80))

@etape('Les engrenages', ['l\'engrenage A', 'l\'engrenage B (avec son roulement)', '4 petites vis M2,5 × 8 du servo',
       '1 vis M3 × 10', 'un pied à coulisse'],
       ['Pas besoin de brancher le servo pour cette étape.',
        'Pose l\'engrenage B sur son poteau, SANS vis.',
        'Pose l\'engrenage A sur le palonnier : ses dents entrent dans celles de B.',
        'Tourne A doucement jusqu\'à ce que ses 4 trous tombent pile sur ceux du palonnier. Garde la position où les 2 bras sont le plus près de '
        f'{ENTRE_TROUS:.0f} mm entre les 2 trous du bout (dessin vu de dessus).',
        'Les 2 bras doivent être symétriques. Sinon : soulève B, tourne-le d\'une dent, repose-le.',
        'Visse A avec les 4 vis M2,5 × 8. Visse B avec la vis M3 × 10, SANS rondelle.'],
       f'Pas besoin d\'être pile à {ENTRE_TROUS:.0f} mm : au premier lancement de tester_pince, tu règles la pince à la main et le servo '
       'enregistre cette position comme son milieu (étalonnage).')
def e_engrenages(ax):
    pcs = fixe() + mobile(('engrenage A', 'engrenage B'), pales=False)
    dessiner(ax, pcs, vue=(90, -90), cadre=(-20, 110, -60, 60, -10, 50), marge=0.62)
    zt = G.Z0 + G.EP_ENG + 5
    ax.plot([Q1[1][0]] * 2, [Q1[1][1], Q1[-1][1]], [zt] * 2, color='#c0392b', lw=2.5, zorder=60)
    for k in (1, -1): ax.plot([Q1[k][0]], [Q1[k][1]], [zt], 'o', color='#c0392b', ms=9, zorder=61)
    etiquette(ax, (Q1[1][0], 0, zt), f'{ENTRE_TROUS:.0f} mm\nentre les 2 trous', (110, 0), '#c0392b')
    etiquette(ax, (G.AX, G.AY, zt), 'A (sur le servo)\n4 vis M2,5', (-120, 90))
    etiquette(ax, (G.AX, -G.AY, zt), 'B (sur son poteau)\nvis M3 × 10', (-120, -90))
    ax.text2D(0.08, 0.95, 'VU DE DESSUS', transform=ax.transAxes, fontsize=15, weight='bold')

@etape('Les doigts', ['les 2 doigts (avec leurs roulements)', '2 vis M3 × 16', '2 écrous frein M3', '2 rondelles M3'],
       ['Chaque doigt se pose SUR le bout du bras de son engrenage : la mâchoire vers l\'avant et vers le bas.',
        'Entre le doigt et le bras : 1 rondelle.',
        'Vis M3 × 16 par le dessus, à travers le roulement avant du doigt, la rondelle et le bras.',
        'Écrou frein en dessous. Serre jusqu\'au contact, puis vérifie que le doigt tourne encore librement.',
        'Le trou arrière du doigt porte le bouchon : il servira à l\'étape suivante.',
        'Même chose de l\'autre côté.'],
       'Si le doigt frotte après serrage : desserre d\'un quart de tour (l\'écrou frein ne se dévissera pas).')
def e_doigts(ax):
    pcs = fixe() + mobile(('engrenage A', 'engrenage B'))
    dz = 14
    for k in (1, -1):
        pcs.append((P['doigt +Y' if k > 0 else 'doigt -Y'].translate((0, 0, dz)), COUL['doigt +Y']))
        x, y = Q1[k]
        pcs += [(vis(x, y, G.Z_DOIGT + dz + 12, 16), NOIR), (rondelle(x, y, G.Z0 + G.EP_ENG + 4), RONDELLE), (ecrou(x, y, G.Z0 - 14), '#555')]
    dessiner(ax, pcs, vue=(24, -40), marge=0.8)
    x, y = Q1[-1]
    etiquette(ax, (x, y, G.Z_DOIGT + dz + 30), 'vis M3 × 16', (-110, 30))
    etiquette(ax, (x, y, G.Z0 + G.EP_ENG + 4.3), 'rondelle', (-130, 10))
    etiquette(ax, (x, y, G.Z0 - 12), 'écrou frein\n(dessous)', (-120, -30))
    etiquette(ax, (x + 30, y - 6, G.Z_DOIGT + dz), 'doigt', (90, -40))

@etape('Les bras libres', ['les 2 bras libres (avec leurs 2 roulements)', '2 vis M3 × 10', '2 vis M3 × 8', '2 rondelles M3'],
       ['Le roulement du bras se pose sur son pivot : côté bride pour l\'un, poteau de la base pour l\'autre.',
        'L\'autre bout du bras vient au-dessus du bouchon du doigt, avec 1 rondelle entre les deux.',
        'Pivot : vis M3 × 10 dans l\'insert, SANS rondelle.',
        'Bout du bras : vis M3 × 8, SANS rondelle dessus : elle traverse le roulement du bras et se visse dans le bouchon du doigt.',
        'Visse jusqu\'au contact, sans forcer : le plastique du bouchon fait le filetage. Le bras doit tourner librement mais ne plus pouvoir se soulever.'],
       'Bien M3 × 8 au bout du bras : une M3 × 10 dépasserait sous le doigt et frotterait sur le bras de l\'engrenage.')
def e_bras_libres(ax):
    pcs = fixe() + mobile(('engrenage A', 'engrenage B', 'doigt +Y', 'doigt -Y'))
    dz = 14
    for k in (1, -1):
        pcs.append((P['bras libre +Y' if k > 0 else 'bras libre -Y'].translate((0, 0, dz)), COUL['bras libre +Y']))
        pcs += [(vis(*PIV[k], G.Z_LIBRE + 4 + dz + 10, 10), NOIR), (vis(*Q2[k], G.Z_LIBRE + G.EP_LIBRE + dz + 6, 8), NOIR),
                (rondelle(*Q2[k], G.Z_LIBRE - 0.5 + 6), RONDELLE)]
    dessiner(ax, pcs, vue=(30, -40), marge=0.8)
    etiquette(ax, (*PIV[1], G.Z_LIBRE + dz + 26), 'pivot :\nM3 × 10, sans rondelle', (-120, 30))
    etiquette(ax, (*Q2[1], G.Z_LIBRE + dz + 22), 'bout : M3 × 8 dans le\nroulement, vissée\ndans le bouchon', (100, 50))
    etiquette(ax, (*Q2[1], G.Z_LIBRE + 6.3), 'rondelle', (110, -30))

@etape('Essai à la main, puis sur le bras', ['la pince montée', 'le bout de l\'avant-bras', 'les 2 vis M3 × 30 de l\'entretoise'],
       ['Servo NON alimenté : ouvre et ferme doucement à la main (ça résiste un peu, c\'est le servo).',
        'Ça doit aller d\'un bout à l\'autre sans point dur, et les mâchoires restent parallèles.',
        'Premier essai moteur, pince SEULE sur la table : bras\\tester_pince.bat. Il commence par l\'étalonnage : pince réglée à la main à 71 mm entre les mâchoires.',
        'Quand elle marche : enlève les 2 vis M3 × 30 du bout de l\'avant-bras, enfile le manchon jusqu\'au fond.',
        'Remets les 2 vis M3 × 30 : elles traversent maintenant le manchon.'],
       'Point dur ? Ne force pas : regarde quelle vis est trop serrée ou quelle pièce frotte.')
def e_final(ax):
    pcs = [(BASE, COUL['base']), (SERVO, '#555'), (BRIDE, COUL['bride'])] + mobile(tuple(P), pales=False) + [(AVB.translate((-25, 0, 0)), COUL['avant-bras'])]
    dessiner(ax, pcs, vue=(25, -55), marge=0.75)
    etiquette(ax, (G.XF - 50, 0, G.ZC + 12), 'avant-bras', (-40, 70))
    etiquette(ax, (G.XF - 7, 0, G.ZC + 15), 'manchon', (40, 90))

if __name__ == '__main__':
    with PdfPages(G.OUT / 'plan_montage.pdf') as pdf:
        page_pieces(pdf, 0)
        for n, (titre, il_faut, faire, attention, f) in enumerate(ETAPES, 1):
            fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
            ax = fig.add_axes([0.0, 0.02, 0.6, 0.86], projection='3d'); f(ax)
            fig.text(0.03, 0.94, f'Étape {n} / {len(ETAPES)} — {titre}', fontsize=24, weight='bold')
            nl = len(il_faut) + sum(len(textwrap.wrap(l, 48)) for l in faire) + len(faire) * 0.45 + (4 if attention else 0)
            k = min(1.0, 24 / nl)                 # réduit police et interlignes quand l'étape est longue
            fs, pas, y = 14 * max(k, 0.8), 0.03 * k, 0.86
            fig.text(0.61, y, 'Il te faut :', fontsize=16, weight='bold'); y -= 0.035
            for l in il_faut: fig.text(0.62, y, '•  ' + l, fontsize=fs); y -= pas
            y -= 0.025 * k; fig.text(0.61, y, 'Ce qu\'il faut faire :', fontsize=16, weight='bold'); y -= 0.035
            for i, l in enumerate(faire, 1):
                lignes = textwrap.wrap(l, 48)
                fig.text(0.62, y, f'{i}.', fontsize=fs, weight='bold')
                for li in lignes: fig.text(0.645, y, li, fontsize=fs); y -= 0.028 * k
                y -= 0.012 * k
            if attention:
                y -= 0.02; t = '\n'.join(textwrap.wrap('⚠ ' + attention, 50))
                fig.text(0.61, y, t, fontsize=13.5, va='top', color='#8a3b00',
                         bbox=dict(boxstyle='round,pad=0.6', fc='#fff3e0', ec='#e2783a'))
            fig.savefig(G.OUT / f'plan_montage_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)
    print('ok', len(ETAPES), 'étapes')
