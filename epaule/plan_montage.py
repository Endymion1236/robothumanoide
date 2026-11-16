"""Plan de montage illustré de l'épaule : une page par étape (PDF + PNG), comme celui de la pince.
À lancer après generer_epaule.py. Repère de l'épaule : X vers l'avant, Y sortant du mur (le long de l'axe), Z en haut.
Pièces déjà montées : pâles ; pièces de l'étape : en couleur ; visserie dessinée écartée, dans l'axe de son trou."""
import math, textwrap, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import manifold3d as mf
import generer_epaule as E
E.PINCE = E.pince_ouverte()

LUM = np.array([0.5, 0.6, 0.6]); LUM /= np.linalg.norm(LUM)
COUL = {'bati': '#8fb38a', 'berceau': '#b8c9e0', 'bride': '#7aa0d4', 'servo': '#333333', 'bas': '#e2a04a', 'haut': '#d9822b',
        'avant': '#4f8fa3', 'ressort': '#c0392b'}
LAITON, NOIR, RONDELLE = '#d1a23a', '#1e1e1e', '#c9c9c9'
VUE = (24, 48)
TROU_CONSEILLE = (-46.0, 50.0)         # calcul_ressort.py pour le ressort 70 x 10 x 1,2

def cy(x, z, y0, y1, d, n=24): return E.cyl_y(x, z, min(y0, y1), max(y0, y1), d, n)
def insert(x, z, y, sens=1):            # insert M3 dessiné de y vers y + sens*5,7
    return cy(x, z, y, y + sens * 5.7, 4.6) - cy(x, z, y - sens * 0.1, y + sens * 5.8, 2.6)
def vis(x, z, y_tete, longueur, sens, d=3.0):
    """Vis d'axe Y : tête en y_tete, tige vers y_tete + sens*longueur."""
    return cy(x, z, y_tete, y_tete - sens * d, d * 1.8) + cy(x, z, y_tete, y_tete + sens * longueur, d)
def ecrou(x, z, y): return cy(x, z, y, y + 2.4, 6.2, 6)
def pale(c, k=0.6):
    r = np.array(matplotlib.colors.to_rgb(c)); return tuple(r + (1 - r) * k)

def dessiner(ax, pieces, vue=VUE, marge=1.0, cadre=None):
    faces, couls, pts = [], [], []
    for m, c in pieces:
        t = E.mesh(m); base = np.array(matplotlib.colors.to_rgb(c)); pts.append(t.vertices)
        k = 0.45 + 0.55 * np.clip(t.face_normals @ LUM, 0, 1)
        faces.append(t.vertices[t.faces]); couls.append(np.clip(base * k[:, None], 0, 1))
    ax.add_collection3d(Poly3DCollection(np.concatenate(faces), facecolors=np.concatenate(couls), linewidth=0))
    if cadre is None:
        v = np.vstack(pts); mi, ma = v.min(0), v.max(0)
    else:
        mi, ma = np.array(cadre[::2], float), np.array(cadre[1::2], float)
    c, d = (mi + ma) / 2, (ma - mi).max() / 2 * marge
    ax.set(xlim=(c[0] - d, c[0] + d), ylim=(c[1] - d, c[1] + d), zlim=(c[2] - d, c[2] + d))
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.view_init(*vue)

def etiquette(ax, xyz, texte, decal, coul='#111'):
    x2, y2, _ = proj3d.proj_transform(*xyz, ax.get_proj())
    ax.annotate(texte, xy=(x2, y2), xytext=decal, textcoords='offset points', fontsize=12, color=coul, weight='bold', ha='center',
                va='center', bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=coul, lw=1.2),
                arrowprops=dict(arrowstyle='-|>', color=coul, lw=1.6, shrinkA=2, shrinkB=1), zorder=50)

# positions utiles
BRIDE_VIS = [(-24.9, s * 19.4) for s in (1, -1)]                               # vis de la bride, en haut des colonnes du berceau
Y_HAUT_COL = 46.5
ENT = [(E.ENT_A + E.ENT_A_L / 2, s * E.VIS_ENT_Z) for s in (1, -1)] + [(E.ENT_B + E.ENT_B_L / 2, s * E.VIS_ENT_Z) for s in (1, -1)]
Y_HAUT_ENT_BAS = E.Y_FOURCHE + E.F.plaque_T + E.F.demi_H
DISQUE = [(sx * E.F.trou_d, sz * E.F.trou_d) for sx in (1, -1) for sz in (1, -1)]
FIXE = lambda: [(E.BATI, pale(COUL['bati'])), (E.BERCEAU_E, pale(COUL['berceau'])), (E.SERVO_E, '#888'), (E.BRIDE_E, pale(COUL['bride']))]
def bras_pale(alpha=0.0, avec_avant=True):
    p = E.bras_complet(alpha, 0.0, avec_pince=avec_avant)
    out = [(p['bras bas'] + p['bras haut'], pale(COUL['haut'])), (p['berceau du coude'] + p['bride du coude'], pale(COUL['berceau'])), (p['servo du coude'], '#888')]
    if avec_avant: out.append((p['avant-bras et pince'], pale(COUL['avant'])))
    return out

ETAPES = []
def etape(titre, il_faut, faire, attention=None):
    def deco(f): ETAPES.append((titre, il_faut, faire, attention, f)); return f
    return deco

@etape('Le servo de l\'épaule, tout seul', ['le servo de l\'épaule', 'la carte + 12 V', 'le logiciel FD'],
       ['Branche UN SEUL servo sur la carte.', 'Dans FD, onglet Programming : ligne 5 · ID, mets 2, puis Save.',
        'Search : il doit réapparaître avec l\'ID 2.', 'Ne règle PAS ses butées : c\'est le programme de l\'épaule qui le fera, bras tenu à la main.',
        'Ferme FD, coupe le 12 V, débranche.'],
       'Numéros du bras : socle 1 (plus tard), épaule 2, coude 1 pour l\'instant, pince 4.')
def e_servo(ax):
    dessiner(ax, [(E.SERVO_E, COUL['servo'])], marge=0.9)
    etiquette(ax, (8, 47, 0), 'palonnier', (90, 50)); etiquette(ax, (-15, 30, 12), 'servo n° 2', (-90, 60))

@etape('Les 17 inserts', ['les 2 berceaux à inserts', 'la moitié basse du bras', 'la moitié haute du bras', '17 inserts M3', 'le fer à souder'],
       ['Berceaux (× 2) : 4 inserts dans le SOCLE, posés depuis le dessous, au ras du dessous (jamais au-dessus du socle).',
        'Berceaux : 2 inserts en haut des colonnes (vis de la bride).',
        'Moitié basse du bras : 4 inserts en haut des entretoises.',
        'Moitié haute : 1 insert pour la vis du ressort (face extérieure).',
        'Fer à 230 °C pour le PETG, insert bien droit, au ras.'],
       'Les inserts du socle reçoivent les vis venant de derrière le mur (ou de sous la platine) : ils doivent être au ras du dessous.')
def e_inserts(ax):
    dz = 80
    pcs = [(E.BERCEAU_E, COUL['berceau']), (E.BRAS_BAS.translate((0, 0, -dz)), COUL['bas']), (E.BRAS_HAUT.translate((0, 0, dz)), COUL['haut'])]
    pcs += [(insert(x, z, -8, -1), LAITON) for x, z in E.TROUS_MUR]
    pcs += [(insert(x, z, Y_HAUT_COL + 8, 1), LAITON) for x, z in BRIDE_VIS]
    pcs += [(insert(x, z - dz, Y_HAUT_ENT_BAS + 8, 1), LAITON) for x, z in ENT]
    pcs += [(insert(E.B_VIS, dz, E.Y_FACE + 8, 1), LAITON)]
    dessiner(ax, pcs, marge=0.7)
    etiquette(ax, (E.TROUS_MUR[0][0], -11, E.TROUS_MUR[0][1]), 'socle du berceau :\n4 inserts par-dessous', (-60, -90))
    etiquette(ax, (BRIDE_VIS[0][0], Y_HAUT_COL + 11, BRIDE_VIS[0][1]), 'colonnes : 2', (-110, 40))
    etiquette(ax, (ENT[2][0], Y_HAUT_ENT_BAS + 11, ENT[2][1] - dz), 'moitié basse :\n4 sur les entretoises', (130, 10))
    etiquette(ax, (E.B_VIS, E.Y_FACE + 11, dz), 'moitié haute :\nvis du ressort', (100, 40))

@etape('Le berceau de l\'épaule sur le mur', ['le bâti', 'un berceau à inserts', '4 vis M3 × 10'],
       ['Pose le berceau contre le mur du bâti, son socle à plat contre le mur, le côté ouvert vers l\'arrière.',
        'Les 4 vis M3 × 10 entrent PAR DERRIÈRE le mur et se vissent dans les inserts du socle.',
        'Serre en croix, jusqu\'au contact.'],
       'Rien ne doit dépasser côté berceau : la fourche du bras passe 2 mm au-dessus du socle.')
def e_berceau_mur(ax):
    dy = 28
    pcs = [(E.BATI, pale(COUL['bati'])), (E.BERCEAU_E.translate((0, dy, 0)), COUL['berceau'])]
    pcs += [(vis(x, z, -E.EP_MUR - 14, 10, 1), NOIR) for x, z in E.TROUS_MUR]
    dessiner(ax, pcs, marge=0.7)
    etiquette(ax, (E.TROUS_MUR[0][0], -E.EP_MUR - 18, E.TROUS_MUR[0][1]), '4 vis M3 × 10\npar derrière le mur', (40, 120))
    etiquette(ax, (-20, dy + 3, 25), 'berceau\n(socle contre le mur)', (110, 70))

@etape('Le berceau du coude sur la platine', ['la moitié haute du bras', 'le 2e berceau à inserts', '4 vis M3 × 10'],
       ['Le berceau du coude se pose sur la face EXTÉRIEURE de la platine (le bout large de la moitié haute).',
        'Les 4 vis M3 × 10 entrent PAR-DESSOUS (face intérieure, têtes dans les creux) et se vissent dans les inserts du socle.',
        'À faire AVANT de monter le bras sur l\'épaule : après, on n\'y a plus accès.'],
       'Le berceau du coude remplace le support de table : le coude n\'y retournera pas.')
def e_berceau_platine(ax):
    dy = 30
    pcs = [(E.BRAS_HAUT, COUL['haut']), (E.BERCEAU_COUDE.translate((0, dy, 0)), COUL['berceau'])]
    pcs += [(vis(x, z, E.Y_PL_HAUT - 12, 10, 1), NOIR) for x, z in E.TROUS_PLATINE]
    dessiner(ax, pcs, marge=0.66)
    etiquette(ax, (E.TROUS_PLATINE[0][0], E.Y_PL_HAUT - 15, E.TROUS_PLATINE[0][1]), '4 vis M3 × 10\npar-dessous', (110, -70))
    etiquette(ax, (100, E.Y_FACE + dy + 40, 25), 'berceau du coude', (140, 60))
    etiquette(ax, (10, E.Y_FACE, 0), 'moitié haute\n(platine)', (90, 110))

@etape('Le servo et le haut du bras', ['le servo n° 2 + son disque libre', 'les 2 moitiés du haut du bras', '8 vis M2,5 des disques', '4 vis M3 × 30'],
       ['Même fourche qu\'au coude, et même ordre de montage que sur le support de table.',
        'Servo dans le berceau du mur, palonnier vers l\'extérieur (côté opposé au mur), câble dans sa rainure.',
        'Moitié BASSE sur le disque libre (4 vis M2,5), moitié HAUTE sur le palonnier (4 vis M2,5), bras à peu près horizontal : le programme réglera le zéro exact.',
        '4 vis M3 × 30 par la face extérieure (têtes noyées), dans les inserts de la moitié basse.',
        'Serre en croix, doucement : arrête dès que les entretoises se touchent.'],
       'Ne force pas le servo à tourner à la main pendant le montage.')
def e_bras(ax):
    dy = 30
    pcs = [(E.BATI, pale(COUL['bati'])), (E.BERCEAU_E, pale(COUL['berceau'])), (E.SERVO_E, COUL['servo']),
           (E.BRAS_BAS, COUL['bas']), (E.BRAS_HAUT.translate((0, dy, 0)), COUL['haut'])]
    pcs += [(vis(x, z, E.Y_FACE + dy + 14, 30, -1), NOIR) for x, z in ENT]
    dessiner(ax, pcs, marge=0.6)
    etiquette(ax, (ENT[2][0], E.Y_FACE + dy + 18, ENT[2][1]), '4 vis M3 × 30', (60, 100))
    etiquette(ax, (110, 25, -12), 'moitié basse\n(sur le disque libre)', (-40, -150))
    etiquette(ax, (140, E.Y_FACE + dy, 25), 'moitié haute\n(sur le palonnier)', (40, 120))
    etiquette(ax, (-15, 30, 12), 'servo n° 2', (-60, 130))

@etape('La bride de l\'épaule', ['la bride', '2 vis M3 × 10'],
       ['Pose la bride sur le servo, entre les deux colonnes du berceau.',
        'Visse les 2 vis M3 × 10 dans les inserts des colonnes, un peu chacune, à tour de rôle.',
        'Serre jusqu\'à ce que le servo ne bouge plus. Pas plus.'],
       'Comme au coude : la bride appuie sur le servo avant de toucher les colonnes, c\'est ce qui le tient.')
def e_bride(ax):
    dy = 22
    pcs = [(E.BATI, pale(COUL['bati'])), (E.BERCEAU_E, pale(COUL['berceau'])), (E.SERVO_E, '#888'),
           (E.BRAS_BAS + E.BRAS_HAUT, pale(COUL['haut'])), (E.BRIDE_E.translate((0, dy, 0)), COUL['bride'])]
    pcs += [(vis(x, z, 51.9 + dy + 14, 10, -1), NOIR) for x, z in BRIDE_VIS]
    dessiner(ax, pcs, marge=0.62)
    etiquette(ax, (BRIDE_VIS[0][0], 51.9 + dy + 18, BRIDE_VIS[0][1]), '2 vis M3 × 10', (-80, 80))
    etiquette(ax, (-25, 51.9 + dy, -10), 'bride', (-110, -40))

@etape('Le coude, l\'avant-bras et la pince', ['le coude démonté du support de table (servo, fourche, pince)', 'la bride du coude', '2 vis M3 × 10'],
       ['Démonte le coude du support de table : la fourche et la pince restent montées sur le servo.',
        'Glisse le servo du coude dans son nouveau berceau, sur la platine, câble dans sa rainure.',
        'Bride du coude : 2 vis M3 × 10, serrées à tour de rôle, comme d\'habitude.',
        'L\'avant-bras passe sur le côté du haut du bras, jamais dedans.'],
       'Passe les câbles du coude et de la pince avec une boucle souple à chaque articulation.')
def e_coude(ax):
    p = E.bras_complet(0.0, 0.0, avec_pince=True)
    pcs = FIXE() + [(p['bras bas'] + p['bras haut'], pale(COUL['haut'])), (p['berceau du coude'], pale(COUL['berceau'])),
                    (p['servo du coude'], COUL['servo']), (p['bride du coude'], COUL['bride']), (p['avant-bras et pince'], COUL['avant'])]
    dessiner(ax, pcs, marge=0.55)
    etiquette(ax, (110, 95, 0), 'servo du coude\ndans son berceau', (-60, 90))
    etiquette(ax, (230, 75, 0), 'avant-bras + pince', (60, 80))

@etape('Essai à la main, et le pied bien fixé', ['le bras monté', 'un serre-joint (ou 4 vis à bois)'],
       ['Servo NON alimenté : lève et baisse le bras à la main, de 30° sous l\'horizontale à la verticale.',
        'Rien ne doit toucher : ni le bâti, ni le berceau, ni les câbles.',
        'Fixe le pied du bâti sur la table : serre-joint, ou 4 vis à bois par les trous du pied.',
        'Sans ça, le bras tendu fait basculer le bâti.'],
       'Tant qu\'il n\'y a pas de ressort, le bras retombe tout seul : accompagne-le, ne le lâche pas.')
def e_essai(ax):
    pcs = FIXE() + [(m, c) for m, c in bras_pale(45.0)]
    pcs = [(m, c if k > 0 else COUL['bati']) for k, (m, c) in enumerate(pcs)]
    dessiner(ax, pcs, marge=0.55)
    etiquette(ax, (-84, -15, -101), 'pied : serre-joint\nou 4 vis à bois', (-90, -60))
    etiquette(ax, (80, 40, 80), 'de −30° à +90°', (80, 80))

@etape('Le ressort, en dernier', ['le ressort 70 × 10 × 1,2', '2 vis M3 × 16 + 2 rondelles', '1 écrou M3', 'des lunettes'],
       ['Lève le bras vers 70° et tiens-le : à cette position, le ressort se pose sans tirer.',
        'Un bout : vis M3 × 16 + rondelle dans l\'insert de la moitié haute (vis du ressort).',
        'L\'autre bout : vis M3 × 16 + rondelle dans le trou du mât conseillé : rangée du HAUT, colonne la plus en ARRIÈRE (la plus loin du bras). Écrou derrière.',
        'Ne lâche pas le bras tant que le servo n\'est pas alimenté et réglé, ou le bras posé.'],
       'Lunettes : le ressort tire jusqu\'à 4 kg. Le meilleur trou se confirme à l\'essai motorisé (commande m).')
def e_ressort(ax):
    a = 70.0
    pcs = FIXE() + bras_pale(a, avec_avant=False)
    pcs = [(m, c if k > 0 else COUL['bati']) for k, (m, c) in enumerate(pcs)]
    pcs += [(E.ressort(a, TROU_CONSEILLE, 10)[0], COUL['ressort'])]
    r = math.radians(a)
    pcs += [(vis(E.B_VIS * math.cos(r), E.B_VIS * math.sin(r), E.Y_RESSORT - 8, 16, 1), NOIR)]
    pcs += [(vis(TROU_CONSEILLE[0], TROU_CONSEILLE[1], E.Y_RESSORT - 8, 16, 1), NOIR)]
    pcs += [(ecrou(TROU_CONSEILLE[0], TROU_CONSEILLE[1], E.Y_MAT + E.EP_MUR), '#555')]
    dessiner(ax, pcs, marge=0.6, vue=(18, 30))
    etiquette(ax, (TROU_CONSEILLE[0], E.Y_MAT + E.EP_MUR + 2, TROU_CONSEILLE[1]), 'trou du mât (haut, arrière)\n+ écrou derrière', (110, -30), '#c0392b')
    etiquette(ax, (E.B_VIS * math.cos(r), E.Y_RESSORT - 10, E.B_VIS * math.sin(r)), 'vis du ressort\n(insert du bras)', (-120, 30), '#c0392b')

@etape('Premier essai motorisé', ['bras\\tester_epaule.bat', 'la carte + 12 V', 'le servo n° 2 branché'],
       ['D\'abord SANS ressort et sans avant-bras si possible : étalonnage, sens et butées.',
        'Étalonnage sans moteur : tu tiens le bras à l\'horizontale (zéro), puis tu le lèves à la main ; le programme écrit les butées (−30° et +90°).',
        'Avec l\'avant-bras et la pince : tester_epaule.bat --coude 1 (le coude est tenu raide), puis m : mesure de l\'effort à 6 hauteurs.',
        'Avec le ressort : refais m, change de trou, garde celui qui donne l\'effort le plus faible.'],
       'Si une sécurité s\'arrête, l\'épaule RETIENT le bras (force réduite) au lieu de le lâcher. Garde quand même la main près de l\'interrupteur.')
def e_moteur(ax):
    pcs = FIXE() + bras_pale(20.0)
    pcs = [(m, c if k > 0 else COUL['bati']) for k, (m, c) in enumerate(pcs)]
    pcs += [(E.ressort(20.0, TROU_CONSEILLE, 10)[0], COUL['ressort'])]
    dessiner(ax, pcs, marge=0.55)

def page_pieces(pdf, n):
    fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
    fig.suptitle('Épaule — les pièces (regarde-les bien avant de commencer)', fontsize=20, weight='bold', y=0.985)
    liste = [('Bâti', E.BATI, COUL['bati'], '× 1'), ('Berceau à inserts', E.BERCEAU_C, COUL['berceau'], '× 2'),
             ('Bride du berceau', E.BRIDE_C, COUL['bride'], '× 1 (+ celle du coude)'), ('Haut du bras, moitié basse', E.BRAS_BAS, COUL['bas'], '× 1'),
             ('Haut du bras, moitié haute', E.BRAS_HAUT, COUL['haut'], '× 1'), ('Ressort 70 × 10 × 1,2', E.ressort(70, TROU_CONSEILLE, 10)[0], COUL['ressort'], '× 1')]
    for k, (nom, m, c, q) in enumerate(liste):
        ax = fig.add_subplot(3, 3, k + 1, projection='3d'); dessiner(ax, [(m, c)], marge=0.75)
        ax.set_title(f'{nom}  {q}', fontsize=14, weight='bold', color=c if c != COUL['berceau'] else '#4a6a9a')
    vis_l = [('Inserts M3', insert(0, 0, 0), LAITON, '× 17'), ('Vis M3 × 10', vis(0, 0, 0, 10, 1), NOIR, '× 12'),
             ('Vis M3 × 30', vis(0, 0, 0, 30, 1), NOIR, '× 4')]
    for k, (nom, m, c, q) in enumerate(vis_l):
        ax = fig.add_subplot(3, 3, 7 + k, projection='3d'); dessiner(ax, [(m, c)], cadre=(-10, 10, -6, 34, -10, 10), marge=0.9)
        ax.set_title(f'{nom}  {q}', fontsize=14, weight='bold')
    fig.text(0.04, 0.03, 'Et aussi : 8 vis M2,5 des disques du servo, 2 vis M3 × 16 + 2 rondelles et 1 écrou M3 (ressort), un serre-joint pour le pied.\n'
             'Couleurs : chaque pièce garde la même couleur dans tout le plan. Une pièce pâle = déjà montée aux étapes d\'avant.', fontsize=13)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08, hspace=0.3, wspace=0.02)
    fig.savefig(E.OUT / f'plan_montage_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)

if __name__ == '__main__':
    with PdfPages(E.OUT / 'plan_montage_epaule.pdf') as pdf:
        page_pieces(pdf, 0)
        for n, (titre, il_faut, faire, attention, f) in enumerate(ETAPES, 1):
            fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
            ax = fig.add_axes([0.0, 0.02, 0.6, 0.86], projection='3d'); f(ax)
            fig.text(0.03, 0.94, f'Étape {n} / {len(ETAPES)} — {titre}', fontsize=24, weight='bold')
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
