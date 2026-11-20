"""Plan de montage illustré de la FLEXION du poignet (servo n° 6) : une page par étape, PDF + PNG.
Les dessins montrent le bras couché sur le côté : le socle du berceau est en bas, l'axe du servo est vertical."""
import sys, os
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import generer_flexion as X, plan_montage_epaule_outils as PM
from generer_epaule import box, placer, F, B
import manifold3d as mf
P = X.P
C = {'support': '#8e6bbf', 'fourche': '#3aa6a6', 'servo': '#3a3a3a', 'bride': '#e0602a', 'insert': '#d4a72c', 'rot': '#5b8bd6'}
GRIS, GS, NOIR = PM.GRIS, PM.GRIS_SERVO, PM.NOIR
D = lambda m: placer(m, [[1, 0, 0], [0, 0, 1], [0, 1, 0]], (0, 0, 0))          # dessin : l'axe Y du bras devient la verticale
T = lambda m, d: m.translate(d)
def cz(x, y, z0, z1, d, n=16): return mf.Manifold.cylinder(z1 - z0, d / 2, d / 2, n).translate((x, y, z0))
def vis(x, y, z, L, d=3.0, bas=False):
    return (cz(x, y, z - L, z, d) + cz(x, y, z - L - d, z - L, d * 1.8, 20)) if bas else (cz(x, y, z, z + L, d) + cz(x, y, z + L, z + L + d, d * 1.8, 20))
AVB = D(box(-70, -X.EP_F / 2, -12, 0, X.EP_F / 2, 12))
SUP, SERVO, BRIDE, BASSE, HAUTE = D(X.SUPPORT), D(X.SERVO), D(X.BRIDE), D(X.BASSE), D(X.HAUTE)
XA = X.X_AXE; XE = XA + X.L_FOURCHE - X.ENT_L / 2                              # axe ; milieu de l'entretoise du bout
bb = X.BRIDE.bounding_box(); XBR, ZBR, Y_BR = (bb[0] + bb[3]) / 2, (bb[5] - bb[2]) / 2 - 4, bb[4]
DISQUE = [(XA + sx * F.trou_d, sz * F.trou_d) for sx in (1, -1) for sz in (1, -1)]
Y_HAUT, Y_BAS = X.EP_F / 2, -X.EP_F / 2
ETAPES = []
def etape(titre, il_faut, faire, attention=None, leg=()):
    def deco(f): ETAPES.append((titre, il_faut, faire, attention, leg, f)); return f
    return deco

@etape('Préparer le servo n° 6', ['un servo neuf, seul sur le câble', 'le logiciel FD', 'ses 2 disques et ses 8 petites vis'],
       ['Branche ce servo SEUL sur la carte, 12 V allumé, ouvre FD.', 'Donne-lui le numéro 6 (ligne ID), puis Save.', 'Règle ses butées : 1024 (Min) et 3072 (Max), puis Save.',
        'Coupe le 12 V avant de le débrancher.', 'Cette fois il faut les DEUX disques : le palonnier, et le second disque (celui qui tourne librement) monté au dos.'],
       'Contraire du servo n° 5 : ici le second disque est indispensable, la fourche se visse dessus.', [(C['servo'], 'servo n° 6')])
def e1(fig):
    ax, = PM.panneaux(fig, 1); PM.dessiner(ax, [(SERVO, C['servo'])], vue=(22, -55), marge=0.75)
    PM.etiquette(ax, (XA, 0, Y_HAUT - 5), 'palonnier', (90, 50)); PM.etiquette(ax, (XA, 0, Y_BAS + 5), 'second disque, au dos', (110, -50))

@etape('Quatre inserts', ['le support de flexion', 'la moitié BASSE de la fourche', '4 inserts M3 (Ø 4,7 × 3,8)', 'le fer à souder'],
       ['Support : un insert en haut de chacun des 2 piliers (ceux qui recevront la bride).', 'Moitié basse de la fourche : un insert dans chacun des 2 trous du dessus du bloc.', 'À fleur de la surface, bien droits. Laisse refroidir.'],
       'Les 2 moitiés de la fourche se ressemblent : la BASSE a les trous de 4 mm (inserts), la HAUTE a des trous qui la traversent.', [(C['support'], 'support'), (C['fourche'], 'fourche, moitié basse'), (C['insert'], 'insert M3')])
def e2(fig):
    a1, a2 = PM.panneaux(fig, 2, ['A. Le support : 2 inserts', 'B. La moitié basse : 2 inserts'])
    ins = [(cz(XBR, s * ZBR, Y_BR + 8, Y_BR + 12, 4.7, 20), C['insert']) for s in (1, -1)]
    PM.dessiner(a1, [(SUP, C['support'])] + ins, vue=(28, -55), marge=0.85)
    for s in (1, -1): PM.guide(a1, (XBR, s * ZBR, Y_BR + 8), (XBR, s * ZBR, Y_BR - 6))
    yb = Y_BAS + F.plaque_T + F.demi_H
    ins = [(cz(XE, s * F.vis_M3_Y, yb + 8, yb + 12, 4.7, 20), C['insert']) for s in (1, -1)]
    PM.dessiner(a2, [(BASSE, C['fourche'])] + ins, vue=(28, -55), marge=0.7)
    for s in (1, -1): PM.guide(a2, (XE, s * F.vis_M3_Y, yb + 8), (XE, s * F.vis_M3_Y, yb))

@etape('La fourche sur le servo, à plat sur la table', ['le servo n° 6 avec ses 2 disques', 'les 2 moitiés de la fourche', '8 vis du servo (5,3 mm)'],
       ['Travaille sur la table, pas sur le bras : les vis sont verticales, c\'est bien plus facile.', 'A. Retourne le servo, second disque vers le haut. Pose la moitié BASSE dessus, son bloc tourné vers le servo, et visse 4 vis.',
        'B. Remets le servo à l\'endroit, palonnier vers le haut. Pose la moitié HAUTE dessus, son bloc en face de l\'autre, et visse 4 vis.',
        'Tourne chaque disque à la main pour mettre ses 4 trous en face avant de visser.', 'Les deux blocs du bout se font face, avec un petit jour entre eux : c\'est normal.'],
       'Serre jusqu\'au contact, sans forcer : 2,5 mm de plastique sous chaque tête, comme sur l\'avant-bras.', [(C['fourche'], 'fourche'), (C['servo'], 'servo n° 6')])
def e3(fig):
    a1, a2 = PM.panneaux(fig, 2, ['A. Moitié basse sur le second disque (servo retourné)', 'B. Moitié haute sur le palonnier'])
    ret = lambda m: m.mirror((0, 0, 1))
    PM.dessiner(a1, [(ret(SERVO), C['servo']), (T(ret(BASSE), (0, 0, 18)), C['fourche'])] + [(vis(x, z, -Y_BAS + 18 + 8, 5.3, 2.5), NOIR) for x, z in DISQUE], vue=(26, -55), marge=0.82)
    PM.dessiner(a2, [(SERVO, C['servo']), (BASSE, GRIS), (T(HAUTE, (0, 0, 18)), C['fourche'])] + [(vis(x, z, Y_HAUT + 18 + 8, 5.3, 2.5), NOIR) for x, z in DISQUE], vue=(26, -55), marge=0.82)
    PM.etiquette(a2, (XA, 0, Y_HAUT + 30), '4 vis du servo', (150, -20), taille=11); PM.etiquette(a1, (XA, 0, -Y_BAS + 30), '4 vis du servo', (150, -20), taille=11)

@etape('Le support sur l\'avant-bras', ['le support de flexion', 'les 2 vis M3 × 30 qui tenaient la pince'],
       ['Coupe le 12 V. Retire la pince (ou le support de rotation) du bout de l\'avant-bras : 2 vis M3 × 30.', 'Enfile le manchon du support sur le bout de l\'avant-bras, jusqu\'au fond.',
        'Le grand socle plat du support vient du côté de l\'avant-bras où il n\'y a PAS les têtes des 2 vis.', 'Remets les 2 vis M3 × 30 par le même côté qu\'avant.'],
       'Dessin : bras couché sur le côté. En vrai, le socle plat est vertical, sur le flanc du bras.', [(C['support'], 'support de flexion')])
def e4(fig):
    ax, = PM.panneaux(fig, 1); d = (30, 0, 0)
    pcs = [(AVB, GRIS), (T(SUP, d), C['support'])] + [(T(vis(-X.ENT_L / 2, dz, P.YI + P.MUR + 10, 30, bas=False), d), NOIR) for dz in (-F.vis_M3_Y, F.vis_M3_Y)]
    PM.dessiner(ax, pcs, vue=(26, -58), cadre=(-75, 110, -40, 40, -35, 75), marge=0.62)
    PM.guide(ax, (30, 0, 0), (0, 0, 0)); PM.etiquette(ax, (-40, 0, 22), 'avant-bras', (-60, 70)); PM.etiquette(ax, (30 - X.ENT_L / 2, 0, P.YI + 45), '2 vis M3 × 30', (90, 30))
    PM.etiquette(ax, (60, -20, X.Y_SOCLE), 'socle plat', (110, -40))

@etape('Le servo dans le berceau, puis la bride', ['le servo avec sa fourche', '2 câbles de servo', 'la bride du berceau, 2 vis M3 × 10'],
       ['Branche les 2 câbles sur le servo.', 'Descends le servo dans le berceau, palonnier vers le haut : la moitié basse de la fourche passe entre le socle et le servo.',
        'Les câbles sortent par les côtés, dans leur passage.', 'Pose la bride sur le servo, entre les 2 piliers, et visse ses 2 vis M3 × 10.', 'Fais pivoter la fourche à la main, un quart de tour de chaque côté : elle ne doit rien toucher.'],
       'Si la fourche frotte sur le socle, le servo n\'est pas descendu jusqu\'en bas.', [(C['servo'], 'servo et fourche'), (C['bride'], 'bride')])
def e5(fig):
    ax, = PM.panneaux(fig, 1); dz = 34
    pcs = [(AVB, GRIS), (SUP, GRIS)] + [(T(m, (0, 0, dz)), c) for m, c in ((SERVO, C['servo']), (BASSE, C['fourche']), (HAUTE, C['fourche']))] + [(T(BRIDE, (0, 0, dz + 30)), C['bride'])]
    pcs += [(vis(XBR, s * ZBR, Y_BR + dz + 38, 10), NOIR) for s in (1, -1)]
    PM.dessiner(ax, pcs, vue=(24, -58), cadre=(-75, 110, -40, 40, -35, 120), marge=0.6)
    PM.guide(ax, (XA, 0, dz + Y_BAS), (XA, 0, Y_BAS)); PM.etiquette(ax, (XBR, 0, Y_BR + dz + 32), 'bride', (-90, 40)); PM.etiquette(ax, (XBR, -ZBR, Y_BR + dz + 50), '2 vis M3 × 10', (90, 30))

@etape('Le support de rotation au bout de la fourche', ['le support de rotation (bleu)', '2 vis M3 × 30'],
       ['Enfile le manchon du support de rotation sur le bout de la fourche, jusqu\'au fond, ses oreilles vers le HAUT de la pince.', 'Passe les 2 vis M3 × 30 par le manchon : elles traversent la moitié haute et se vissent dans les inserts de la moitié basse.',
        'Ces 2 vis ferment la fourche ET tiennent le support de rotation.', 'Continue ensuite avec le plan du poignet « rotation », à partir de son étape 4 (le servo n° 5 glisse par le haut).'],
       'Sans le poignet de rotation : enfile la pince à la place, avec les mêmes 2 vis.', [(C['rot'], 'support de rotation'), (C['fourche'], 'fourche')])
def e6(fig):
    ax, = PM.panneaux(fig, 1); ROT = D(X.au_bout(P.SUPPORT)); d = (30, 0, 0)
    pcs = [(AVB, GRIS), (SUP, GRIS), (SERVO, GS), (BRIDE, GRIS), (BASSE, C['fourche']), (HAUTE, C['fourche']), (T(ROT, d), C['rot'])]
    pcs += [(T(vis(XA + X.L_FOURCHE - X.ENT_L / 2, dz, P.YI + P.MUR + 10, 30), d), NOIR) for dz in (-F.vis_M3_Y, F.vis_M3_Y)]
    PM.dessiner(ax, pcs, vue=(24, -58), cadre=(-40, 190, -45, 45, -35, 75), marge=0.62)
    PM.guide(ax, (XA + X.L_FOURCHE + 30, 0, 0), (XA + X.L_FOURCHE, 0, 0)); PM.etiquette(ax, (XA + X.L_FOURCHE + 22, 0, P.YI + 45), '2 vis M3 × 30', (90, 30))

@etape('Câbles et essai à la main', ['3 câbles de servo, des colliers'],
       ['Câbles : coude → servo n° 6 → servo n° 5 → servo n° 4 (pince).', 'À chaque articulation, laisse une boucle souple ; attache le surplus le long de l\'avant-bras.',
        'Sans courant, plie le poignet à la main : un quart de tour vers le haut, un quart de tour vers le bas. Rien ne doit toucher ni tirer.', 'Fais de même pour la rotation de la pince.'],
       'Ne mets pas le 12 V pour bouger ce servo tant que le programme tester_flexion n\'est pas prêt : ce poignet porte la pince, il doit être RETENU, jamais lâché.', [(C['fourche'], 'fourche')])
def e7(fig):
    a1, a2 = PM.panneaux(fig, 2, ['Poignet droit', 'Plié de 60° vers le bas'])
    for ax, a in ((a1, 0), (a2, -60)):
        pcs = [(AVB, GRIS), (SUP, C['support']), (SERVO, GS), (BRIDE, C['bride'])] + [(D(X.flechir(m, a)), C['fourche']) for m in (X.BASSE, X.HAUTE)]
        pcs += [(D(X.flechir(m, a)), c) for m, c in zip(X.suite(), [C['rot'], GRIS, GS, '#c9a35a', '#c9a35a', GS] + ['#7fb069'] * 4)]
        PM.dessiner(ax, pcs, vue=(8, -90), marge=0.62)

def page_pieces(pdf):
    fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
    fig.suptitle('Flexion du poignet (servo n° 6) : les pièces', fontsize=20, weight='bold', y=0.985)
    for k, (nom, m, c, vue) in enumerate([('Support de flexion (à imprimer)', SUP, C['support'], (28, -55)), ('Fourche, moitié BASSE (à imprimer) : 2 trous pour inserts', BASSE, C['fourche'], (28, -55)),
                                          ('Fourche, moitié HAUTE (à imprimer) : trous traversants', HAUTE.mirror((0, 0, 1)), C['fourche'], (28, -55)), ('Bride du berceau (la même qu\'au coude)', BRIDE, C['bride'], (28, -55))]):
        ax = fig.add_subplot(2, 2, k + 1, projection='3d'); PM.dessiner(ax, [(m, c)], vue=vue, marge=0.72); ax.set_title(nom, fontsize=14, weight='bold', color=c)
    fig.text(0.03, 0.03, 'Visserie : 2 vis M3 × 30 (manchon) · 8 vis du servo n° 6 (5,3 mm) · 2 vis M3 × 30 (bout de la fourche) · 2 vis M3 × 10 (bride) · 4 inserts M3.\n'
             'PROTOTYPE : vérifié par le calcul, jamais monté. Les dessins montrent le bras couché sur le côté. EN COULEUR = ce que tu poses · GRIS = déjà monté.', fontsize=13)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.1, hspace=0.15, wspace=0.02)
    fig.savefig(X.OUT / 'plan_montage_flexion_00.png', dpi=90); pdf.savefig(fig); plt.close(fig)

if __name__ == '__main__':
    with PdfPages(X.OUT / 'plan_montage_flexion.pdf') as pdf:
        page_pieces(pdf)
        for n, (titre, il_faut, faire, attention, leg, f) in enumerate(ETAPES, 1):
            fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white'); f(fig)
            PM.mise_en_page(fig, n, len(ETAPES), titre, il_faut, faire, attention, leg)
            fig.savefig(X.OUT / f'plan_montage_flexion_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)
    print('ok', len(ETAPES), 'étapes')
