"""Plan de montage illustré du socle tournant : une page par étape (PDF + PNG), même présentation que l'épaule.
Lancer après generer_socle.py."""
import sys, os, math, textwrap
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import generer_socle as S
import plan_montage_epaule_outils as PM
E = PM.E
C = {'base': '#c9a35a', 'palier': '#5b8bd6', 'entretoise': '#9b6fd0', 'roulement': '#8f9ba6', 'plateau': '#e0602a', 'servo': '#3a3a3a', 'bati': '#7fb069'}
GRIS, GRIS_SERVO, LAITON, NOIR = PM.GRIS, PM.GRIS_SERVO, PM.LAITON, PM.NOIR
T = lambda m, dz: m.translate((0, 0, dz))
def insert(x, y, z): return S.cyl(x, y, z, z + 5.7, 4.8, 20) - S.cyl(x, y, z - .1, z + 5.8, 2.6, 12)
def vis(x, y, z_bas, L, d=3.0): return S.cyl(x, y, z_bas, z_bas + L, d, 12) + S.cyl(x, y, z_bas + L, z_bas + L + d, d * 1.8, 20)
R1 = S.anneau(S.Z_RA, S.Z_RA + S.ROUL_EP, 47, 35); R2 = S.anneau(S.Z_RB, S.Z_RB + S.ROUL_EP, 47, 35)
AX, AY = S.AXE_DANS_PIED; TROUS_PL = [(x - AX, y - AY) for x, y in S.TROUS_PIED]
ZT = S.Z_HAUT - S.SERRAGE; ZP = S.Z_PLATEAU + S.EP_PLATEAU
VIS_PAL = [(S.CERCLE_TROUS / 2 * math.cos(math.radians(45 + 90 * k)), S.CERCLE_TROUS / 2 * math.sin(math.radians(45 + 90 * k))) for k in range(4)]
ETAPES = []
def etape(titre, il_faut, faire, attention=None, leg=()):
    def deco(f): ETAPES.append((titre, il_faut, faire, attention, leg, f)); return f
    return deco

@etape('Le servo du socle, tout seul', ['un servo neuf (il porte le n° 1)', 'la carte + 12 V', 'le logiciel FD'],
       ['Branche CE servo seul sur la carte (le bras débranché : le coude porte encore le n° 1).', 'Il garde le n° 1.',
        'Programming : ligne 9 · Min Position Limit = 1024, ligne 11 · Max Position Limit = 3072, Save à chaque fois.',
        'Debug : vitesse 300, position 2048. Le palonnier est au milieu : n\'y touche plus.', 'Coupe le 12 V, débranche.'],
       'Butées 1024–3072 = un quart de tour de chaque côté.', [(C['servo'], 'servo n° 1')])
def e1(fig):
    ax, = PM.panneaux(fig, 1); PM.dessiner(ax, [(S.SERVO, C['servo'])], vue=(25, -60), marge=0.85)
    PM.etiquette(ax, (0, 0, S.Z_PAL), 'palonnier à 2048', (110, 50))

@etape('Les 8 inserts', ['la base', 'le plateau', '8 inserts M3, fer à 230 °C'],
       ['Base : 4 inserts en haut des 4 poteaux.', 'Plateau : 4 inserts dans les 4 trous des coins, par la face PLATE (celle sans moyeu), au ras.',
        'Insert bien droit.'], 'Sur le plateau, les inserts reçoivent les vis du pied du bâti.', [(C['base'], 'base'), (C['plateau'], 'plateau')])
def e2(fig):
    a1, a2 = PM.panneaux(fig, 2, ['A. Base : 4 en haut des poteaux', 'B. Plateau : 4 par la face plate'])
    PM.dessiner(a1, [(S.BASE, C['base'])] + [(insert(x, y, ZT + 10), LAITON) for x, y in S.POTEAUX], vue=(28, -60), marge=0.7)
    for x, y in S.POTEAUX: PM.guide(a1, (x, y, ZT + 10), (x, y, ZT))
    PM.dessiner(a2, [(S.PLATEAU, C['plateau'])] + [(insert(x, y, ZP + 10), LAITON) for x, y in TROUS_PL], vue=(32, -60), marge=0.7)
    for x, y in TROUS_PL: PM.guide(a2, (x, y, ZP + 10), (x, y, ZP))
    PM.etiquette(a2, (0, 0, S.Z_PAL + 12), 'moyeu (dessous)', (110, -40))

@etape('Le servo dans la base', ['la base', 'le servo n° 1'],
       ['Le servo se pose DEBOUT dans son logement, palonnier en haut.', 'Le palonnier va du côté où le mur de la base est plus bas (il déborde un peu du servo).',
        'Le câble sort par la fenêtre carrée, sur le côté.', 'Le servo doit être bien à plat au fond.'], 'Ne tourne pas le palonnier : il doit rester à 2048.', [(C['base'], 'base'), (C['servo'], 'servo')])
def e3(fig):
    ax, = PM.panneaux(fig, 1); PM.dessiner(ax, [(S.BASE, C['base']), (T(S.SERVO, 35), C['servo'])], vue=(28, -60), marge=0.75)
    PM.etiquette(ax, (0, 0, S.Z_PAL + 35), 'palonnier en haut', (110, 40)); PM.etiquette(ax, (S.X0S + 23, -S.SW / 2 - 4, 12), 'fenêtre du câble', (-60, -80))
    PM.etiquette(ax, (S.POTEAUX[2][0], S.POTEAUX[2][1], ZT), 'poteau', (90, 10))

@etape('Les 2 roulements dans le palier', ['le palier', '2 roulements 6807', 'l\'entretoise'],
       ['Dans le tube du palier, dans cet ordre : un roulement poussé jusqu\'au fond, l\'entretoise, le 2e roulement.',
        'Ils entrent en appuyant à la main, bien à plat.', 'Le 2e roulement arrive au ras du haut du tube.'],
       'Trop serré : un peu de papier de verre dans le tube. Trop lâche : dis-le-moi avant d\'aller plus loin.',
       [(C['palier'], 'palier'), (C['roulement'], 'roulement'), (C['entretoise'], 'entretoise')])
def e4(fig):
    ax, = PM.panneaux(fig, 1)
    PM.dessiner(ax, [(S.PALIER, C['palier']), (T(R1, 38), C['roulement']), (T(S.ENTRETOISE, 52), C['entretoise']), (T(R2, 62), C['roulement'])], vue=(25, -60), marge=0.75)
    PM.guide(ax, (0, 0, S.Z_TUBE), (0, 0, S.Z_RB + 62))
    PM.etiquette(ax, (23, 0, S.Z_RA + 41), '1. roulement', (110, -10)); PM.etiquette(ax, (23, 0, S.Z_RA + 62), '2. entretoise', (110, 10)); PM.etiquette(ax, (23, 0, S.Z_RB + 65), '3. roulement', (110, 30))

@etape('Le palier sur la base', ['la base avec son servo', 'le palier garni', '4 vis M3 × 10'],
       ['Pose le palier sur les 4 poteaux : son tube vient au-dessus du palonnier.', '4 vis M3 × 10 dans les inserts des poteaux, serrées en croix.',
        'Le palier appuie sur le dessus du servo : c\'est lui qui le tient (0,5 mm de serrage).'], 'Normal qu\'il reste un petit jour sur les poteaux avant de serrer.', [(C['palier'], 'palier')])
def e5(fig):
    ax, = PM.panneaux(fig, 1); dz = 30
    pcs = [(S.BASE, GRIS), (S.SERVO, GRIS_SERVO), (T(S.PALIER, dz), C['palier']), (T(S.ROULEMENTS, dz), C['roulement'])] + [(vis(x, y, S.Z_HAUT + 4 + dz + 8, 10), NOIR) for x, y in S.POTEAUX]
    PM.dessiner(ax, pcs, vue=(28, -60), marge=0.72)
    for x, y in S.POTEAUX: PM.guide(ax, (x, y, S.Z_HAUT + dz + 12), (x, y, ZT))
    PM.etiquette(ax, (S.POTEAUX[2][0], S.POTEAUX[2][1], S.Z_HAUT + dz + 25), '4 vis M3 × 10', (90, 40))

@etape('Le plateau', ['le plateau (avec ses inserts)', '4 vis M2,5 (fournies avec le servo)', 'un tournevis long, un foret de 2,5 à 3 mm'],
       ['Si le fond du moyeu est fermé par une fine peau : perce les 4 petits trous au foret, à la main, par le bout du moyeu.',
        'Descends le moyeu dans les 2 roulements, jusqu\'à ce qu\'il se pose sur le palonnier.',
        'Oriente le plateau : côtés parallèles à ceux de la base (dessin B). Le bras pointera du côté où le moyeu est le plus près du bord.',
        '4 vis M2,5 dans le palonnier, tournevis passé par le creux du moyeu. Serre à tour de rôle, sans forcer.'],
       'Le moyeu doit entrer à la main, sans jeu. S\'il force, ponce-le légèrement.', [(C['plateau'], 'plateau')])
def e6(fig):
    a1, a2 = PM.panneaux(fig, 2, ['A. Le moyeu descend dans les roulements, 4 vis M2,5 par le creux', 'B. Vu de dessus : plateau aligné sur la base'])
    dz = 45; demi = S.box(-200, -200, -10, 200, 0, 300)
    pcs = [(S.BASE - demi, GRIS), (S.SERVO, GRIS_SERVO), (S.PALIER - demi, GRIS), (S.ROULEMENTS - demi, C['roulement']), (S.ENTRETOISE - demi, GRIS), (T(S.PLATEAU - demi, dz), C['plateau'])]
    pcs += [(vis(x, y, ZP + dz + 12, 6, 2.5), NOIR) for x, y in VIS_PAL]
    PM.dessiner(a1, pcs, vue=(14, -80), marge=0.62, cadre=(-100, 60, -10, 70, 0, 150))
    PM.guide(a1, (0, 0, ZP + dz + 12), (0, 0, S.Z_PAL + dz + 4)); PM.etiquette(a1, (0, 0, ZP + dz + 22), '4 vis M2,5', (130, -30)); PM.etiquette(a1, (0, 0, S.Z_PAL + 2), 'palonnier', (-120, -30))
    PM.etiquette(a1, (0, 0, S.Z_PAL + dz + 15), 'moyeu', (-110, 30))
    PM.dessiner(a2, [(S.BASE, GRIS), (S.PALIER, GRIS), (S.PLATEAU, C['plateau'])], vue=(90, -90), marge=0.62, cadre=(-100, 60, -70, 70, 0, 80)); a2.set_proj_type('ortho')
    PM.etiquette(a2, (34 - AX, 0, ZP), 'le bras pointera\nde ce côté →', (60, 60), C['plateau'])

@etape('Essai à la main, base serrée, bâti vissé', ['le socle monté', 'un serre-joint', 'le bâti avec le bras', '4 vis M3 × 12'],
       ['Servo non alimenté : tourne le plateau à la main d\'un quart de tour de chaque côté. Pas de point dur, et il ne doit pas pencher.',
        'Serre la BASE sur la table (serre-joint sur son bord, ou 4 vis à bois).', 'Pose le pied du bâti sur le plateau : mêmes contours, 4 trous en face.',
        '4 vis M3 × 12 par le dessus du pied, dans les inserts du plateau.', 'Câbles du bras : par l\'extérieur, avec une grande boucle souple.'],
       'L\'axe de l\'épaule est maintenant à 179 mm de la table : les objets se posent sur le plan de travail surélevé de 78 mm.', [(C['bati'], 'bâti'), (C['base'], 'base à serrer')])
def e7(fig):
    ax, = PM.panneaux(fig, 1); dzb = ZP + E.H_AXE + E.EP_PIED; place = lambda m, d=0: m.translate((-AX, -AY, dzb + d))
    pcs = [(S.BASE, C['base']), (S.PALIER, GRIS), (S.PLATEAU, GRIS), (place(E.BATI, 25), C['bati'])] + [(vis(x, y, ZP + 25 + 6 + 8, 12), NOIR) for x, y in TROUS_PL]
    PM.dessiner(ax, pcs, vue=(20, -55), marge=0.6, cadre=(-100, 60, -70, 70, 0, 260))
    for x, y in TROUS_PL: PM.guide(ax, (x, y, ZP + 25), (x, y, ZP))
    PM.etiquette(ax, (TROUS_PL[2][0], TROUS_PL[2][1], ZP + 55), '4 vis M3 × 12', (110, 20)); PM.etiquette(ax, (45, -50, 3), 'serre-joint ici', (90, -30), '#8a6a20')

@etape('Les numéros, puis le branchement', ['le bras monté sur le socle', 'FD'],
       ['Bras branché SANS le servo du socle : dans FD, Search montre 1, 2, 4.', 'Clique sur le n° 1 (le coude) : Programming, ligne 5 · ID = 3, Save. Search : 2, 3, 4.',
        'Coupe le 12 V. Branche le servo du socle (n° 1) à la suite de la chaîne. Rallume : Search montre 1, 2, 3, 4.', 'Ferme FD. Premier essai : bras\\tester_socle.bat (c, g, d, puis G, D), le bras replié à la verticale. Ensuite piloter_bras.bat : t45, t0.'],
       'Ne branche jamais le servo du socle tant que le coude porte encore le n° 1 : ils répondraient en même temps.', [])
def e8(fig):
    ax, = PM.panneaux(fig, 1); dzb = ZP + E.H_AXE + E.EP_PIED; place = lambda m: m.translate((-AX, -AY, dzb))
    p = E.bras_complet(30.0, -30.0, avec_pince=True)
    pcs = [(S.BASE, C['base']), (S.PALIER, C['palier']), (S.PLATEAU, C['plateau']), (place(E.BATI), C['bati']), (place(E.BERCEAU_E + E.BRIDE_E), GRIS), (place(E.SERVO_E), GRIS_SERVO)]
    pcs += [(place(m), GRIS) for m in p.values()]
    PM.dessiner(ax, pcs, vue=(18, -55), marge=0.55, cadre=(-100, 300, -100, 100, 0, 320))
    PM.etiquette(ax, (0, 0, 20), 'socle : n° 1', (-110, -20)); PM.etiquette(ax, (-AX, -AY + 30, dzb), 'épaule : n° 2', (-130, 30)); PM.etiquette(ax, (104 - AX, 40, dzb + 60), 'coude : n° 3', (30, 90)); PM.etiquette(ax, (300 - AX, 60, dzb + 60), 'pince : n° 4', (40, 70))

def page_pieces(pdf):
    fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
    fig.suptitle('Socle tournant : les pièces. Chaque pièce garde SA couleur dans tout le plan', fontsize=20, weight='bold', y=0.985)
    for k, (nom, m, c, q, vue) in enumerate([('Base', S.BASE, C['base'], '× 1', (28, -60)), ('Palier', S.PALIER, C['palier'], '× 1', (28, -60)), ('Plateau (moyeu dessous)', S.PLATEAU, C['plateau'], '× 1', (-25, -60)),
                                             ('Entretoise', S.ENTRETOISE, C['entretoise'], '× 1', (30, -60)), ('Roulement 6807', R1, C['roulement'], '× 2', (30, -60)), ('Servo n° 1', S.SERVO, C['servo'], '× 1', (25, -60))]):
        ax = fig.add_subplot(2, 3, k + 1, projection='3d'); PM.dessiner(ax, [(m, c)], vue=vue, marge=0.72); ax.set_title(f'{nom}  {q}', fontsize=14, weight='bold', color=c)
    fig.text(0.03, 0.03, 'Visserie : 8 inserts M3 · 4 vis M3 × 10 (palier) · 4 vis M3 × 12 (pied du bâti) · 4 vis M2,5 du palonnier · un serre-joint.\n'
             'Dans les étapes : EN COULEUR = ce que tu poses maintenant · GRIS = déjà monté · pointillés rouges = où va la vis.', fontsize=13)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.1, hspace=0.15, wspace=0.02)
    fig.savefig(S.OUT / 'plan_montage_00.png', dpi=90); pdf.savefig(fig); plt.close(fig)

if __name__ == '__main__':
    with PdfPages(S.OUT / 'plan_montage_socle.pdf') as pdf:
        page_pieces(pdf)
        for n, (titre, il_faut, faire, attention, leg, f) in enumerate(ETAPES, 1):
            fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white'); f(fig)
            PM.mise_en_page(fig, n, len(ETAPES), titre, il_faut, faire, attention, leg)
            fig.savefig(S.OUT / f'plan_montage_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)
    print('ok', len(ETAPES), 'étapes')
