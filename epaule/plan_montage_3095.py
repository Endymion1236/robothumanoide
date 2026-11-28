"""Plan de montage illustré de l'épaule STS3095 : une page par étape (PDF + PNG), même présentation que le socle et l'ancienne
épaule. Demandé par Nicolas le 28/11/2026, après l'impression du berceau et des deux moitiés du haut du bras.
PROTOTYPE : l'épaule n'a jamais été montée, ce plan suit le dessin. Lancer après generer_epaule_3095.py."""
import sys, os, math
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import plan_montage_epaule_outils as PM
import generer_epaule_3095 as G
E = PM.E
C = {'bati': '#7fb069', 'berceau': '#5b8bd6', 'bride': '#9b6fd0', 'bas': '#f0a030', 'haut': '#e0602a', 'servo': '#3a3a3a', 'disque': '#b9c2cc', 'coude': '#2f9fae'}
GRIS, GRIS_SERVO, LAITON, NOIR = PM.GRIS, PM.GRIS_SERVO, PM.LAITON, PM.NOIR
T = lambda m, d: m.translate(d)
def insert_z(x, y, z): return G.cyl_z(x, y, z, z + 5.7, 4.8, 20) - G.cyl_z(x, y, z - .1, z + 5.8, 2.6, 12)
def vis_z(x, y, z_bas, L, d=3.0): return G.cyl_z(x, y, z_bas, z_bas + L, d, 12) + G.cyl_z(x, y, z_bas + L, z_bas + L + d, d * 1.8, 20)
QUATRE = [(G.CERCLE_TROUS / 2 * math.cos(math.radians(22.5 + 90 * k)), G.CERCLE_TROUS / 2 * math.sin(math.radians(22.5 + 90 * k))) for k in range(4)]
ENT = [(x + l / 2, s * G.VIS_ENT_Z) for x, l in ((G.ENT_A, G.ENT_A_L), (G.ENT_B, G.ENT_B_L)) for s in (1, -1)]
YJ = G.YC - G.JEU_SERRAGE / 2
SERVO_COMPLET = [(G.SERVO, C['servo']), (G.DISQUES, C['disque'])]
ETAPES = []
def etape(titre, il_faut, faire, attention=None, leg=()):
    def deco(f): ETAPES.append((titre, il_faut, faire, attention, leg, f)); return f
    return deco

@etape('Le gros servo, tout seul', ['le servo STS3095 neuf', 'la carte + 12 V', 'le logiciel FD'],
       ['Vérifie « 12 V » sur l\'étiquette du servo.', 'Branche CE servo seul sur la carte (tout le bras débranché : neuf, il porte sans doute le n° 1, celui du socle).',
        'Donne-lui un numéro libre (le n° 9 par exemple : il prendra le n° 2 quand l\'ancienne épaule sera démontée).',
        'Debug : vitesse 300, position 2048. Les deux disques sont au milieu de leur course : n\'y touche plus.', 'Coupe le 12 V, débranche.'],
       '2048 = haut du bras à l\'HORIZONTALE. Tout le montage se fait dans cette position.', [(C['servo'], 'servo STS3095'), (C['disque'], 'ses 2 disques')])
def e1(fig):
    ax, = PM.panneaux(fig, 1); PM.dessiner(ax, SERVO_COMPLET, vue=(24, 48), marge=0.9)
    PM.etiquette(ax, (0, G.Y_D2, 0), 'disque côté extérieur', (120, 40)); PM.etiquette(ax, (0, G.Y_D1, 0), 'disque côté LOGO', (-150, -60))
    PM.etiquette(ax, (-30, G.YC, 15), 'prises SVG de ce côté\n(opposé au logo)', (150, 90))

@etape('Les 10 inserts', ['le berceau', 'la moitié basse du bras', '10 inserts M3, fer à 230 °C'],
       ['Berceau : 4 inserts dans le socle, par la face PLATE qui ira contre le mur.', 'Berceau : 2 inserts sur le dessus des deux joues (pour la bride).',
        'Moitié basse : 4 inserts sur le dessus des 2 entretoises (les 2 blocs qui dépassent).', 'Chaque insert bien droit, au ras du plastique.'],
       'La moitié HAUTE ne reçoit aucun insert pour l\'instant (celui du ressort est facultatif).', [(C['berceau'], 'berceau'), (C['bas'], 'moitié basse')])
def e2(fig):
    a1, a2, a3 = PM.panneaux(fig, 3, ['A. Socle du berceau : 4', 'B. Dessus des joues : 2', 'C. Moitié basse : 4'])[:3]
    PM.dessiner(a1, [(G.BERCEAU, C['berceau'])] + [(PM.insert(x, z, -12, 1), LAITON) for x, z in G.TROUS_MUR], vue=(18, -62), marge=0.8)
    for x, z in G.TROUS_MUR: PM.guide(a1, (x, -12, z), (x, 0, z))
    PM.dessiner(a2, [(G.BERCEAU, C['berceau'])] + [(insert_z(G.X_VIS_BRIDE, y, G.Z_APPUI + 10), LAITON) for y in G.Y_VIS_BRIDE], vue=(34, 40), marge=0.8)
    for y in G.Y_VIS_BRIDE: PM.guide(a2, (G.X_VIS_BRIDE, y, G.Z_APPUI + 10), (G.X_VIS_BRIDE, y, G.Z_APPUI))
    PM.dessiner(a3, [(G.BRAS_BAS, C['bas'])] + [(PM.insert(x, z, YJ + 12, -1), LAITON) for x, z in ENT], vue=(30, 62), marge=0.8)
    for x, z in ENT: PM.guide(a3, (x, YJ + 12, z), (x, YJ, z))

@etape('La moitié basse sur le disque côté LOGO', ['le servo (à 2048)', 'la moitié basse', '4 vis Ø 2,6 × 9 fournies avec le servo'],
       ['Pose le servo à plat, LOGO vers le haut.', 'Pose la moitié basse sur le disque du côté du logo, cuvette ronde vers toi, le bras partant du côté OPPOSÉ au grand bout du boîtier.',
        'Bras bien dans l\'alignement du boîtier (c\'est la position « horizontale »).', '4 vis Ø 2,6 × 9 au fond de la cuvette, un trou sur deux. Serre en croix, sans forcer.'],
       'À faire MAINTENANT : une fois le servo dans le berceau, ces vis sont contre le mur. Ne visse jamais une vis de 9 mm seule dans un disque, sans le plastique.',
       [(C['bas'], 'moitié basse'), (C['servo'], 'servo')])
def e3(fig):
    ax, = PM.panneaux(fig, 1)
    y0 = G.Y_D1 - G.SOUS_TETE
    PM.dessiner(ax, SERVO_COMPLET + [(G.BRAS_BAS, C['bas'])] + [(PM.vis(x, z, y0 - 18, 9, 1, d=2.6), NOIR) for x, z in QUATRE], vue=(20, -58), marge=0.72)
    for x, z in QUATRE: PM.guide(ax, (x, y0 - 18, z), (x, y0, z))
    PM.etiquette(ax, (60, G.Y_BAS0, 0), 'moitié basse', (60, -90)); PM.etiquette(ax, (-35, G.Y_S0, 0), 'face du LOGO', (-110, -70))
    PM.etiquette(ax, (G.ENT_B + 7, YJ, 0), 'entretoises\nvers le servo', (-10, 120))

@etape('Le berceau sur le mur du bâti', ['le nouveau bâti (epaule3095_bati)', 'le berceau', '4 vis M3 × 10'],
       ['Présente le berceau contre le mur, côté intérieur, socle plat contre le mur.', '4 vis M3 × 10 par-DERRIÈRE le mur, dans les 4 inserts du socle.', 'Serre en croix.'],
       'Si le bâti n\'est pas encore imprimé : saute cette étape, monte la suite sur la table, et reviens-y. Le berceau se visse aussi bien servo en place (les vis sont derrière le mur).',
       [(C['bati'], 'bâti'), (C['berceau'], 'berceau')])
def e4(fig):
    ax, = PM.panneaux(fig, 1)
    PM.dessiner(ax, [(G.BATI, C['bati']), (T(G.BERCEAU, (0, 30, 0)), C['berceau'])] + [(PM.vis(x, z, -G.EP_MUR - 16, 10, 1), NOIR) for x, z in G.TROUS_MUR], vue=(22, -52), marge=0.62)
    for x, z in G.TROUS_MUR: PM.guide(ax, (x, -G.EP_MUR - 16, z), (x, -G.EP_MUR, z))
    PM.etiquette(ax, (-30, -G.EP_MUR, 30), 'mur', (-110, 60)); PM.etiquette(ax, (-30, 60, 10), 'berceau', (120, 70))

@etape('Le servo descend dans le berceau', ['le servo avec sa moitié basse', 'le berceau'],
       ['Tiens le servo au-dessus du berceau, LOGO (et moitié basse) du côté du socle du berceau, grand bout vers l\'arrière.',
        'Descends-le bien droit : la moitié basse passe entre le socle et le servo.', 'Il doit se poser à plat au fond, sans forcer.',
        'Les deux prises SVG restent accessibles côté extérieur : une dessus, une dessous (par l\'échancrure du fond).'],
       'Tu l\'as déjà essayé : c\'est le sens validé sur tes photos du 26/11. Branche le câble du dessous AVANT si tu comptes t\'en servir.',
       [(C['servo'], 'servo'), (C['bas'], 'moitié basse')])
def e5(fig):
    ax, = PM.panneaux(fig, 1); h = (0, 0, 55)
    PM.dessiner(ax, [(G.BERCEAU, GRIS)] + [(T(m, h), c) for m, c in SERVO_COMPLET] + [(T(G.BRAS_BAS, h), C['bas'])], vue=(22, 52), marge=0.7)
    for x in (-40, 10): PM.guide(ax, (x, G.YC, 55 - G.S_W / 2), (x, G.YC, -G.S_W / 2))
    PM.etiquette(ax, (-50, 3, 10), 'socle du berceau\n(côté mur)', (-150, -30)); PM.etiquette(ax, (-20, G.Y_S1, 55), 'prises SVG\nde ce côté', (40, 120))

@etape('La bride', ['la bride', '2 vis M3 × 10'],
       ['Pose la bride sur les deux joues, par-dessus le servo.', '2 vis M3 × 10 dans les inserts du dessus des joues.', 'Serre : le servo ne doit plus bouger du tout.'],
       'Bride pas encore imprimée : passe à l\'étape 7, tu la poseras après (elle se met par le dessus, bras monté). Sans elle, le servo peut remonter : essais À LA MAIN seulement. Elle pince le servo de 0,3 mm, c\'est voulu.', [(C['bride'], 'bride')])
def e6(fig):
    ax, = PM.panneaux(fig, 1); z = G.S_W / 2 + G.EP_BRIDE
    PM.dessiner(ax, [(G.BERCEAU, GRIS), (G.SERVO, GRIS_SERVO), (G.DISQUES, GRIS), (G.BRAS_BAS, GRIS), (T(G.BRIDE, (0, 0, 22)), C['bride'])]
                + [(vis_z(G.X_VIS_BRIDE, y, z + 30, 10), NOIR) for y in G.Y_VIS_BRIDE], vue=(26, 48), marge=0.7)
    for y in G.Y_VIS_BRIDE: PM.guide(ax, (G.X_VIS_BRIDE, y, z + 30), (G.X_VIS_BRIDE, y, G.Z_APPUI))

@etape('La moitié haute ferme le bras', ['la moitié haute (avec la platine du coude)', '4 vis Ø 2,6 × 9', '4 vis M3 × 30', 'le tournevis fin'],
       ['Pose la moitié haute sur le disque côté extérieur, cuvette vers toi, dans l\'alignement de la moitié basse.', '4 vis Ø 2,6 × 9 dans la cuvette, un trou sur deux.',
        '4 vis M3 × 30 au fond des 4 puits : elles traversent les entretoises et se vissent dans les inserts de la moitié basse.',
        'Serre les 4 longues en croix, un peu chacune. Il reste 0,4 mm de jour entre les entretoises : c\'est normal.'],
       'Ne fais pas pivoter le bras tant que les vis des deux disques ne sont pas toutes serrées.', [(C['haut'], 'moitié haute')])
def e7(fig):
    ax, = PM.panneaux(fig, 1); d = (0, 26, 0); yh = G.Y_D2 + G.SOUS_TETE
    PM.dessiner(ax, [(G.BERCEAU, GRIS), (G.BRIDE, GRIS), (G.SERVO, GRIS_SERVO), (G.DISQUES, GRIS), (G.BRAS_BAS, GRIS), (T(G.BRAS_HAUT, d), C['haut'])]
                + [(PM.vis(x, z, yh + 62, 9, -1, d=2.6), NOIR) for x, z in QUATRE] + [(PM.vis(x, z, G.Y_FACE + 70, 30, -1), NOIR) for x, z in ENT], vue=(24, 50), marge=0.62)
    for x, z in QUATRE: PM.guide(ax, (x, yh + 62, z), (x, yh, z))
    for x, z in ENT: PM.guide(ax, (x, G.Y_FACE + 70, z), (x, YJ, z))
    PM.etiquette(ax, (G.X_PLAT0 + 15, G.Y_FACE + 26, 0), 'platine du coude', (120, -70)); PM.etiquette(ax, (G.ENT_A + 6, G.Y_FACE + 70, 9), '4 vis M3 × 30', (-40, 100))
    PM.etiquette(ax, (0, yh + 62, 12), '4 vis Ø 2,6 × 9', (-140, 60))

@etape('Contrôle à la main, puis le coude', ['rien : le servo reste DÉBRANCHÉ', 'ensuite : le berceau du coude et ses 4 vis M3 × 10'],
       ['Servo non alimenté, fais pivoter le bras doucement à la main, du plus bas au plus haut.', 'Il ne doit frotter nulle part. Les passages les plus justes sont en bas : 1,5 mm entre les disques et le fond du berceau, 2 mm entre la moitié basse et le berceau.',
        'Remets le bras à l\'horizontale.', 'Seulement ensuite : le berceau du coude sur la platine (4 vis M3 × 10), comme sur l\'ancien bras. Il recouvre deux têtes de vis, d\'où l\'ordre.'],
       'Aucun mouvement au moteur avant : le bloc 12 V de 10 A, les butées et la limite de force réglées avec moi. Ce servo est trois fois plus fort que les autres.',
       [(C['haut'], 'moitié haute'), (C['bas'], 'moitié basse')])
def e8(fig):
    a1, a2 = PM.panneaux(fig, 2, ['Bras en bas (−30°)', 'Bras en haut (+90°)'])
    for ax, alpha in ((a1, -30), (a2, 90)):
        PM.dessiner(ax, [(G.BERCEAU, C['berceau']), (G.BRIDE, C['bride']), (G.SERVO, C['servo']), (E.tourner_y(G.DISQUES, alpha), C['disque']),
                         (E.tourner_y(G.BRAS_BAS, alpha), C['bas']), (E.tourner_y(G.BRAS_HAUT, alpha), C['haut'])], vue=(18, 60), marge=0.72)

def page_pieces(pdf):
    fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
    fig.suptitle('Épaule STS3095 : les pièces (PROTOTYPE, jamais montée). Chaque pièce garde SA couleur dans tout le plan', fontsize=19, weight='bold', y=0.985)
    for k, (nom, m, c, q, vue) in enumerate([('Berceau', G.BERCEAU, C['berceau'], '× 1', (26, 48)), ('Moitié basse du bras', G.BRAS_BAS, C['bas'], '× 1', (28, -60)),
                                             ('Moitié haute (platine du coude)', G.BRAS_HAUT, C['haut'], '× 1', (28, 55)), ('Bride', G.BRIDE, C['bride'], '× 1', (30, 48)),
                                             ('Bâti', G.BATI, C['bati'], '× 1', (22, -52)), ('Servo STS3095', G.SERVO + G.DISQUES, C['servo'], '× 1', (24, 48))]):
        ax = fig.add_subplot(2, 3, k + 1, projection='3d'); PM.dessiner(ax, [(m, c)], vue=vue, marge=0.72); ax.set_title(f'{nom}  {q}', fontsize=14, weight='bold', color=c)
    fig.text(0.03, 0.03, 'Visserie : 10 inserts M3 · 6 vis M3 × 10 (4 berceau sur le mur, 2 bride) · 4 vis M3 × 30 (entretoises) · 8 vis Ø 2,6 × 9 fournies avec le servo (4 par disque).\n'
             'Dans les étapes : EN COULEUR = ce que tu poses maintenant · GRIS = déjà monté · pointillés rouges = où va la vis.', fontsize=13)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.1, hspace=0.15, wspace=0.02)
    fig.savefig(G.OUT / 'plan_montage_3095_00.png', dpi=90); pdf.savefig(fig); plt.close(fig)

if __name__ == '__main__':
    with PdfPages(G.OUT / 'plan_montage_epaule_3095.pdf') as pdf:
        page_pieces(pdf)
        for n, (titre, il_faut, faire, attention, leg, f) in enumerate(ETAPES, 1):
            fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white'); f(fig)
            PM.mise_en_page(fig, n, len(ETAPES), titre, il_faut, faire, attention, leg)
            fig.savefig(G.OUT / f'plan_montage_3095_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)
    print('ok', len(ETAPES), 'étapes')
