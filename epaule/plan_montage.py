"""Plan de montage illustré de l'épaule (V2 du plan, 16/11/2026) : une page par étape, PDF + PNG.
Lancer après generer_epaule.py. Dessin « technique » : contours noirs, une couleur par pièce posée à l'étape,
gris pour ce qui est déjà monté, légende sur chaque page, pointillés de la vis à son trou.
Repère de l'épaule : X vers l'avant, Y sort du mur (axe de l'épaule), Z en haut."""
import math, textwrap, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import generer_epaule as E
E.PINCE = E.pince_ouverte()

# ---------------- couleurs : UNE par pièce, gardée dans tout le plan ----------------
C = {'bati': '#7fb069', 'berceau': '#5b8bd6', 'bride': '#9b6fd0', 'bas': '#f0a030', 'haut': '#e0602a', 'servo': '#3a3a3a',
     'coude': '#2f9fae', 'ressort': '#d0302a'}
GRIS, GRIS_SERVO = '#dcdcdc', '#a8a8a8'
LAITON, NOIR = '#d6a62e', '#151515'
CABLE = '#f2d21b'
TROU_CONSEILLE = (-46.0, 50.0)

def cy(x, z, y0, y1, d, n=24): return E.cyl_y(x, z, min(y0, y1), max(y0, y1), d, n)
def insert(x, z, y, sens=1): return cy(x, z, y, y + sens * 5.7, 4.8, 20) - cy(x, z, y - sens * 0.1, y + sens * 5.8, 2.6, 12)
def vis(x, z, y_tete, longueur, sens, d=3.0):
    """Vis d'axe Y : tête en y_tete (côté opposé à sens), tige de longueur `longueur` dans le sens `sens`."""
    return cy(x, z, y_tete, y_tete - sens * d, d * 1.8, 20) + cy(x, z, y_tete, y_tete + sens * longueur, d, 12)
def ecrou(x, z, y): return cy(x, z, y, y + 2.4, 6.2, 6)
def rot_y_vers_z(m): return m.rotate((90, 0, 0))                 # pour montrer une pièce « face Y vers le haut »
def p_y_vers_z(p): return (p[0], -p[2], p[1])

# ---------------- rendu : faces ombrées + arêtes vives en noir ----------------
LUM = np.array([0.35, -0.55, 0.75]); LUM /= np.linalg.norm(LUM)
def dessiner(ax, pieces, vue=(24, 48), marge=1.0, cadre=None):
    """pieces : (manifold, couleur). Arêtes vives (> 25°) dessinées en noir, seulement celles tournées vers nous."""
    e, a = map(math.radians, vue)
    cam = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    polys, fc, ec, lw, pts = [], [], [], [], []
    for m, c in pieces:
        t = E.mesh(m); base = np.array(matplotlib.colors.to_rgb(c)); pts.append(t.vertices)
        k = 0.55 + 0.45 * np.clip(t.face_normals @ LUM, 0, 1)
        col = np.clip(base * k[:, None], 0, 1)
        for tri, cc in zip(t.vertices[t.faces], col):
            polys.append(tri); fc.append((*cc, 1)); ec.append((*cc, 1)); lw.append(0.25)
        vif = t.face_adjacency_angles > math.radians(25)
        vu = (t.face_normals[t.face_adjacency] @ cam).max(axis=1) > -0.05
        for i, j in t.face_adjacency_edges[vif & vu]:
            p, q = t.vertices[i] + cam * 0.4, t.vertices[j] + cam * 0.4
            polys.append(np.array([p, q, p])); fc.append((0, 0, 0, 0)); ec.append((0.08, 0.08, 0.08, 1)); lw.append(0.9)
    ax.add_collection3d(Poly3DCollection(polys, facecolors=fc, edgecolors=ec, linewidths=lw))
    if cadre is None:
        v = np.vstack(pts); mi, ma = v.min(0), v.max(0)
    else:
        mi, ma = np.array(cadre[::2], float), np.array(cadre[1::2], float)
    c0, d = (mi + ma) / 2, (ma - mi).max() / 2 * marge
    ax.set(xlim=(c0[0] - d, c0[0] + d), ylim=(c0[1] - d, c0[1] + d), zlim=(c0[2] - d, c0[2] + d))
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.view_init(*vue)

def etiquette(ax, xyz, texte, decal, coul='#111', taille=12):
    x2, y2, _ = proj3d.proj_transform(*xyz, ax.get_proj())
    ax.annotate(texte, xy=(x2, y2), xytext=decal, textcoords='offset points', fontsize=taille, color=coul, weight='bold', ha='center',
                va='center', bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=coul, lw=1.4),
                arrowprops=dict(arrowstyle='-|>', color=coul, lw=1.6, shrinkA=2, shrinkB=1), zorder=50)
def guide(ax, p, q):
    ax.plot(*zip(p, q), ls=(0, (4, 3)), color='#c0392b', lw=1.4, zorder=40)

def panneaux(fig, n, titres=None):
    """n vues dans la partie gauche de la page."""
    axes = []
    for k in range(n):
        if n == 1: r = [0.0, 0.1, 0.6, 0.78]
        elif n == 2: r = [0.0, 0.1 + 0.4 * (1 - k), 0.6, 0.39]
        else: r = [0.0 + 0.3 * (k % 2), 0.1 + 0.4 * (1 - k // 2), 0.3, 0.39]
        ax = fig.add_axes(r, projection='3d'); axes.append(ax)
        if titres: ax.text2D(0.03, 0.97, titres[k], transform=ax.transAxes, fontsize=14, weight='bold', va='top')
    return axes

def legende(fig, elements):
    x = 0.02
    for coul, texte in elements:
        fig.add_artist(Rectangle((x, 0.035), 0.016, 0.022, transform=fig.transFigure, fc=coul, ec='#222', lw=0.8))
        fig.text(x + 0.021, 0.046, texte, fontsize=11.5, va='center'); x += 0.03 + 0.0072 * len(texte)

# ---------------- positions ----------------
B = E.B
BRIDE_VIS = [(-24.9, s * 19.4) for s in (1, -1)]
Y_HAUT_COL = 46.5
ENT = [(E.ENT_A + E.ENT_A_L / 2, s * E.VIS_ENT_Z) for s in (1, -1)] + [(E.ENT_B + E.ENT_B_L / 2, s * E.VIS_ENT_Z) for s in (1, -1)]
Y_HAUT_ENT_BAS = E.Y_FOURCHE + E.F.plaque_T + E.F.demi_H
LEG_BASE = [(GRIS, 'déjà monté'), (NOIR, 'vis'), (LAITON, 'insert M3')]

ETAPES = []
def etape(titre, il_faut, faire, attention=None, legende_pieces=()):
    def deco(f): ETAPES.append((titre, il_faut, faire, attention, legende_pieces, f)); return f
    return deco

@etape('Le servo de l\'épaule, tout seul', ['le servo de l\'épaule', 'la carte + 12 V', 'le logiciel FD'],
       ['Branche UN SEUL servo sur la carte.', 'FD, onglet Programming : ligne 5 · ID → 2, puis Save.',
        'Search : il doit réapparaître avec l\'ID 2.', 'Ne règle PAS ses butées : le programme de l\'épaule le fera, bras tenu à la main.',
        'Ferme FD, coupe le 12 V, débranche.'], 'Numéros : épaule 2, coude 1 (pour l\'instant), pince 4.', [(C['servo'], 'servo de l\'épaule')])
def e_servo(fig):
    ax, = panneaux(fig, 1); dessiner(ax, [(E.SERVO_C, C['servo'])], marge=0.85)
    etiquette(ax, (40, 30, 47), 'palonnier\n(disque cranté)', (110, 60)); etiquette(ax, (25, 18, 25), 'servo → ID 2', (-110, -40))

@etape('Les 17 inserts', ['2 berceaux à inserts', 'moitié basse du haut du bras', 'moitié haute du haut du bras', '17 inserts M3, fer à 230 °C'],
       ['Berceau (× 2) : 4 inserts SOUS le socle, posés par-dessous, au ras du dessous.',
        'Berceau (× 2) : 2 inserts en haut des 2 colonnes.',
        'Moitié basse : 4 inserts en haut des 2 entretoises.',
        'Moitié haute : 1 insert sur la face plate, à mi-longueur (vis du ressort).',
        'Insert bien droit, enfoncé jusqu\'au ras.'],
       'Les inserts du socle reçoivent des vis venant de derrière : ils doivent être au ras du DESSOUS du socle.',
       [(C['berceau'], 'berceau'), (C['bas'], 'moitié basse'), (C['haut'], 'moitié haute')])
def e_inserts(fig):
    a1, a2, a3 = panneaux(fig, 3, ['A. Berceau (× 2)', 'B. Moitié basse', 'C. Moitié haute'])
    trous_socle = [(x, y) for x in (8, 72) for y in (8, 52)]
    cols = [(50.4, 10.6), (50.4, 49.4)]
    from manifold3d import Manifold
    ins_z = lambda x, y, z0, h: Manifold.cylinder(h, 2.4, 2.4, 20).translate((x, y, z0)) - Manifold.cylinder(h + 0.2, 1.3, 1.3, 12).translate((x, y, z0 - 0.1))
    pcs = [(E.BERCEAU_C, C['berceau'])] + [(ins_z(x, y, -16, 5.7), LAITON) for x, y in trous_socle] + [(ins_z(x, y, 56, 5.7), LAITON) for x, y in cols]
    dessiner(a1, pcs, vue=(18, -60), marge=0.75)
    for x, y in trous_socle: guide(a1, (x, y, -10), (x, y, 0))
    for x, y in cols: guide(a1, (x, y, 56), (x, y, 46.5))
    etiquette(a1, (72, 8, -14), '4 sous le socle', (70, -30), taille=11); etiquette(a1, (50.4, 49.4, 62), '2 en haut\ndes colonnes', (80, 20), taille=11)
    bas = rot_y_vers_z(E.BRAS_BAS)
    pcs = [(bas, C['bas'])] + [(rot_y_vers_z(insert(x, z, Y_HAUT_ENT_BAS + 10, 1)), LAITON) for x, z in ENT]
    dessiner(a2, pcs, vue=(30, -70), marge=0.62)
    for x, z in ENT: guide(a2, p_y_vers_z((x, Y_HAUT_ENT_BAS + 10, z)), p_y_vers_z((x, Y_HAUT_ENT_BAS, z)))
    etiquette(a2, p_y_vers_z((ENT[2][0], Y_HAUT_ENT_BAS + 14, ENT[2][1])), '4 en haut des\nentretoises', (-90, 70), taille=11)
    haut = rot_y_vers_z(E.BRAS_HAUT)
    pcs = [(haut, C['haut']), (rot_y_vers_z(insert(E.B_VIS, 0, E.Y_FACE + 10, 1)), LAITON)]
    dessiner(a3, pcs, vue=(35, -70), marge=0.62)
    guide(a3, p_y_vers_z((E.B_VIS, E.Y_FACE + 10, 0)), p_y_vers_z((E.B_VIS, E.Y_FACE, 0)))
    etiquette(a3, p_y_vers_z((E.B_VIS, E.Y_FACE + 14, 0)), '1 insert\n(vis du ressort)', (-40, 50), taille=11)
    etiquette(a3, p_y_vers_z((120, E.Y_FACE, 0)), 'platine', (50, -40), taille=11)

@etape('Le bloc épaule sur le mur', ['le bâti', 'le bloc monté sur la table', '4 vis M3 × 10'],
       ['Présente le bloc entre le mur et le mât : le haut du bras ressort vers l\'avant, par le côté ouvert du bâti.',
        'Le SOCLE du berceau se pose à plat contre la face intérieure du mur (celle qui regarde le mât).',
        'Les 2 colonnes du berceau vont vers l\'ARRIÈRE (côté mur du fond), comme sur le dessin A.',
        'Les 4 vis M3 × 10 passent PAR DERRIÈRE le mur (dessin B) et se vissent dans les inserts du socle.',
        'Serre en croix, jusqu\'au contact.'],
       'Les vis sont derrière le mur : faciles d\'accès, même avec le bras monté. Tiens le bloc d\'une main pendant les 2 premières vis.',
       [(C['bati'], 'bâti'), (C['berceau'], 'bloc épaule')])
def e_berceau_mur(fig):
    a1, a2 = panneaux(fig, 2, ['A. Côté berceau', 'B. Par derrière le mur'])
    dy = 26
    bloc = E.BERCEAU_E + E.SERVO_E + E.BRAS_BAS + E.BRAS_HAUT + E.BRIDE_E
    pcs = [(E.BATI, C['bati']), (bloc.translate((0, dy, 0)), C['berceau'])]
    dessiner(a1, pcs, vue=(22, 55), marge=0.7)
    for x, z in E.TROUS_MUR: guide(a1, (x, 0, z), (x, dy, z))
    etiquette(a1, (-20, dy + 5, 28), 'socle du berceau\ncontre le mur', (-150, -20)); etiquette(a1, (120, dy + 50, 0), 'haut du bras\n(vers l\'avant)', (-40, -110))
    etiquette(a1, (20, 0, 30), 'mur', (90, 40))
    pcs = [(E.BATI, C['bati']), (E.BERCEAU_E + E.SERVO_E + E.BRAS_BAS + E.BRAS_HAUT + E.BRIDE_E, GRIS)] + [(vis(x, z, -E.EP_MUR - 16, 10, 1), NOIR) for x, z in E.TROUS_MUR]
    dessiner(a2, pcs, vue=(18, -125), marge=0.62)
    for x, z in E.TROUS_MUR: guide(a2, (x, -E.EP_MUR - 6, z), (x, 0, z))
    etiquette(a2, (E.TROUS_MUR[1][0], -E.EP_MUR - 20, E.TROUS_MUR[1][1]), '4 vis M3 × 10', (-90, -60))

@etape('Le berceau du coude sur la platine', ['la moitié haute (avec son insert)', 'le 2e berceau à inserts', '4 vis M3 × 10'],
       ['La platine est le bout LARGE de la moitié haute.',
        'Le socle du berceau se pose sur la face EXTÉRIEURE de la platine : celle qui porte l\'insert du ressort (dessin A).',
        'Les 4 vis M3 × 10 entrent par l\'autre face (dessin B) et se vissent dans les inserts du socle.',
        'À faire AVANT de monter le bras sur l\'épaule.'],
       'Ce berceau remplace le support de table du coude.', [(C['haut'], 'moitié haute'), (C['berceau'], 'berceau du coude')])
def e_berceau_platine(fig):
    a1, a2 = panneaux(fig, 2, ['A. Face extérieure (avec l\'insert du ressort)', 'B. Face intérieure : les vis'])
    dy = 28
    pcs = [(E.BRAS_HAUT, C['haut']), (E.BERCEAU_COUDE.translate((0, dy, 0)), C['berceau']), (insert(E.B_VIS, 0, E.Y_FACE - 5.7, 1), LAITON)]
    dessiner(a1, pcs, vue=(28, 55), marge=0.6)
    for x, z in E.TROUS_PLATINE: guide(a1, (x, E.Y_FACE, z), (x, E.Y_FACE + dy, z))
    etiquette(a1, (E.B_VIS, E.Y_FACE, 0), 'insert du\nressort', (-70, -60)); etiquette(a1, (110, E.Y_FACE + dy + 45, 20), 'berceau du coude', (60, 60))
    etiquette(a1, (130, E.Y_FACE, -28), 'platine', (60, -50))
    pcs = [(E.BRAS_HAUT, C['haut']), (E.BERCEAU_COUDE, GRIS)] + [(vis(x, z, E.Y_PL_HAUT - 16, 10, 1), NOIR) for x, z in E.TROUS_PLATINE]
    dessiner(a2, pcs, vue=(20, -125), marge=0.6)
    for x, z in E.TROUS_PLATINE: guide(a2, (x, E.Y_PL_HAUT - 6, z), (x, E.Y_PL_HAUT, z))
    etiquette(a2, (E.TROUS_PLATINE[1][0], E.Y_PL_HAUT - 20, E.TROUS_PLATINE[1][1]), '4 vis M3 × 10', (110, 30))
    etiquette(a2, (60, E.Y_PL_HAUT, 0), 'moitié haute,\nface intérieure', (-90, -60))

@etape('Câbles, servo et haut du bras, À PLAT SUR LA TABLE', ['le 2e berceau à inserts (pas encore sur le mur)', 'le servo n° 2, son disque libre, 2 câbles', 'les 2 moitiés du haut du bras', '8 vis M2,5 (fournies avec le servo)', '4 vis M3 × 30'],
       ['D\'ABORD LES CÂBLES : branche 2 câbles sur les 2 prises du servo (vers la carte, vers le coude). Après, on ne les atteint plus.',
        'Couche-les dans la rainure du berceau, un qui sort de chaque côté, puis pose le servo dessus, palonnier vers le haut. Aucun câble pincé ni posé sur le socle.',
        'Moitié BASSE (orange clair) côté socle du berceau, sur le disque libre : 4 vis M2,5.',
        'Moitié HAUTE (orange foncé) : elle se POSE À PLAT SUR le palonnier (il n\'entre pas dedans ; le trou du milieu laisse passer sa vis centrale). 4 vis M2,5 dans les trous du palonnier.',
        '4 vis M3 × 30 par la face extérieure (dessin B), dans les inserts de la moitié basse. Serre en croix, arrête dès que les entretoises se touchent.'],
       'Chaîne : carte → épaule (n° 2) → coude (n° 1) → pince (n° 4). Une fois sur le mur : câble de la carte vers le bas, câble du coude vers le haut.',
       [(CABLE, 'câbles'), (C['berceau'], 'berceau'), (C['servo'], 'servo'), (C['bas'], 'moitié basse'), (C['haut'], 'moitié haute')])
def e_bras(fig):
    a1, a2 = panneaux(fig, 2, ['A. Les 2 câbles dans la rainure, le servo, la moitié basse', 'B. Moitié haute posée sur le palonnier + 4 vis M3 × 30'])
    cables = E.berceau_sur_mur(E.box(37, -28, 6.3, 41, 27, 8.7) + E.box(37, 33, 6.3, 41, 88, 8.7))
    pcs = [(E.BERCEAU_E, C['berceau']), (E.SERVO_E, C['servo']), (E.BRAS_BAS, C['bas']), (cables, CABLE)]
    dessiner(a1, pcs, vue=(30, 55), marge=0.62)
    etiquette(a1, (-15, 47, 10), 'servo', (-90, 50)); etiquette(a1, (90, 9, 12), 'moitié basse\n(côté socle)', (90, -40))
    etiquette(a1, (-13.5, 7.5, -55), 'câble vers\nla carte', (-90, -30), '#8a6d00'); etiquette(a1, (-13.5, 7.5, 50), 'câble vers\nle coude', (150, -10), '#8a6d00')
    dy = 30
    pcs = [(E.BERCEAU_E, GRIS), (E.SERVO_E, GRIS_SERVO), (E.BRAS_BAS, GRIS), (E.BRAS_HAUT.translate((0, dy, 0)), C['haut'])]
    pcs += [(vis(x, z, E.Y_FACE + dy + 16, 30, -1), NOIR) for x, z in ENT]
    dessiner(a2, pcs, vue=(30, 55), marge=0.62)
    for x, z in ENT: guide(a2, (x, E.Y_FACE + dy - 14, z), (x, Y_HAUT_ENT_BAS, z))
    etiquette(a2, (130, E.Y_FACE + dy, 25), 'moitié haute', (110, 40)); etiquette(a2, (ENT[2][0], E.Y_FACE + dy + 20, ENT[2][1]), '4 vis M3 × 30', (-120, 60))

@etape('La bride de l\'épaule, toujours sur la table', ['la bride', '2 vis M3 × 10'],
       ['La bride se pose en travers sur le servo, entre les 2 colonnes du berceau.',
        'Les 2 vis M3 × 10 se vissent dans les inserts en haut des colonnes, un peu chacune, à tour de rôle.',
        'Serre jusqu\'à ce que le servo ne bouge plus. Pas plus.'],
       'Comme au coude : la bride appuie sur le servo avant de toucher les colonnes.', [(C['bride'], 'bride')])
def e_bride(fig):
    ax, = panneaux(fig, 1)
    dy = 22
    pcs = [(E.BERCEAU_E, GRIS), (E.SERVO_E, GRIS_SERVO), (E.BRIDE_E.translate((0, dy, 0)), C['bride'])]
    pcs += [(vis(x, z, 51.9 + dy + 16, 10, -1), NOIR) for x, z in BRIDE_VIS]
    dessiner(ax, pcs, vue=(38, 70), marge=0.75, cadre=(-65, 35, -5, 95, -40, 40))
    ax.text2D(0.02, 0.02, '(le haut du bras n\'est pas dessiné, pour y voir clair)', transform=ax.transAxes, fontsize=11, style='italic')
    for x, z in BRIDE_VIS: guide(ax, (x, 51.9 + dy, z), (x, Y_HAUT_COL, z))
    etiquette(ax, (-25, 51.9 + dy, 0), 'bride', (-120, 30)); etiquette(ax, (BRIDE_VIS[0][0], 51.9 + dy + 20, BRIDE_VIS[0][1]), '2 vis M3 × 10', (90, 60))
    etiquette(ax, (-25, 40, -19.4), 'colonne\n(insert en haut)', (110, -60)); etiquette(ax, (-15, 47, 5), 'servo', (-170, 80))

@etape('Le coude, l\'avant-bras et la pince', ['le coude démonté du support de table, avec sa fourche et la pince', 'la bride du coude', '2 vis M3 × 10'],
       ['Démonte le coude du support de table : fourche et pince restent sur le servo.',
        'CÂBLES D\'ABORD : sur le servo du coude, le câble qui vient de l\'épaule et celui de la pince, branchés AVANT de le poser.',
        'Le servo du coude se couche dans le berceau de la platine, câbles dans la rainure, un de chaque côté.',
        'Bride du coude : 2 vis M3 × 10, comme d\'habitude.',
        'L\'avant-bras passe à côté du haut du bras, jamais dedans.'],
       'Câble épaule → coude : environ 20 cm, avec une boucle souple près de l\'axe de l\'épaule, loin du ressort. Trop court : rallonge 5264 3 broches, pas de dominos.', [(C['coude'], 'coude, avant-bras, pince')])
def e_coude(fig):
    ax, = panneaux(fig, 1)
    p = E.bras_complet(0.0, 0.0, avec_pince=True)
    pcs = [(E.BATI, GRIS), (E.BERCEAU_E + E.BRIDE_E, GRIS), (E.SERVO_E, GRIS_SERVO), (p['bras bas'] + p['bras haut'], GRIS), (p['berceau du coude'], GRIS),
           (p['servo du coude'] + p['bride du coude'] + p['avant-bras et pince'], C['coude'])]
    dessiner(ax, pcs, vue=(28, 60), marge=0.52)
    etiquette(ax, (120, 95, 0), 'servo du coude', (-90, 80)); etiquette(ax, (240, 80, 0), 'avant-bras + pince', (40, 90))

@etape('Essai à la main, et le pied bien fixé', ['le bras monté', 'un serre-joint (ou 4 vis à bois)'],
       ['Servo NON alimenté : lève et baisse le bras à la main, de 30° sous l\'horizontale jusqu\'à la verticale.',
        'Rien ne doit toucher, et aucun câble ne doit se tendre ni se coincer sous la fourche.',
        'Fixe le pied sur la table : serre-joint sur le bord du pied, ou 4 vis à bois dans ses 4 trous.'],
       'Sans ressort, le bras retombe tout seul : accompagne-le, ne le lâche pas.', [(C['bati'], 'pied à fixer')])
def e_essai(fig):
    ax, = panneaux(fig, 1)
    p = E.bras_complet(45.0, 0.0, avec_pince=True)
    pcs = [(E.BATI, C['bati']), (E.BERCEAU_E + E.BRIDE_E, GRIS), (E.SERVO_E, GRIS_SERVO)] + [(m, GRIS) for m in p.values()]
    dessiner(ax, pcs, vue=(25, 60), marge=0.52)
    etiquette(ax, (-84, -15, -101), 'trous du pied\n(vis à bois)', (-100, -50)); etiquette(ax, (100, 50, 100), 'de −30° à +90°', (60, 80))

@etape('Le ressort, en dernier', ['le ressort 70 × 10 × 1,2', '2 vis M3 × 16 + 2 rondelles', '1 écrou M3', 'des lunettes'],
       ['Lève le bras vers 70° et tiens-le : le ressort se pose sans tirer.',
        'Bout 1 : vis M3 × 16 + rondelle dans l\'insert du ressort (moitié haute).',
        'Bout 2 : vis M3 × 16 + rondelle dans le trou ROUGE du mât (dessin B : rangée du haut, colonne la plus loin du bras), écrou derrière le mât.',
        'Ne lâche le bras que servo alimenté et réglé, ou bras posé.'],
       'Lunettes : le ressort tire jusqu\'à 4 kg. Le meilleur trou se confirme à l\'essai motorisé (commande m).',
       [(C['ressort'], 'ressort'), (C['bati'], 'mât du bâti')])
def e_ressort(fig):
    a1, a2 = panneaux(fig, 2, ['A. Le ressort en place (bras à 70°)', 'B. Les 12 trous du mât, vus de face'])
    a = 70.0; r = math.radians(a)
    p = E.bras_complet(a, 0.0, avec_pince=False)
    pcs = [(E.BATI, C['bati']), (E.BERCEAU_E + E.BRIDE_E, GRIS), (E.SERVO_E, GRIS_SERVO)] + [(m, GRIS) for k, m in p.items() if k != 'avant-bras et pince']
    pcs += [(E.ressort(a, TROU_CONSEILLE, 10)[0], C['ressort'])]
    pcs += [(vis(E.B_VIS * math.cos(r), E.B_VIS * math.sin(r), E.Y_RESSORT - 8, 16, 1), NOIR), (vis(*TROU_CONSEILLE, E.Y_RESSORT - 8, 16, 1), NOIR)]
    pcs += [(ecrou(*TROU_CONSEILLE, E.Y_MAT + E.EP_MUR), NOIR)]
    dessiner(a1, pcs, vue=(15, 25), marge=0.62, cadre=(-100, 80, -10, 90, -105, 150))
    etiquette(a1, (E.B_VIS * math.cos(r), E.Y_RESSORT - 10, E.B_VIS * math.sin(r)), 'vis dans l\'insert\ndu bras', (-110, 40), C['ressort'])
    etiquette(a1, (TROU_CONSEILLE[0], E.Y_MAT + E.EP_MUR + 3, TROU_CONSEILLE[1]), 'trou du mât\n+ écrou derrière', (90, -60), C['ressort'])
    a2.remove(); ax = fig.add_axes([0.1, 0.12, 0.4, 0.33]); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((-62, 18), 38, 48, fc=matplotlib.colors.to_rgba(C['bati'], 0.35), ec='#333', lw=1.2))
    for x, z in E.TROUS_RESSORT:
        bon = (x, z) == TROU_CONSEILLE
        ax.add_patch(plt.Circle((x, z), 2.6 if bon else 1.65, fc=C['ressort'] if bon else 'white', ec='#222', lw=1.2))
    ax.annotate('trou conseillé', xy=(-46, 50), xytext=(-90, 62), fontsize=12, weight='bold', color=C['ressort'], arrowprops=dict(arrowstyle='-|>', color=C['ressort']))
    ax.annotate('', xy=(5, 40), xytext=(-20, 40), arrowprops=dict(arrowstyle='-|>', lw=2, color='#333'))
    ax.text(-19, 44, 'vers l\'avant (côté épaule)', fontsize=11); ax.text(-62, 69, 'haut du mât ↑', fontsize=11)
    ax.set_xlim(-100, 30); ax.set_ylim(12, 74)
    ax.text(-100, 74, 'B. Les 12 trous du mât, vus de face (depuis le bras)', fontsize=14, weight='bold')

@etape('Premier essai motorisé', ['bras\\tester_epaule.bat', 'la carte + 12 V', 'servo n° 2 branché'],
       ['D\'abord SANS ressort : étalonnage, sens et butées.',
        'Étalonnage sans moteur : tu tiens le bras à l\'horizontale (zéro), puis tu le lèves à la main ; le programme écrit les butées (−30° et +90°).',
        'Avec l\'avant-bras et la pince : tester_epaule.bat --coude 1 (le coude est tenu raide), puis m : effort mesuré à 6 hauteurs.',
        'Avec le ressort : refais m, change de trou, garde celui qui donne l\'effort le plus faible.'],
       'Si une sécurité s\'arrête, l\'épaule RETIENT le bras (force réduite) au lieu de le lâcher. Main près de l\'interrupteur.', [])
def e_moteur(fig):
    ax, = panneaux(fig, 1)
    p = E.bras_complet(20.0, 0.0, avec_pince=True)
    pcs = [(E.BATI, C['bati']), (E.BERCEAU_E + E.BRIDE_E, C['berceau']), (E.SERVO_E, C['servo']), (p['bras bas'], C['bas']), (p['bras haut'], C['haut']),
           (p['berceau du coude'] + p['bride du coude'], C['berceau']), (p['servo du coude'] + p['avant-bras et pince'], C['coude']), (E.ressort(20.0, TROU_CONSEILLE, 10)[0], C['ressort'])]
    dessiner(ax, pcs, vue=(25, 60), marge=0.52)

def page_pieces(pdf, n):
    fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
    fig.suptitle('Épaule : les pièces. Chaque pièce garde SA couleur dans tout le plan', fontsize=20, weight='bold', y=0.985)
    liste = [('Bâti', E.BATI, C['bati'], '× 1', (22, 55)), ('Berceau à inserts', E.BERCEAU_C, C['berceau'], '× 2', (25, -60)),
             ('Bride du berceau', E.BRIDE_C, C['bride'], '× 1 (+ celle du coude)', (30, -60)),
             ('Haut du bras, moitié BASSE', rot_y_vers_z(E.BRAS_BAS), C['bas'], '× 1', (30, -70)),
             ('Haut du bras, moitié HAUTE (avec la platine)', rot_y_vers_z(E.BRAS_HAUT), C['haut'], '× 1', (30, -70)),
             ('Ressort 70 × 10 × 1,2', E.ressort(70, TROU_CONSEILLE, 10)[0], C['ressort'], '× 1', (20, -60))]
    for k, (nom, m, c, q, vue) in enumerate(liste):
        ax = fig.add_subplot(3, 3, k + 1, projection='3d'); dessiner(ax, [(m, c)], vue=vue, marge=0.72)
        ax.set_title(f'{nom}  {q}', fontsize=13, weight='bold', color=c)
    for k, (nom, m, c, q) in enumerate([('Inserts M3', insert(0, 0, 0), LAITON, '× 17'), ('Vis M3 × 10', vis(0, 0, 0, 10, 1), NOIR, '× 12'),
                                        ('Vis M3 × 30', vis(0, 0, 0, 30, 1), NOIR, '× 4')]):
        ax = fig.add_subplot(3, 3, 7 + k, projection='3d'); dessiner(ax, [(m, c)], cadre=(-10, 10, -6, 34, -10, 10), marge=0.9)
        ax.set_title(f'{nom}  {q}', fontsize=13, weight='bold')
    fig.text(0.03, 0.025, 'Et aussi : 8 vis M2,5 des disques du servo, 2 vis M3 × 16 + 2 rondelles + 1 écrou M3 (ressort), un serre-joint.\n'
             'Dans les étapes : EN COULEUR = la pièce que tu poses maintenant · GRIS = déjà monté · pointillés rouges = où va la vis.', fontsize=13)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.08, hspace=0.25, wspace=0.02)
    fig.savefig(E.OUT / f'plan_montage_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)

ORDRE = ['Le servo de', 'Les 17 inserts', 'Le berceau du coude', 'Câbles, servo', 'La bride', 'Le bloc épaule', 'Le coude,', 'Essai à la main', 'Le ressort', 'Premier essai']
ETAPES = [next(e for e in ETAPES if e[0].startswith(o)) for o in ORDRE]

if __name__ == '__main__':
    with PdfPages(E.OUT / 'plan_montage_epaule.pdf') as pdf:
        page_pieces(pdf, 0)
        for n, (titre, il_faut, faire, attention, leg, f) in enumerate(ETAPES, 1):
            fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
            f(fig)
            fig.text(0.03, 0.94, f'Étape {n} / {len(ETAPES)} — {titre}', fontsize=24, weight='bold')
            legende(fig, list(leg) + LEG_BASE + [('#c0392b', '- - - où va la vis')])
            nl = len(il_faut) + sum(len(textwrap.wrap(l, 48)) for l in faire) + len(faire) * 0.45 + (4 if attention else 0)
            k = min(1.0, 24 / nl); fs, pas, y = 14 * max(k, 0.8), 0.03 * k, 0.86
            fig.text(0.61, y, 'Il te faut :', fontsize=16, weight='bold'); y -= 0.035
            for l in il_faut: fig.text(0.62, y, '•  ' + l, fontsize=fs); y -= pas
            y -= 0.025 * k; fig.text(0.61, y, 'Ce qu\'il faut faire :', fontsize=16, weight='bold'); y -= 0.035
            for i, l in enumerate(faire, 1):
                fig.text(0.62, y, f'{i}.', fontsize=fs, weight='bold')
                for li in textwrap.wrap(l, 48): fig.text(0.645, y, li, fontsize=fs); y -= 0.028 * k
                y -= 0.012 * k
            if attention:
                y -= 0.02; fig.text(0.61, y, '\n'.join(textwrap.wrap('⚠ ' + attention, 50)), fontsize=13.5, va='top', color='#8a3b00',
                                    bbox=dict(boxstyle='round,pad=0.6', fc='#fff3e0', ec='#e2783a'))
            fig.savefig(E.OUT / f'plan_montage_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)
    print('ok', len(ETAPES), 'étapes')
