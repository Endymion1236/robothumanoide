"""Plan de montage illustré du poignet (rotation de la pince) : une page par étape, PDF + PNG."""
import sys, os
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import generer_poignet as P, plan_montage_epaule_outils as PM
from generer_pince import box
G, V = P.G, P.V
C = {'support': '#5b8bd6', 'barre': '#e0602a', 'base': '#c9a35a', 'servo': '#3a3a3a', 'pince': '#7fb069', 'insert': '#d4a72c'}
GRIS, GS, NOIR = PM.GRIS, PM.GRIS_SERVO, PM.NOIR
AVB = box(-70, -P.FOURCHE_EP / 2, -P.FOURCHE_L / 2, 0, P.FOURCHE_EP / 2, P.FOURCHE_L / 2)
T = lambda m, d: m.translate(d)
def vis_z(x, y, z, L, d=3.0): return P.cyl_z(x, y, z, z + L, d, 12) + P.cyl_z(x, y, z + L, z + L + d, d * 1.8, 20)
def vis_y(x, y, z, L, d=3.0): return P.cyl_y(y - L, y, x, z, d, 12) + P.cyl_y(y, y + d, x, z, d * 1.8, 20)
def vis_x(x, y, z, L, d=2.5): return P.cyl_x(x - L, x, y, z, d, 12) + P.cyl_x(x, x + d, y, z, d * 1.8, 20)
XB, YB = sum(P.X_BARRE) / 2, P.YP + P.MUR + P.BOSS / 2
CADRE = (-75, 60, -45, 45, -25, 60)
ETAPES = []
def etape(titre, il_faut, faire, attention=None, leg=()):
    def deco(f): ETAPES.append((titre, il_faut, faire, attention, leg, f)); return f
    return deco

@etape('Préparer le servo n° 5', ['un servo neuf, seul sur le câble', 'le logiciel FD'],
       ['Branche ce servo SEUL sur la carte, 12 V allumé, ouvre FD.', 'Donne-lui le numéro 5 (ligne ID), puis Save.',
        'Règle ses butées : 1024 (Min) et 3072 (Max), puis Save. Cela fait un quart de tour de chaque côté.',
        'Coupe le 12 V avant de le débrancher.', 'Garde son palonnier (le disque en aluminium). NE MONTE PAS le second disque, celui qui tourne librement au dos.'],
       'Le disque libre du dos ajouterait 3,3 mm : le servo ne descendrait plus dans le support.', [(C['servo'], 'servo n° 5')])
def e1(fig):
    ax, = PM.panneaux(fig, 1); PM.dessiner(ax, [(P.SERVO, C['servo'])], vue=(20, -50), marge=0.75)
    PM.etiquette(ax, (P.X_PAL, 0, 0), 'palonnier (gardé)', (90, 50)); PM.etiquette(ax, (P.X_DOS, 0, 20), 'dos : pas de second disque', (-140, 60))

@etape('Deux inserts dans le support', ['le support du poignet', '2 inserts M3 (Ø 4,7 × 3,8)', 'le fer à souder'],
       ['Pose le support comme sur le dessin, ses deux oreilles en haut.', 'Enfonce un insert au fer dans le trou de chaque oreille, à fleur du dessus.', 'Laisse refroidir sans toucher.'],
       'Insert bien droit et à fleur : s\'il dépasse, la barre ne se posera pas à plat.', [(C['support'], 'support'), (C['insert'], 'insert M3')])
def e2(fig):
    ax, = PM.panneaux(fig, 1)
    PM.dessiner(ax, [(P.SUPPORT, C['support'])] + [(P.cyl_z(XB, s * YB, P.Z_MURS + 10, P.Z_MURS + 14, 4.7, 20), C['insert']) for s in (1, -1)], vue=(28, -50), marge=0.7)
    for s in (1, -1): PM.guide(ax, (XB, s * YB, P.Z_MURS + 10), (XB, s * YB, P.Z_MURS))
    PM.etiquette(ax, (XB, -YB, P.Z_MURS + 14), '2 inserts', (-90, 40)); PM.etiquette(ax, (-8, P.YI + 2, 0), 'manchon : vers l\'avant-bras', (-150, -60))

@etape('Le support sur l\'avant-bras', ['le support', 'les 2 vis M3 × 30 qui tenaient la pince'],
       ['Coupe le 12 V. Débranche le câble de la pince, puis retire la pince entière (2 vis M3 × 30 sur le côté).', 'Enfile le support sur le bout de l\'avant-bras, à la place de la pince, les oreilles vers le HAUT.',
        'Pousse-le jusqu\'au fond.', 'Remets les 2 vis M3 × 30 par le même côté qu\'avant.'],
       'Le « haut » est le côté où pointait le dessus de la pince (ses plaques), bras à plat.', [(C['support'], 'support')])
def e3(fig):
    ax, = PM.panneaux(fig, 1); d = (28, 0, 0)
    pcs = [(AVB, GRIS), (T(P.SUPPORT, d), C['support'])] + [(T(vis_y(-P.ENT_B / 2, P.YI + P.MUR + 14, dz, 30), d), NOIR) for dz in (-P.VIS_ENT_Y, P.VIS_ENT_Y)]
    PM.dessiner(ax, pcs, vue=(24, 122), cadre=(-75, 80, -45, 60, -25, 50), marge=0.62)
    PM.guide(ax, (28, 0, 0), (0, 0, 0)); PM.etiquette(ax, (-40, 0, 12), 'avant-bras', (60, 70)); PM.etiquette(ax, (28 - P.ENT_B / 2, P.YI + 22, 0), '2 vis M3 × 30', (-20, -90))
    for dz in (-P.VIS_ENT_Y, P.VIS_ENT_Y): PM.guide(ax, (28 - P.ENT_B / 2, P.YI + 14, dz), (28 - P.ENT_B / 2, P.YI, dz))

@etape('Le servo glisse par le haut', ['le servo n° 5', '2 câbles de servo'],
       ['Branche les 2 câbles sur le servo AVANT de le glisser : un de chaque côté.', 'Présente le servo au-dessus du support, palonnier vers l\'AVANT (côté pince), le bout où est le palonnier en BAS.',
        'Fais-le descendre : son dos passe derrière les rails, sa partie haute passe sous les 2 lèvres de devant.', 'Chaque câble descend dans sa fente, sur le côté.', 'Pousse jusqu\'en bas : le dessus du servo arrive à fleur des murs.'],
       'S\'il force, ne tape pas : vérifie que le second disque n\'est pas monté au dos et qu\'aucun câble n\'est coincé.', [(C['servo'], 'servo n° 5'), (C['support'], 'support')])
def e4(fig):
    ax, = PM.panneaux(fig, 1)
    PM.dessiner(ax, [(AVB, GRIS), (P.SUPPORT, C['support']), (T(P.SERVO, (0, 0, 42)), C['servo'])], vue=(22, -52), cadre=(-75, 60, -45, 45, -25, 95), marge=0.6)
    PM.guide(ax, (20, 0, 42 + P.Z_PRES), (20, 0, P.Z_PRES)); PM.etiquette(ax, (P.X_PAL, 0, 42), 'palonnier', (70, 40))
    PM.etiquette(ax, (13, -P.YP - 3, 25), 'fente du câble', (-130, 40)); PM.etiquette(ax, (P.X_LEVRE1, -P.YP + 1, 30), 'lèvre', (110, -40))

@etape('La barre ferme le haut', ['la barre', '2 vis M3 × 10'],
       ['Pose la barre sur le haut du support, sa languette vers le BAS, du côté de l\'avant-bras.', 'La languette descend derrière le haut du servo.', 'Visse les 2 vis M3 × 10 dans les inserts.',
        'Vérifie à la main : le servo ne bouge plus dans son logement.'],
       'Si la barre ne se pose pas à plat, le servo n\'est pas descendu jusqu\'en bas.', [(C['barre'], 'barre')])
def e5(fig):
    ax, = PM.panneaux(fig, 1); dz = 22
    pcs = [(AVB, GRIS), (P.SUPPORT, GRIS), (P.SERVO, GS), (T(P.BARRE, (0, 0, dz)), C['barre'])] + [(vis_z(XB, s * YB, P.Z_MURS + dz + 12, 10), NOIR) for s in (1, -1)]
    PM.dessiner(ax, pcs, vue=(24, -52), cadre=(-75, 60, -45, 45, -25, 90), marge=0.6)
    for s in (1, -1): PM.guide(ax, (XB, s * YB, P.Z_MURS + dz + 12), (XB, s * YB, P.Z_MURS))
    PM.etiquette(ax, (5.5, 0, P.Z_MURS + dz - 4), 'languette', (-110, 30)); PM.etiquette(ax, (XB, -YB, P.Z_MURS + dz + 25), '2 vis M3 × 10', (-110, 30))

@etape('La base de la pince sur le palonnier', ['la base de pince « poignet » (seule, rien dessus)', 'les 4 vis du servo n° 5 (5,3 mm)', 'ton tournevis fin à tige longue'],
       ['Démonte l\'ancienne pince : garde le servo n° 4, la bride, les 2 plaques et leurs mâchoires. L\'ancienne base ne sert plus.', 'Présente la nouvelle base, son moyeu rond contre le palonnier, la plaque de la base en BAS.',
        'Tourne le palonnier à la main pour que ses 4 trous arrivent en face de ceux du moyeu.', 'Passe le tournevis par l\'avant de la base : 2 vis par le logement du servo, 2 vis par les 2 passages à côté.',
        'Serre les 4 vis à tour de rôle, jusqu\'au contact, sans forcer.'],
       'Les 4 vis ne prennent que 2,5 mm dans le palonnier : c\'est tout ce qui tient la pince. Si une vis ne mord pas, arrête et dis-le-moi.', [(C['base'], 'base de la pince')])
def e6(fig):
    a1, a2 = PM.panneaux(fig, 2, ['A. On approche la base', 'B. Les 4 vis, par l\'avant']); d = (26, 0, 0)
    PM.dessiner(a1, [(AVB, GRIS), (P.SUPPORT, GRIS), (P.BARRE, GRIS), (P.SERVO, GS), (T(P.BASE, d), C['base'])], vue=(24, -58), cadre=(-40, 150, -45, 45, -25, 50), marge=0.66)
    PM.guide(a1, (P.X_PAL + 26, 0, 0), (P.X_PAL, 0, 0)); PM.etiquette(a1, (P.X_PAL, 0, 0), 'palonnier', (-60, -60), taille=11); PM.etiquette(a1, (P.X_PAL + 30, 0, 0), 'moyeu', (40, 60), taille=11)
    pcs = [(P.BASE, C['base'])] + [(vis_x(P.X_FOND_PINCE + 60, y, z, 5.3), NOIR) for y, z in P.TROUS]
    PM.dessiner(a2, pcs, vue=(28, 35), marge=0.9)
    for y, z in P.TROUS: PM.guide(a2, (P.X_FOND_PINCE + 55, y, z), (P.X_PAL + 3, y, z))
    PM.etiquette(a2, (P.X_FOND_PINCE + 62, 0, 0), '4 vis du servo', (90, 50), taille=11)

@etape('Remonter la pince et brancher', ['le servo n° 4, la bride, 2 vis M3 × 10', 'les 2 plaques avec leurs mâchoires', 'un câble de 90 cm, des colliers'],
       ['Pose le servo n° 4 dans la base, puis la bride et ses 2 vis.', 'Remonte la plaque fixe et la plaque mobile comme sur le plan de la pince V4 (étapes 3 et 4).',
        'Câbles : coude → servo n° 5, puis servo n° 5 → servo n° 4.', 'Entre le n° 5 et le n° 4, laisse une BOUCLE souple d\'une dizaine de centimètres : c\'est elle qui laisse tourner la pince.',
        'Enroule le surplus et attache-le le long de l\'avant-bras, loin du coude.', 'Sans courant, tourne la pince à la main d\'un quart de tour de chaque côté : rien ne doit tirer ni se coincer.'],
       'Ne mets pas encore le 12 V : le programme d\'essai du poignet (tester_poignet) arrive, il règlera le milieu.', [(C['pince'], 'pince V4'), (C['base'], 'base')])
def e7(fig):
    a1, a2 = PM.panneaux(fig, 2, ['Pince droite', 'Pince tournée d\'un quart de tour'])
    for ax, a in ((a1, 0), (a2, 90)):
        pcs = [(AVB, GRIS), (P.SUPPORT, GRIS), (P.BARRE, GRIS), (P.SERVO, GS), (P.rouler(P.BASE, a), C['base'])]
        pcs += [(P.rouler(x, a), c) for x, c in zip(P.pince_complete(-13.1), (C['base'], C['servo'], C['pince'], C['pince'], C['pince'], C['pince']))]
        PM.dessiner(ax, pcs, vue=(24, -58), cadre=(-40, 190, -70, 70, -60, 70), marge=0.66)

def page_pieces(pdf):
    fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
    fig.suptitle('Poignet (rotation de la pince) : les pièces', fontsize=20, weight='bold', y=0.985)
    for k, (nom, m, c, vue) in enumerate([('Support du poignet (à imprimer)', P.SUPPORT, C['support'], (28, -50)), ('Barre (à imprimer, languette en l\'air)', P.BARRE, C['barre'], (-25, -50)),
                                          ('Base de la pince « poignet » (à imprimer)', P.BASE, C['base'], (22, -150)), ('Servo n° 5, sans son second disque', P.SERVO, C['servo'], (20, -50))]):
        ax = fig.add_subplot(2, 2, k + 1, projection='3d'); PM.dessiner(ax, [(m, c)], vue=vue, marge=0.72); ax.set_title(nom, fontsize=14, weight='bold', color=c)
    fig.text(0.03, 0.03, 'Visserie : 2 vis M3 × 30 (celles de la pince) · 2 vis M3 × 10 + 2 inserts M3 (barre) · les 4 vis du servo n° 5 (5,3 mm) · 2 vis M3 × 10 (bride de la pince).\n'
             'PROTOTYPE : vérifié par le calcul, jamais monté. Dans les étapes : EN COULEUR = ce que tu poses · GRIS = déjà monté · pointillés rouges = le trajet.', fontsize=13)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.1, hspace=0.15, wspace=0.02)
    fig.savefig(P.OUT / 'plan_montage_poignet_00.png', dpi=90); pdf.savefig(fig); plt.close(fig)

if __name__ == '__main__':
    with PdfPages(P.OUT / 'plan_montage_poignet.pdf') as pdf:
        page_pieces(pdf)
        for n, (titre, il_faut, faire, attention, leg, f) in enumerate(ETAPES, 1):
            fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white'); f(fig)
            PM.mise_en_page(fig, n, len(ETAPES), titre, il_faut, faire, attention, leg)
            fig.savefig(P.OUT / f'plan_montage_poignet_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)
    print('ok', len(ETAPES), 'étapes')
