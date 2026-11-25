"""Plan de montage illustré du banc d'essai du doigt motorisé : une page par étape, PDF + PNG → sortie/plan_montage_doigt.pdf"""
import sys, os
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import generer_banc_doigt as B, generer_doigt as D, plan_montage_epaule_outils as PM

C = {'banc': '#7fb069', 'console': '#2f9fae', 'etrier': '#9b6fd0', 'servo': '#3a3a3a', 'pal': '#f2f2f2', 'poulie': '#e0602a',
     'doigt': '#c9a35a', 'insert': '#d4a72c', 'fil': '#d0302a', 'rondelle': '#5b8bd6'}
GRIS, GS, NOIR = PM.GRIS, PM.GRIS_SERVO, PM.NOIR
T = lambda m, d: m.translate(d)
def vis_z(x, y, z, L, d=3.0): return D.cyl_z(x, y, z - L, z, d, 12) + D.cyl_z(x, y, z, z + d, d * 1.8, 20)          # tête en haut, en z
def vis_y(x, y, z, L, d=3.0): return D.cyl_y(x, z, y - L, y, d, 12) + D.cyl_y(x, z, y, y + d, d * 1.8, 20)         # tête vers +y
def insert_z(x, y, z): return D.cyl_z(x, y, z - 3.8, z, 4.7, 20)
DOIGT = lambda angles=(0, 0, 0): [(p, c) for p, c in zip(B.doigt_a(list(angles)), [C['doigt'], '#5b8bd6', '#3aa6a6', '#d6a62e'])]
DOIGT_GRIS = lambda angles=(0, 0, 0): [(p, GRIS) for p in B.doigt_a(list(angles))]
VUE = (24, 62)
XE, ZV = sum(B.X_ETRIER) / 2, B.Z_VIS
Y_ARR = B.Y_CLOISON - B.EP_CLOISON
ETAPES = []
def etape(titre, il_faut, faire, attention=None, leg=()):
    def deco(f): ETAPES.append((titre, il_faut, faire, attention, leg, f)); return f
    return deco

@etape('Préparer le petit servo, SANS rien dessus', ['un servo SCS0009, son câble', 'la DEUXIÈME carte Waveshare, alimentée (voir l\'encadré)', 'tester_doigt.bat (dossier main)'],
       ['Coupe l\'alimentation. Branche le servo SEUL sur la deuxième carte, puis la carte en USB.', 'Remets l\'alimentation et lance tester_doigt.bat.',
        'Tape  n 22  : il prend le numéro 22 (l\'index). Colle une étiquette « 22 » sur le servo.', 'Tape  v  : il fait ± 20° et revient. Rien n\'est monté dessus, aucun risque.',
        'Tape  m  : il se met au milieu de sa course. Tape  q , coupe l\'alimentation.'],
       'JAMAIS sur la carte du bras (12 V) : ces servos ne supportent que 4 à 7,4 V. Le programme refuse une carte à plus de 8 V, mais un seul branchement suffit à griller le servo.',
       [(C['servo'], 'servo SCS0009')])
def e1(fig):
    ax, = PM.panneaux(fig, 1); PM.dessiner(ax, [(B.SERVO, C['servo'])], vue=(28, 40), marge=0.8)
    PM.etiquette(ax, (B.XP, B.y_de_h(B.H_AXE), B.H), 'axe doré', (80, 60)); PM.etiquette(ax, (B.XP - 20, B.y_de_h(B.H_PATTE0), B.H), 'pattes', (-120, 40))

@etape('Six inserts', ['la platine, la console, l\'étrier', '6 inserts M3 (Ø 4,7 × 3,8)', 'le fer à souder'],
       ['Platine : 2 inserts dans le dessus du petit montant (sous la console).', 'Console : 2 inserts dans les 2 trous près de son bout, ceux où se visse le doigt. Les 2 autres trous restent lisses.',
        'Étrier : 1 insert au bout de chaque jambe.', 'Chaque insert bien droit, à fleur. Laisse refroidir sans toucher.'],
       'Les 2 trous lisses de la console (côté montant) ne prennent PAS d\'insert : les vis y passent librement.', [(C['insert'], 'insert M3')])
def e2(fig):
    a1, a2 = PM.panneaux(fig, 2, ['Platine et console', 'Étrier (jambes en l\'air)'])
    zc = B.H_MARCHE - B.EP_CONSOLE
    pcs = [(B.BANC, C['banc']), (T(B.CONSOLE, (0, 0, 25)), C['console'])]
    pcs += [(insert_z(x, y, zc + 8), C['insert']) for x, y in B.VIS_CONSOLE] + [(insert_z(x, y, B.H_MARCHE + 25 + 8), C['insert']) for x, y in B.PATTES_DOIGT]
    PM.dessiner(a1, pcs, vue=(30, 40), marge=0.7)
    for x, y in B.VIS_CONSOLE: PM.guide(a1, (x, y, zc + 8), (x, y, zc))
    for x, y in B.PATTES_DOIGT: PM.guide(a1, (x, y, B.H_MARCHE + 33), (x, y, B.H_MARCHE + 25))
    PM.etiquette(a1, (B.VIS_CONSOLE[0][0], B.VIS_CONSOLE[0][1], zc), 'montant : 2 inserts', (-160, -40), taille=11)
    PM.etiquette(a1, (B.PATTES_DOIGT[0][0], B.PATTES_DOIGT[0][1], B.H_MARCHE + 25), 'console : 2 inserts', (60, 60), taille=11)
    et = B.ETRIER.transform([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, -(B.Y_FOND - 3.0)]])
    bb = et.bounding_box(); zt = bb[5]
    PM.dessiner(a2, [(et, C['etrier'])] + [(D.cyl_z(XE, -z, zt + 6, zt + 9.8, 4.7, 20), C['insert']) for z in ZV], vue=(30, 40), marge=0.8)
    for z in ZV: PM.guide(a2, (XE, -z, zt + 6), (XE, -z, zt))

@etape('La console sur le montant, le doigt sur la console', ['la console', 'le doigt d\'essai monté (base + 3 phalanges)', '4 vis M3 × 10', 'les 2 rondelles imprimées'],
       ['Pose la console sur le montant, ses 2 trous lisses au-dessus des 2 inserts. Visse les 2 vis M3 × 10.', 'Pose la base du doigt sur la console, ses 2 pattes sur les 2 inserts, le doigt vers l\'EXTÉRIEUR.',
        'Mets une rondelle sous la tête de chaque vis, puis visse les 2 vis M3 × 10.', 'Plie le doigt à la main : il doit plier vers le BAS, librement.'],
       'Les rondelles ne sont pas un détail : sans elles, la pointe des vis dépasse sous la console, et le doigt plié à fond vient y frotter.', [(C['console'], 'console'), (C['doigt'], 'doigt'), (C['rondelle'], 'rondelles')])
def e3(fig):
    ax, = PM.panneaux(fig, 1); dz = 30
    pcs = [(B.BANC, GRIS), (B.CONSOLE, C['console'])] + [(T(p, (0, 0, dz)), c) for p, c in DOIGT()]
    zt = B.H_MARCHE + 4 + B.RONDELLE + dz + 12
    pcs += [(vis_z(x, y, zt, 10), NOIR) for x, y in B.PATTES_DOIGT] + [(T(D.cyl_z(x, y, 0, B.RONDELLE, 8.0) - D.cyl_z(x, y, -1, 3, 3.4), (0, 0, zt - 6)), C['rondelle']) for x, y in B.PATTES_DOIGT]
    pcs += [(vis_z(x, y, B.H_MARCHE, 10), NOIR) for x, y in B.VIS_CONSOLE]
    PM.dessiner(ax, pcs, vue=(26, 50), marge=0.62)
    for x, y in B.PATTES_DOIGT: PM.guide(ax, (x, y, zt - 10), (x, y, B.H_MARCHE))
    PM.etiquette(ax, (B.VIS_CONSOLE[0][0], B.VIS_CONSOLE[0][1], B.H_MARCHE + 3), '2 vis M3 × 10 (console)', (-150, 30), taille=11)
    PM.etiquette(ax, (B.PATTES_DOIGT[0][0], B.PATTES_DOIGT[0][1], zt + 4), '2 vis M3 × 10 + rondelles', (40, 60), taille=11)

@etape('Le servo dans la cloison, l\'étrier derrière', ['le servo n° 22', 'l\'étrier', '2 vis M3 × 10'],
       ['Présente le servo DEVANT la cloison (côté doigt), axe doré vers TOI, le câble en arrière.', 'L\'axe doré est du côté du doigt ; le bout d\'où sort le câble est à l\'opposé.',
        'Enfonce-le dans la fenêtre jusqu\'à ce que ses 2 pattes touchent la cloison. Le câble passe derrière.', 'Derrière, pose l\'étrier : sa traverse appuie sur le dessous du servo, ses jambes au-dessus et au-dessous.',
        'Par l\'avant de la cloison, visse les 2 vis M3 × 10 dans les inserts de l\'étrier.'],
       'Le servo doit être serré, sans jeu : c\'est lui qui retient la tension des fils.', [(C['servo'], 'servo n° 22'), (C['etrier'], 'étrier')])
def e4(fig):
    a1, a2 = PM.panneaux(fig, 2, ['A. Le servo entre par l\'avant', 'B. L\'étrier, vu de derrière'])
    PM.dessiner(a1, [(B.BANC, GRIS), (B.CONSOLE, GRIS)] + DOIGT_GRIS() + [(T(B.SERVO, (0, 30, 0)), C['servo'])], vue=VUE, marge=0.62)
    PM.guide(a1, (B.XP - 5, 30 + B.y_de_h(10), B.H), (B.XP - 5, B.y_de_h(10), B.H))
    pcs = [(B.BANC, GRIS), (B.SERVO, GS), (T(B.ETRIER, (0, -22, 0)), C['etrier'])] + [(vis_y(XE, B.Y_CLOISON + 3, z, 10), NOIR) for z in ZV]
    PM.dessiner(a2, pcs, vue=(24, -125), marge=0.7)
    for z in ZV: PM.guide(a2, (XE, Y_ARR - 22, z), (XE, Y_ARR, z))
    PM.etiquette(a2, (XE, Y_ARR - 22, ZV[1]), 'étrier', (-60, 60), taille=11)

@etape('Le palonnier rond, puis la poulie', ['le palonnier ROND du sachet et sa vis centrale', 'la poulie', '1 petite vis du sachet (Ø 1,3 × 6,1)'],
       ['Le servo est resté au milieu (étape 1). Enfonce le palonnier rond sur l\'axe doré, face plate vers toi.', 'Visse sa vis centrale, sans forcer : c\'est elle qui le tient sur l\'axe.',
        'Pose la poulie par-dessus : le disque du palonnier entre dans le creux de dessous.', 'Tourne la poulie pour qu\'un de ses 2 petits trous tombe sur un des 2 trous les PLUS ÉCARTÉS du palonnier.',
        'Visse la petite vis dans ce trou, à la main, jusqu\'au contact.'],
       'Si la petite vis n\'entre pas dans le trou du palonnier (0,7 mm), agrandis-le d\'abord avec une aiguille chauffée. Ne force pas, le palonnier se fendrait.',
       [(C['pal'], 'palonnier rond'), (C['poulie'], 'poulie')])
def e5(fig):
    ax, = PM.panneaux(fig, 1)
    pcs = [(B.BANC, GRIS), (B.CONSOLE, GRIS), (B.ETRIER, GRIS)] + DOIGT_GRIS() + [(B.SERVO, GS), (T(B.PAL, (0, 14, 0)), C['pal']), (T(B.poulie_a(0), (0, 30, 0)), C['poulie'])]
    PM.dessiner(ax, pcs, vue=VUE, marge=0.62)
    PM.guide(ax, (B.XP, 30 + B.y_de_h(B.H_P0), B.H), (B.XP, B.y_de_h(B.H_AXE), B.H))
    PM.etiquette(ax, (B.XP, 14 + B.y_de_h(B.H_AXE), B.H), 'palonnier rond', (-120, 60), taille=11)
    PM.etiquette(ax, (B.XP, 30 + B.y_de_h(B.H_P2), B.H + 5), 'poulie', (40, 70), taille=11)

@etape('Les deux fils', ['le fil de pêche du doigt (un brin, noué au bout)', 'une pince à épiler', 'colle cyano'],
       ['Plie le doigt à MOITIÉ (environ 45° à chaque charnière) et tiens-le ainsi.', 'Fil du DESSOUS (il ferme) : il passe SOUS la poulie, dans la gorge côté servo, fait un tour complet, entre dans le petit trou du fond de sa gorge et ressort sur le dessus. Tends-le, fais 3 nœuds.',
        'Fil du DESSUS (il ouvre) : il passe PAR-DESSUS la poulie, dans la gorge côté toi, fait un tour complet dans l\'AUTRE sens, entre dans son petit trou. Tends-le, fais 3 nœuds.',
        'Les deux fils doivent être tendus comme une corde de guitare molle : sans mou, sans tirer le doigt.', 'Une goutte de colle cyano sur chaque nœud, coupe le surplus à 3 mm.'],
       'Les deux tours sont en sens INVERSE : quand la poulie tourne, l\'un s\'enroule, l\'autre se déroule. Si les deux s\'enroulent ensemble, le doigt se bloque : refais le fil du dessus dans l\'autre sens.',
       [(C['fil'], 'les fils'), (C['poulie'], 'poulie')])
def e6(fig):
    a1, a2 = PM.panneaux(fig, 2, ['Les deux fils, doigt à moitié plié', 'De près : sous et par-dessus la poulie'])
    pcs = [(B.BANC, GRIS), (B.CONSOLE, GRIS), (B.ETRIER, GRIS), (B.SERVO, GS), (B.poulie_a(0), C['poulie'])] + DOIGT((45, 45, 45))
    fils = [(B.tige(a, b, 0.9), C['fil']) for a, b in B.fils()]
    PM.dessiner(a1, pcs + fils, vue=VUE, marge=0.62)
    (a0, b0), (a1_, b1) = B.fils()
    PM.etiquette(a1, tuple((a0 + b0) / 2), 'dessous : FERME', (40, -70), taille=11); PM.etiquette(a1, tuple((a1_ + b1) / 2), 'dessus : OUVRE', (60, 60), taille=11)
    PM.dessiner(a2, [(B.SERVO, GS), (B.poulie_a(0), C['poulie'])] + fils, vue=(8, 92), cadre=(B.XP - 20, B.XP + 40, -30, 15, B.H - 20, B.H + 20), marge=0.95)

@etape('Brancher et faire apprendre la course', ['un serre-joint', 'la carte de la main alimentée', 'tester_doigt.bat'],
       ['Pose le banc au BORD de la table : la console et le doigt dans le vide. Serre la platine avec le serre-joint.', 'Alimentation allumée, lance tester_doigt.bat.',
        'Tape  c  : le servo tourne doucement d\'un côté jusqu\'à sentir la butée du doigt, puis de l\'autre.', 'Il te demande si le doigt est plié ou tendu : réponds  p  ou  t .',
        'Essaie :  t  (tendu),  p  (plié),  a 50  (à moitié),  +  et  - .', 'Dis-moi la course trouvée (le calcul en prévoit 221°) et si le doigt se ferme jusqu\'au bout.'],
       'Si le doigt se coince, le servo s\'arrête de lui-même et tient sa place. Tape  r  pour le relâcher : un doigt ne porte rien, il ne tombe pas.', [(C['doigt'], 'doigt'), (C['poulie'], 'poulie')])
def e7(fig):
    a1, a2 = PM.panneaux(fig, 2, ['Tendu (0 %)', 'Plié (100 %)'])
    base = [(B.BANC, C['banc']), (B.CONSOLE, C['console']), (B.ETRIER, C['etrier']), (B.SERVO, C['servo'])]
    PM.dessiner(a1, base + [(B.poulie_a(0), C['poulie'])] + DOIGT() + [(B.tige(a, b, 0.9), C['fil']) for a, b in B.fils()], vue=VUE, marge=0.62)
    PM.dessiner(a2, base + [(B.poulie_a(220), C['poulie'])] + DOIGT((80, 80, 80)), vue=VUE, marge=0.62)

def page_pieces(pdf):
    fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
    fig.suptitle('Doigt motorisé, banc d\'essai : les pièces', fontsize=20, weight='bold', y=0.985)
    for k, (nom, m, c, vue) in enumerate([('Platine (à imprimer)', B.BANC, C['banc'], (28, 40)), ('Console (à imprimer)', B.CONSOLE, C['console'], (35, 40)),
                                          ('Étrier (à imprimer)', B.ETRIER, C['etrier'], (24, -125)), ('Poulie (à imprimer)', B.POULIE, C['poulie'], (35, 40))]):
        ax = fig.add_subplot(2, 2, k + 1, projection='3d'); PM.dessiner(ax, [(m, c)], vue=vue, marge=0.72); ax.set_title(nom, fontsize=14, weight='bold', color=c)
    fig.text(0.03, 0.03, 'À imprimer aussi : 2 rondelles (banc_doigt_rondelles.stl). Le doigt d\'essai (base + 3 phalanges) est celui que tu as déjà.\n'
             'Visserie : 6 vis M3 × 10, 6 inserts M3, 1 petite vis du sachet du servo. PETG, 4 périmètres, 40 %, sans supports.\n'
             'ALIMENTATION de la carte de la main : 6 V (l\'UBEC, cavalier enlevé) ou, pour ce premier essai, le petit boîtier 5 V. Mesure au multimètre AVANT de brancher le servo.\n'
             'PROTOTYPE : vérifié par le calcul, jamais monté. Dans les étapes : EN COULEUR = ce que tu poses · GRIS = déjà monté · pointillés rouges = le trajet.', fontsize=12.5)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.13, hspace=0.15, wspace=0.02)
    fig.savefig(B.OUT / 'plan_montage_doigt_00.png', dpi=90); pdf.savefig(fig); plt.close(fig)

if __name__ == '__main__':
    with PdfPages(B.OUT / 'plan_montage_doigt.pdf') as pdf:
        page_pieces(pdf)
        for n, (titre, il_faut, faire, attention, leg, f) in enumerate(ETAPES, 1):
            fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white'); f(fig)
            PM.mise_en_page(fig, n, len(ETAPES), titre, il_faut, faire, attention, leg)
            fig.savefig(B.OUT / f'plan_montage_doigt_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)
    print('ok', len(ETAPES), 'étapes')
