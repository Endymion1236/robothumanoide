"""Plan de montage illustré de la pince V4 (sans engrenages) : une page par étape, PDF + PNG."""
import sys, os, math
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import generer_pince as G, generer_pince_v4 as V, plan_montage_epaule_outils as PM
C = {'base': '#c9a35a', 'servo': '#3a3a3a', 'fixe': '#5b8bd6', 'mobile': '#e0602a', 'mach': '#7fb069', 'tapis': '#555555'}
GRIS, GS, NOIR = PM.GRIS, PM.GRIS_SERVO, PM.NOIR
T = lambda m, dz: m.translate((0, 0, dz))
def vis(x, y, z_bas, L, d=3.0): return G.cyl(x, y, z_bas, z_bas + L, d, 12) + G.cyl(x, y, z_bas + L, z_bas + L + d, d * 1.8, 20)
D_MIL = V.V4_MILIEU if hasattr(V, 'V4_MILIEU') else -13.1
VP = [(G.AX + G.CERCLE_TROUS / 2 * math.cos(math.radians(45 + 90 * k)), G.AY + G.CERCLE_TROUS / 2 * math.sin(math.radians(45 + 90 * k))) for k in range(4)]
CADRE = (-30, 150, -70, 70, -25, 70)
ETAPES = []
def etape(titre, il_faut, faire, attention=None, leg=()):
    def deco(f): ETAPES.append((titre, il_faut, faire, attention, leg, f)); return f
    return deco

@etape('Démonter l\'ancienne pince', ['la pince V3', 'une clé Allen, un tournevis'],
       ['Coupe le 12 V. Tu peux laisser la pince sur l\'avant-bras.', 'Retire : les 2 engrenages, les 2 bras libres, les 2 plaques des doigts, les roulements.',
        'Dévisse les 2 mâchoires vertes de leurs plaques : tu les gardes, avec leurs inserts.', 'Il reste : la base, le servo (palonnier en place) et la bride.'],
       'Les 2 mâchoires sont identiques : elles vont indifféremment d\'un côté ou de l\'autre.', [(C['base'], 'base et bride (gardées)'), (C['servo'], 'servo'), (C['mach'], 'mâchoires (gardées)')])
def e1(fig):
    ax, = PM.panneaux(fig, 1)
    PM.dessiner(ax, [(G.BASE, C['base']), (G.BRIDE, C['base']), (G.SERVO, C['servo']), (V.MACH_F.translate((0, -25, 0)), C['mach']), (V.MACH_M.translate((0, 25, 0)), C['mach'])], vue=(28, -55), cadre=CADRE, marge=0.62)
    PM.etiquette(ax, (G.AX, G.AY, G.Z0), 'palonnier', (-30, 80)); PM.etiquette(ax, (G.AX, -G.AY, G.Z0), 'poteau de l\'ancien\nengrenage B', (120, 60)); PM.etiquette(ax, (*G.P_LIBRE[1], G.Z_LIBRE), 'poteau du bras libre', (-90, -70))

@etape('Une mâchoire sous chaque plaque', ['les 2 plaques neuves', 'les 2 mâchoires', '4 vis M3 × 10'],
       ['Pose chaque plaque à l\'envers sur la table, ou tiens la mâchoire dessous.', 'Le CREUX de la mâchoire regarde vers l\'intérieur de la pince (vers l\'autre mâchoire).',
        '2 vis M3 × 10 par plaque, par le dessus, dans les inserts de la mâchoire.', 'Sur la plaque bleue, les têtes s\'enfoncent dans 2 petits logements.'],
       'Si une vis ne mord pas, l\'insert est enfoncé trop loin dans la mâchoire : essaie une M3 × 12.', [(C['fixe'], 'plaque fixe'), (C['mobile'], 'plaque mobile'), (C['mach'], 'mâchoire')])
def e2(fig):
    a1, a2 = PM.panneaux(fig, 2, ['A. Plaque fixe (bleue)', 'B. Plaque mobile (orange)'])
    PM.dessiner(a1, [(T(V.PF, 25), C['fixe']), (V.MACH_F, C['mach'])] + [(vis(x, y, V.ZF1 + 25 + 8, 10), NOIR) for x, y in V._vf], vue=(25, -60), marge=0.7)
    for x, y in V._vf: PM.guide(a1, (x, y, V.ZF1 + 30), (x, y, G.Z_DOIGT))
    PM.etiquette(a1, (V.XC, V.YF, 0), 'creux vers\nl\'intérieur', (110, 20), taille=11)
    PM.dessiner(a2, [(T(V.PM, 25), C['mobile']), (V.MACH_M, C['mach'])] + [(vis(x, y, V.ZT + 25 + 8, 10), NOIR) for x, y in V._vm], vue=(25, 120), marge=0.88)
    for x, y in V._vm: PM.guide(a2, (x, y, V.ZT + 30), (x, y, G.Z_DOIGT))
    PM.etiquette(a2, (V.XC, V.YM, 0), 'creux vers\nl\'intérieur', (110, 20), taille=11)

@etape('La plaque fixe sur ses 2 poteaux', ['la plaque fixe avec sa mâchoire', '1 vis M3 × 16', '1 vis M3 × 10'],
       ['La plaque se pose sur 2 poteaux de la base, du même côté.', 'Son pied rond descend sur le poteau de l\'ancien engrenage B : vis M3 × 16, tête noyée dans son logement.',
        'L\'autre bout se pose sur le poteau du bras libre : vis M3 × 10.', 'Serre les deux : la mâchoire fixe ne doit plus bouger du tout.'],
       'Si le pied rond ne touche pas son poteau : retire les rondelles qui restaient dessus.', [(C['fixe'], 'plaque fixe')])
def e3(fig):
    ax, = PM.panneaux(fig, 1); dz = 22
    pcs = [(G.BASE, GRIS), (G.BRIDE, GRIS), (G.SERVO, GS), (T(V.PF, dz), C['fixe']), (T(V.MACH_F, dz), C['mach']),
           (vis(*V.POT_B, V.ZF1 - 4 + dz + 12, 16), NOIR), (vis(*V.POT_L, V.ZF1 + dz + 12, 10), NOIR)]
    PM.dessiner(ax, pcs, vue=(28, -55), cadre=CADRE, marge=0.62)
    PM.guide(ax, (*V.POT_B, V.ZF1 + dz + 8), (*V.POT_B, V.Z_POT_B)); PM.guide(ax, (*V.POT_L, V.ZF1 + dz + 12), (*V.POT_L, V.ZF0))
    PM.etiquette(ax, (*V.POT_B, V.ZF1 + dz + 30), 'M3 × 16', (70, 50)); PM.etiquette(ax, (*V.POT_L, V.ZF1 + dz + 24), 'M3 × 10', (-80, 50))
    PM.etiquette(ax, (*V.POT_B, V.ZF1 + dz - 3), 'pied rond', (-110, -25))

@etape('La plaque mobile sur le palonnier', ['la plaque mobile avec sa mâchoire', 'les 4 vis du servo (5,3 mm)', 'un tournevis fin'],
       ['Pose le moyeu rond de la plaque sur le palonnier.', 'Tourne-la jusqu\'à ce que ses 4 trous tombent sur ceux du palonnier, mâchoire à peu près en face de l\'autre.',
        'Les 4 vis descendent au fond de 4 puits : visse-les à tour de rôle, sans forcer.', 'L\'angle exact n\'a pas d\'importance : le programme le règlera.'],
       'Les têtes sont au fond des puits : il ne reste que 2,8 mm de plastique dessous. Serre jusqu\'au contact, pas plus.', [(C['mobile'], 'plaque mobile')])
def e4(fig):
    ax, = PM.panneaux(fig, 1); dz = 25; pm, mm, _ = V.mobile(D_MIL)
    pcs = [(G.BASE, GRIS), (G.BRIDE, GRIS), (G.SERVO, GS), (V.PF, GRIS), (V.MACH_F, GRIS), (T(pm, dz), C['mobile']), (T(mm, dz), C['mach'])] + [(vis(x, y, V.ZT + dz + 10, 5.3, 2.5), NOIR) for x, y in VP]
    PM.dessiner(ax, pcs, vue=(30, 125), cadre=CADRE, marge=0.62)
    PM.guide(ax, (G.AX, G.AY, V.ZT + dz + 10), (G.AX, G.AY, G.Z0)); PM.etiquette(ax, (G.AX, G.AY, V.ZT + dz + 20), '4 vis du servo', (90, 40)); PM.etiquette(ax, (G.AX, G.AY, G.Z0 - 2), 'palonnier', (110, -40))

@etape('Le tapis antidérapant', ['le tapis de 2 mm', 'des ciseaux, du double face fin'],
       ['Découpe 2 rectangles de 40 mm × 60 mm.', 'Colle-les dans le CREUX de chaque mâchoire, sur toute la hauteur.', 'Appuie bien, surtout sur les bords.'],
       'Pas de colle cyanoacrylate : elle durcit ce genre de mousse.', [(C['tapis'], 'tapis')])
def e5(fig):
    ax, = PM.panneaux(fig, 1); pm, mm, tp = V.mobile(8)
    PM.dessiner(ax, [(G.BASE, GRIS), (G.BRIDE, GRIS), (G.SERVO, GS), (V.PF, GRIS), (V.MACH_F, GRIS), (pm, GRIS), (mm, GRIS), (V.TAPIS_F, C['tapis']), (tp, C['tapis'])], vue=(22, 35), cadre=CADRE, marge=0.62)
    PM.etiquette(ax, (V.XC, V.YF + 1, 10), 'tapis', (-90, 60))

@etape('Étalonnage et premier essai', ['bras\\tester_pince.bat (fichier test_pince.py à jour)', 'un pied à coulisse'],
       ['Lance tester_pince.bat, tape e, puis réponds 4 (pince sans engrenages).', 'La force est coupée : règle la mâchoire mobile à la main à 54 mm entre les deux TAPIS, au milieu des mâchoires (58 mm sans tapis).',
        'Tape o pour valider : le servo retient cette position comme son milieu.', 'Essaie : o (ouvrir), puis un gobelet et s (serrer). La largeur affichée doit être celle de l\'objet, à quelques mm près.',
        'Fermée à vide, les bouts des mâchoires se touchent : c\'est normal.'],
       'Si le sens est inversé (o ferme au lieu d\'ouvrir) : supprime sens_pince.json dans le dossier bras et relance.', [(C['mobile'], 'mâchoire mobile'), (C['fixe'], 'mâchoire fixe')])
def e6(fig):
    ax, = PM.panneaux(fig, 1); pm, mm, tp = V.mobile(D_MIL)
    PM.dessiner(ax, [(G.BASE, GRIS), (G.BRIDE, GRIS), (G.SERVO, GS), (V.PF, C['fixe']), (V.MACH_F, C['mach']), (V.TAPIS_F, C['tapis']), (pm, C['mobile']), (mm, C['mach']), (tp, C['tapis'])], vue=(90, -90), cadre=(-30, 150, -70, 70, -20, 60), marge=0.58)
    ax.set_proj_type('ortho'); y1 = V.YF + V.TAPIS; y2 = y1 + 54
    ax.plot([V.XC, V.XC], [y1, y2], [70, 70], color='#c0392b', lw=3, zorder=60); PM.etiquette(ax, (V.XC, (y1 + y2) / 2, 70), '54 mm entre\nles tapis', (-75, 0), '#c0392b')

def page_pieces(pdf):
    fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
    fig.suptitle('Pince V4, sans engrenages : les pièces', fontsize=20, weight='bold', y=0.985)
    for k, (nom, m, c, q, vue) in enumerate([('Plaque fixe (à imprimer)', V.PF, C['fixe'], '× 1', (30, -60)), ('Plaque mobile (à imprimer)', V.PM, C['mobile'], '× 1', (30, 120)),
                                             ('Mâchoire (de la V3, gardée)', V.MACH_F, C['mach'], '× 2', (20, 60)), ('Base, bride, servo (gardés)', G.BASE + G.BRIDE + G.SERVO, C['base'], '', (28, -55))]):
        ax = fig.add_subplot(2, 2, k + 1, projection='3d'); PM.dessiner(ax, [(m, c)], vue=vue, marge=0.72); ax.set_title(f'{nom}  {q}', fontsize=14, weight='bold', color=c)
    fig.text(0.03, 0.03, 'Visserie : les 4 vis du servo (5,3 mm) · 5 vis M3 × 10 · 1 vis M3 × 16 · tapis antidérapant de 2 mm.\n'
             'Dans les étapes : EN COULEUR = ce que tu poses maintenant · GRIS = déjà monté · pointillés rouges = où va la vis.', fontsize=13)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.1, hspace=0.15, wspace=0.02)
    fig.savefig(G.OUT / 'plan_montage_v4_00.png', dpi=90); pdf.savefig(fig); plt.close(fig)

if __name__ == '__main__':
    with PdfPages(G.OUT / 'plan_montage_pince_v4.pdf') as pdf:
        page_pieces(pdf)
        for n, (titre, il_faut, faire, attention, leg, f) in enumerate(ETAPES, 1):
            fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white'); f(fig)
            PM.mise_en_page(fig, n, len(ETAPES), titre, il_faut, faire, attention, leg)
            fig.savefig(G.OUT / f'plan_montage_v4_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)
    print('ok', len(ETAPES), 'étapes')
