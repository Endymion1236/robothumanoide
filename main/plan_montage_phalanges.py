"""Plan de montage illustré du DOIGT lui-même (base + 3 phalanges) : dans quel sens tourner chaque pièce, comment fixer les
articulations (axes en filament), comment passer et bloquer les deux fils. Demande de Nicolas, 26/11/2026.
Une page par étape, PDF + PNG → sortie/plan_montage_phalanges.pdf. PROTOTYPE : vérifié par le calcul, jamais monté."""
import sys, os
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import generer_doigt as D, generer_banc_doigt as B, plan_montage_epaule_outils as PM

C = {'base': '#c9a35a', 'p1': '#5b8bd6', 'p2': '#3aa6a6', 'p3': '#d6a62e', 'axe': '#e0602a', 'ferme': '#d0302a', 'ouvre': '#2e7d32', 'noeud': '#111111'}
COUL = [C['base'], C['p1'], C['p2'], C['p3']]
GRIS = PM.GRIS
L1, L2, L3 = D.LONGUEURS; R = D.R
X_PUITS = L1 + L2 + L3 - 9.0                       # le puits vertical du bout du doigt, dans le repère du doigt tendu
L_AXE = 17.0                                      # filament : 14 mm de large + 1,5 mm de chaque côté pour les têtes
P = lambda *v: np.array(v, float)
def doigt(angles=(0, 0, 0), couleurs=COUL): return list(zip(D.doigt(list(angles)), couleurs))
def axe(x, depasse=1.5, y0=None): return D.cyl_y(x, 0, -D.LARGEUR / 2 - depasse if y0 is None else y0, (D.LARGEUR / 2 + depasse) if y0 is None else y0 + L_AXE, 1.75, 16)
def fil(points, c, d=0.9): return [(B.tige(P(*a), P(*b), d), c) for a, b in zip(points, points[1:])]
def coupe(m): return m ^ D.box(-200, 0.0, -50, 200, 50, 50)            # moitié arrière seulement : on voit les canaux et le puits de profil
def boule(p, d=3.0): return D.cyl_z(p[0], p[1], p[2] - d / 2, p[2] + d / 2, d, 12)
ETAPES = []
def etape(titre, il_faut, faire, attention=None, leg=()):
    def deco(f): ETAPES.append((titre, il_faut, faire, attention, leg, f)); return f
    return deco

LEG4 = [(C['base'], 'base'), (C['p1'], 'phalange 1'), (C['p2'], 'phalange 2'), (C['p3'], 'phalange 3 (le bout)')]

@etape('Reconnaître les 4 pièces et les ranger dans l\'ordre', ['la base et les 3 phalanges imprimées', 'un réglet'],
       ['La BASE est la seule qui a deux pattes percées (pour la visser). Elle fait 39 mm de long.',
        'La phalange 1 est la plus LONGUE des trois : 42 mm de bout en bout.', 'La phalange 2 lui ressemble, en plus court : 34 mm.',
        'La phalange 3 est le BOUT du doigt : 26 mm, un bout arrondi, et un petit trou vertical qui la traverse de part en part, juste devant sa languette (le « puits »).',
        'Pose-les à la file comme sur le dessin : base, 1, 2, 3.'],
       'Les phalanges 1 et 2 ne se distinguent que par leur longueur : mesure-les.', LEG4)
def e1(fig):
    ax, = PM.panneaux(fig, 1, ['Les 4 pièces à la file, écartées (vue du côté du DOS de la main)'])
    ecart = [0, 14, 28, 42]; pcs = D.doigt([0, 0, 0])
    PM.dessiner(ax, [(p.translate((e, 0, 0)), c) for p, e, c in zip(pcs, ecart, COUL)], vue=(32, -62), marge=0.6)
    for x, t in ((-18, 'BASE\n(2 pattes)'), (14 + 15, 'phalange 1\n42 mm'), (28 + L1 + 11, 'phalange 2\n34 mm'), (42 + L1 + L2 + 8, 'phalange 3\n26 mm, bout rond')):
        PM.etiquette(ax, (x, 0, -R), t, (0, -95), taille=12)
    PM.etiquette(ax, (42 + X_PUITS, 0, R), 'le puits', (90, 30), taille=11)

@etape('Le sens de chaque pièce : languette derrière, fourche devant, pont côté DOS', ['une phalange (la 1, par exemple)'],
       ['Chaque phalange a deux bouts différents. Le bout MINCE (5 mm de large, un trou) est la LANGUETTE : elle va vers la base.',
        'Le bout LARGE fendu en deux oreilles est la FOURCHE : elle va vers le bout du doigt.',
        'Regarde la fourche : d\'un côté la fente est OUVERTE jusqu\'au bord, de l\'autre un petit PONT de plastique la referme.',
        'Le côté du PONT est le DOS du doigt (le dessus de la main). Le côté ouvert est la PAUME : c\'est par là que le doigt plie.',
        'Même repère sur la languette : son côté PLAT, plus bas que le reste, est le côté du dos.',
        'Tourne les 4 pièces pour que tous les ponts et tous les plats soient du même côté, vers le haut.'],
       'Une phalange montée à l\'envers plie vers le dos et ne se tend plus : vérifie le pont AVANT de poser un axe.',
       [(C['p1'], 'phalange 1')])
def e2(fig):
    a1, a2 = PM.panneaux(fig, 2, ['Vue du côté du DOS (les ponts en haut)', 'Vue du côté de la PAUME (fente ouverte)'])
    ph = D.PHALANGES[0]
    PM.dessiner(a1, [(ph, C['p1'])], vue=(38, -60), marge=0.8)
    PM.etiquette(a1, (-3, 0, D.R_L), 'LANGUETTE\n(vers la base)\ndessus PLAT', (-140, 20)); PM.etiquette(a1, (L1 + 2, 0, R), 'le PONT\n= côté DOS', (120, 40))
    PM.etiquette(a1, (L1, -D.LARGEUR / 2, 0), 'FOURCHE\n(vers le bout)', (110, -40))
    PM.dessiner(a2, [(ph.rotate((180, 0, 0)), C['p1'])], vue=(38, -60), marge=0.8)
    PM.etiquette(a2, (L1 - 4, 0, R), 'fente OUVERTE\n= côté PAUME', (130, 40)); PM.etiquette(a2, (-3, 0, R), 'languette :\ncôté rond', (-140, 20))

@etape('Emboîter une articulation et la vérifier, SANS axe', ['la base et la phalange 1, ponts en haut'],
       ['Présente la languette de la phalange 1 devant la fourche de la base, les deux ponts et plats vers le haut.',
        'Glisse la languette dans la fente, par en dessous (côté PAUME) ou bien droit par l\'avant : par le dessus, le pont l\'arrête.',
        'Aligne les trous : tu dois voir le jour à travers les deux oreilles et la languette.',
        'Tiens l\'ensemble entre deux doigts et essaie : la phalange doit PLIER vers la paume jusqu\'à l\'équerre (90°)…',
        '…et, dans l\'autre sens, s\'arrêter DROITE, en butée sous le pont. Elle ne doit pas se retourner vers le dos.',
        'Si elle frotte dans la fente : un coup de lime sur les flancs de la languette (jeu prévu : 0,25 mm par côté).'],
       'Si la phalange se retourne vers le dos, elle est à l\'envers : sors-la, retourne-la, recommence.',
       [(C['base'], 'base'), (C['p1'], 'phalange 1')])
def e3(fig):
    a1, a2 = PM.panneaux(fig, 2, ['La languette entre par en dessous (côté paume)', 'Vérification : droite en butée, pliée à 90°'])
    PM.dessiner(a1, [(D.BASE, C['base']), (D.PHALANGES[0].translate((4, 0, -16)), C['p1'])], vue=(18, -70), marge=0.7)
    PM.guide(a1, (2, 0, -14), (0, 0, -2)); PM.etiquette(a1, (2, 0, R), 'pont de la base', (130, 30)); PM.etiquette(a1, (8, 0, -16 + D.R_L), 'plat de la languette', (120, -10))
    PM.dessiner(a2, [(D.BASE, C['base']), (D.PHALANGES[0], C['p1']), (D.PHALANGES[0].rotate((0, 90, 0)), '#a9c2ea')], vue=(8, -88), marge=0.75)
    PM.etiquette(a2, (L1 - 6, 0, R), 'TENDU : en butée', (120, 30)); PM.etiquette(a2, (0, 0, -L1 + 6), 'PLIÉ à 90°', (90, 0))

@etape('L\'axe : un bout de filament, une tête de chaque côté', ['du filament de 1,75 mm (PETG ou PLA)', 'une pince coupante, un réglet', 'le fer à souder'],
       ['Coupe 3 morceaux de filament bien DROITS de 17 mm (redresse-le entre les doigts s\'il est courbe).',
        'Sur chaque morceau, fais d\'abord UNE tête : touche un bout 1 seconde avec le plat du fer chaud, il s\'écrase en petit champignon.',
        'Articulation emboîtée, trous alignés : pousse l\'axe par le bout sans tête, à travers oreille, languette, oreille.',
        'Il traverse les 14 mm et dépasse de 1,5 mm de l\'autre côté. S\'il force trop : repasse un foret de 2 mm À LA MAIN dans les oreilles.',
        'Écrase le bout qui dépasse avec le fer, 1 seconde : la deuxième tête retient l\'axe.',
        'Vérifie : la phalange plie et se tend toute seule sous son poids, sans point dur.'],
       'Fer chaud : tiens la pièce par l\'autre bout, ne touche QUE le filament (1 seconde), pas l\'oreille. Une tête trop écrasée contre l\'oreille freine : laisse un cheveu de jeu.',
       [(C['axe'], 'axe en filament (17 mm)')])
def e4(fig):
    a1, a2 = PM.panneaux(fig, 2, ['L\'axe entre par le flanc', 'En place : 1,5 mm dépasse de chaque côté'])
    pcs = [(D.BASE, C['base']), (D.PHALANGES[0], C['p1'])]
    PM.dessiner(a1, pcs + [(axe(0, y0=-D.LARGEUR / 2 - 22), C['axe'])], vue=(26, -38), marge=0.7)
    PM.guide(a1, (0, -D.LARGEUR / 2 - 5, 0), (0, -D.LARGEUR / 2, 0)); PM.etiquette(a1, (0, -D.LARGEUR / 2 - 20, 0), 'tête déjà faite\nde ce côté', (-120, 30))
    PM.dessiner(a2, pcs + [(axe(0), C['axe'])], vue=(62, -88), marge=0.7, cadre=(-22, 22, -14, 14, -10, 10))
    PM.etiquette(a2, (0, -D.LARGEUR / 2 - 1.5, 0), 'tête', (-70, -50)); PM.etiquette(a2, (0, D.LARGEUR / 2 + 1.5, 0), 'tête à écraser', (-130, 20))

@etape('Les trois articulations, de la base vers le bout', ['la phalange 2, la phalange 3', '2 axes'],
       ['Phalange 2 : sa languette dans la fourche de la phalange 1, ponts du même côté. Vérifie SANS axe (étape 3), puis pose l\'axe (étape 4).',
        'Phalange 3 (le bout rond) : pareil, dans la fourche de la phalange 2. Son puits se retrouve juste devant l\'articulation.',
        'Pose le doigt à plat, ponts vers le haut : il doit être DROIT, les trois phalanges en butée.',
        'Prends-le par la base, paume vers le bas : les trois phalanges doivent tomber et plier d\'elles-mêmes.',
        'Regarde dans les deux petits trous à l\'arrière de la base : tu dois voir le jour jusqu\'au puits, doigt tendu.'],
       'Si on ne voit pas le jour dans un canal : un fil d\'imprimante ou une goutte bouche le trou. Passe une aiguille ou un foret de 1,5 mm À LA MAIN.',
       LEG4 + [(C['axe'], 'les 3 axes')])
def e5(fig):
    a1, a2 = PM.panneaux(fig, 2, ['Doigt tendu, vu du dos', 'Tenu par la base : il plie tout seul vers la paume'])
    axes = lambda ang: [(axe(0), C['axe'])]
    PM.dessiner(a1, doigt() + [(axe(x), C['axe']) for x in (0, L1, L1 + L2)], vue=(34, -62), marge=0.62)
    PM.etiquette(a1, (X_PUITS, 0, R), 'puits', (90, 40)); PM.etiquette(a1, (-D.L_BASE, 0, D.Z_FIL), '2 canaux\n(entrées)', (-120, 10))
    PM.dessiner(a2, doigt((60, 60, 60)), vue=(8, -88), marge=0.62)

@etape('Les deux fils : par les canaux, jusqu\'au puits', ['2 fils de pêche tressés de 30 cm', 'une pince à épiler', 'une aiguille'],
       ['Doigt TENDU, à plat, ponts vers le haut. Marque un des fils au feutre : ce sera celui du DESSUS (il ouvre).',
        'Fil du DESSOUS (côté paume, il FERME) : entre-le par le trou du BAS à l\'arrière de la base. Pousse-le : il traverse les 4 pièces.',
        'Quand il arrive dans le puits, attrape-le à la pince à épiler par la bouche du puits côté PAUME et sors-en 5 cm.',
        'Fil du DESSUS (marqué, il OUVRE) : entre-le par le trou du HAUT de la base, pousse-le jusqu\'au puits.',
        'Sors-le par la bouche du puits côté DOS, puis repique-le tout droit dans le puits, de haut en bas : il ressort côté PAUME, à côté du premier.',
        'Tu as maintenant les deux bouts qui sortent sous le bout du doigt.'],
       'Si le fil bute à une articulation : plie-la de quelques degrés puis retends-la en poussant. Un fil coupé net (ciseaux, pas arraché) entre mieux ; une goutte de colle séchée sur son bout le raidit.',
       [(C['ferme'], 'fil du dessous : FERME'), (C['ouvre'], 'fil du dessus : OUVRE')])
def e6(fig):
    a1, a2 = PM.panneaux(fig, 2, ['Doigt coupé dans sa longueur : les deux canaux', 'De près : le bout du doigt, coupé'])
    z = D.Z_FIL
    bas = fil([(-D.L_BASE - 30, 0, -z), (X_PUITS, 0, -z), (X_PUITS - 1, 0, -R - 16)], C['ferme'])
    haut = fil([(-D.L_BASE - 30, 0, z), (X_PUITS, 0, z), (X_PUITS + 1, 0, -R - 16)], C['ouvre'])
    transp = [(coupe(p), '#d9d9d9') for p, _ in doigt()]
    PM.dessiner(a1, transp + bas + haut, vue=(4, -89), marge=0.62)
    PM.etiquette(a1, (-D.L_BASE - 25, 0, z), 'DESSUS (ouvre)', (-20, 45), coul=C['ouvre']); PM.etiquette(a1, (-D.L_BASE - 25, 0, -z), 'DESSOUS (ferme)', (10, -70), coul=C['ferme'])
    PM.etiquette(a1, (X_PUITS, 0, -R - 14), 'les 2 bouts\nsortent côté paume', (-150, -30))
    PM.dessiner(a2, [(coupe(D.PHALANGES[2].translate((L1 + L2, 0, 0))), '#d9d9d9')] + bas + haut, vue=(4, -89), marge=0.8, cadre=(L1 + L2 - 4, L1 + L2 + L3 + 6, -8, 8, -R - 18, R + 6))
    PM.etiquette(a2, (X_PUITS, 0, R), 'puits (côté DOS)', (110, 30)); PM.etiquette(a2, (X_PUITS, 0, -R), 'bouche côté PAUME', (60, -40))

@etape('Le nœud dans le puits, la colle, et l\'essai à la main', ['colle cyano (une petite goutte)', 'des ciseaux'],
       ['Noue les deux bouts ENSEMBLE, tout près du doigt : trois nœuds simples serrés l\'un sur l\'autre (une petite boule de 2 mm).',
        'Coupe ce qui dépasse à 3 mm du nœud.', 'Tire doucement les deux fils côté base, ensemble : le nœud rentre dans le puits et s\'y arrête (les canaux sont trop fins pour lui).',
        'Doigt tendu, les deux fils légèrement tendus : dépose UNE petite goutte de colle sur le nœud, par la bouche du puits. Laisse sécher 5 minutes sans bouger.',
        'Essai : tire le fil du DESSOUS, le doigt se ferme. Tire le fil du DESSUS (marqué), il se rouvre jusqu\'aux butées.',
        'Il faut tirer environ 16 mm de fil pour fermer à fond. Dis-moi dans quel ordre plient les phalanges et s\'il faut forcer.'],
       'Très peu de colle : si elle coule dans un canal, le fil y reste collé et le doigt est bloqué. Sans colle, le nœud se promène de 7 mm dans le puits : le doigt aurait du jeu.',
       [(C['ferme'], 'fil du dessous : FERME'), (C['ouvre'], 'fil du dessus : OUVRE'), (C['noeud'], 'le nœud')])
def e7(fig):
    a1, a2 = PM.panneaux(fig, 2, ['Le nœud rentré dans le puits (bout du doigt coupé)', 'On tire le fil du dessous : le doigt se ferme'])
    z = D.Z_FIL
    bas = fil([(-D.L_BASE - 30, 0, -z), (X_PUITS, 0, -z)], C['ferme']); haut = fil([(-D.L_BASE - 30, 0, z), (X_PUITS, 0, z), (X_PUITS + 0.3, 0, -z)], C['ouvre'])
    PM.dessiner(a1, [(coupe(D.PHALANGES[2].translate((L1 + L2, 0, 0))), '#d9d9d9')] + bas + haut + [(boule((X_PUITS, -0.5, -z - 0.6), 2.4), C['noeud'])], vue=(4, -89), marge=0.8,
                cadre=(L1 + L2 - 4, L1 + L2 + L3 + 6, -8, 8, -R - 8, R + 8))
    PM.etiquette(a1, (X_PUITS, -0.5, -z - 0.6), 'nœud + goutte de colle', (90, -60))
    PM.dessiner(a2, doigt((70, 70, 70)), vue=(8, -88), marge=0.95)
    PM.etiquette(a2, (-D.L_BASE, 0, -z), 'on tire ICI\n(fil du dessous)', (-130, -30), coul=C['ferme'])

def page_garde(pdf):
    fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white')
    fig.suptitle('Le doigt : monter la base et les 3 phalanges', fontsize=20, weight='bold', y=0.985)
    a1 = fig.add_subplot(1, 2, 1, projection='3d'); PM.dessiner(a1, doigt() + [(axe(x), C['axe']) for x in (0, L1, L1 + L2)], vue=(34, -62), marge=0.62)
    a1.set_title('Doigt tendu, vu du dos', fontsize=14, weight='bold')
    a2 = fig.add_subplot(1, 2, 2, projection='3d'); PM.dessiner(a2, doigt((70, 70, 70)), vue=(8, -88), marge=0.62); a2.set_title('Doigt fermé, de profil', fontsize=14, weight='bold')
    fig.text(0.03, 0.03, 'Il te faut : la base et les 3 phalanges imprimées · du filament de 1,75 mm (3 axes de 17 mm) · 2 fils de pêche tressés de 30 cm · fer à souder,\n'
             'pince coupante, pince à épiler, aiguille, ciseaux, une goutte de colle cyano.\n'
             'Les trois repères à retenir : la LANGUETTE (bout mince) va vers la base · le PONT de la fourche est du côté du DOS · le doigt plie vers la PAUME.\n'
             'Fil du DESSOUS (paume) = il ferme · fil du DESSUS (dos) = il ouvre.\n'
             'PROTOTYPE : vérifié par le calcul, jamais monté. Si une pièce ne correspond pas au dessin, arrête-toi et dis-le-moi.', fontsize=12.5)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.16, wspace=0.02)
    fig.savefig(D.OUT / 'plan_montage_phalanges_00.png', dpi=90); pdf.savefig(fig); plt.close(fig)

if __name__ == '__main__':
    with PdfPages(D.OUT / 'plan_montage_phalanges.pdf') as pdf:
        page_garde(pdf)
        for n, (titre, il_faut, faire, attention, leg, f) in enumerate(ETAPES, 1):
            fig = plt.figure(figsize=(16.5, 11.7)); fig.patch.set_facecolor('white'); f(fig)
            PM.mise_en_page(fig, n, len(ETAPES), titre, il_faut, faire, attention, leg)
            fig.savefig(D.OUT / f'plan_montage_phalanges_{n:02d}.png', dpi=90); pdf.savefig(fig); plt.close(fig)
    print('ok', len(ETAPES), 'étapes')
