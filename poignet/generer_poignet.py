"""Poignet du bras de Câlin : ROTATION de la pince sur elle-même (servo n° 5). Prototype : aucune validation physique.

Un STS3215 au bout de l'avant-bras, son axe dans le prolongement du bras ; la pince est vissée sur son palonnier.
Trois pièces à imprimer :
  - support du poignet : s'enfile sur le bout de l'avant-bras à la place de la pince (2 vis M3 × 30 par le côté),
    le servo y GLISSE par le haut entre des rails (derrière) et des lèvres (devant, sur sa partie haute) ;
  - barre du poignet : ferme le haut du support (2 vis M3 × 10 dans 2 inserts) ;
  - base de la pince « poignet » : la base de la pince sans son manchon, avec un moyeu vissé sur le palonnier
    par les 4 vis M2,5 du servo (5,3 mm sous tête, mesuré), têtes au fond de 4 puits.
Repère : X dans l'axe de l'avant-bras (0 = bout de l'avant-bras), Y = axe du coude, Z vers le haut de la pince ;
l'axe de rotation est la droite Y = 0, Z = 0.
Mesures utilisées (README, « Repères sur le servo ») : boîtier 45,2 × 24,4, hauteurs 28,8 / 33, palonnier Ø 19,7 qui
dépasse de 4,3, reliefs de 2 mm au dos, inserts M3 Ø 4,7 × 3,8.
Lancer : python generer_poignet.py → sortie/poignet_*.stl, sortie/verification_poignet.json"""
import sys, os, json, math
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'pince'))
from pathlib import Path
import numpy as np, manifold3d as mf, trimesh as tm
import generer_pince as G, generer_pince_v4 as V
from generer_pince import box, SL, SW, H_BAS, H_HAUT, HAUT_DEBUT, HAUT_ARC, AXE_BOUT, PAL_D, PAL_H, CERCLE_TROUS, BOSS_L, BOSS_W, BOSS_BORD, RELIEF, FOURCHE_EP, FOURCHE_L, ENT_B, VIS_ENT_Y, JEU, M3, M3_INSERT, M2_5

OUT = Path(ICI) / 'sortie'; OUT.mkdir(exist_ok=True)
def cyl_x(x0, x1, y, z, d, n=64): return mf.Manifold.cylinder(x1 - x0, d / 2, d / 2, n).rotate((0, 90, 0)).translate((x0, y, z))
def cyl_y(y0, y1, x, z, d, n=24): return mf.Manifold.cylinder(y1 - y0, d / 2, d / 2, n).rotate((-90, 0, 0)).translate((x, y0, z))
def cyl_z(x, y, z0, z1, d, n=24): return mf.Manifold.cylinder(z1 - z0, d / 2, d / 2, n).translate((x, y, z0))

# ---------------- Le servo du poignet, en place ----------------
EP_FOND, RAIL = 4.0, 3.0                 # fond contre le bout de l'avant-bras ; rails : 3 mm de vide pour les reliefs de 2 mm
X_DOS = EP_FOND + RAIL                   # dos du servo (7)
X_BAS, X_HAUT, X_PAL = X_DOS + H_BAS, X_DOS + H_HAUT, X_DOS + H_BAS + PAL_H      # 35,8 / 40,0 / 40,1
Z_PRES, Z_LOIN = -AXE_BOUT, SL - AXE_BOUT                                       # bouts du servo : −8,1 et +37,1
Z_HAUTE = HAUT_DEBUT - AXE_BOUT          # la partie haute (33 mm) commence 7,5 au-dessus de l'axe
def servo_poignet():
    s = box(X_DOS, -SW / 2, Z_PRES, X_BAS, SW / 2, Z_LOIN)
    s += box(X_BAS, -SW / 2, Z_HAUTE, X_HAUT, SW / 2, Z_LOIN) - cyl_x(X_BAS - 0.1, X_HAUT + 0.1, 0, 0, 2 * HAUT_ARC)
    s += cyl_x(X_BAS, X_PAL, 0, 0, PAL_D) + cyl_x(X_DOS - RELIEF, X_DOS, 0, 0, 5.5)
    s += box(X_DOS - RELIEF, -BOSS_W / 2, Z_LOIN - BOSS_BORD - BOSS_L, X_DOS, BOSS_W / 2, Z_LOIN - BOSS_BORD)
    return s

# ---------------- Support du poignet ----------------
MUR = 3.0
OBLONG = 2.5                                            # demi-longueur des trous oblongs du manchon
YI, ZI = FOURCHE_EP / 2 + JEU, FOURCHE_L / 2 + JEU     # intérieur du manchon (le même que celui de la pince V3)
YP = SW / 2 + JEU                                       # intérieur du logement du servo
Z_FOND = -(ZI + MUR)                                    # dessous de la pièce = face posée sur le plateau d'impression
Z_MURS = Z_LOIN + JEU                                   # dessus des murs = dessus du servo
X_LEVRE0, X_LEVRE1, LEVRE = X_HAUT + 0.2, X_HAUT + 3.0, 1.8      # lèvres devant la partie haute du servo
Z_LEVRE = Z_HAUTE + 2.5
CABLE_Z = (Z_LOIN - 29.0, Z_LOIN - 17.0)                # fenêtres des câbles (comme dans la base de la pince)
BOSS = 8.0; X_BARRE = (27.0, 37.0); INSERT_PROF = 5.0   # bossages des inserts de la barre (devant les fentes des câbles)
def support():
    m = box(-ENT_B, -(YI + MUR), Z_FOND, 0, YI + MUR, ZI) - box(-ENT_B - 1, -YI, -ZI, 0.0, YI, ZI + 1)   # manchon : dessous + 2 joues
    m += box(0, -(YI + MUR), Z_FOND, EP_FOND, YI + MUR, ZI) + box(0, -(YP + MUR), Z_FOND, EP_FOND, YP + MUR, Z_MURS)   # fond
    m += box(0, -(YP + MUR), Z_FOND, X_BAS - 0.5, YP + MUR, Z_PRES - JEU)                                 # plancher sous le servo (s'arrête avant le palonnier, qui dépasse du bout du servo)
    for s in (1, -1):
        y0, y1 = sorted((s * YP, s * (YP + MUR)))
        m += box(0, y0, Z_FOND, X_LEVRE1, y1, Z_MURS)                                                     # mur
        y0, y1 = sorted((s * (YP - 2.2), s * YP)); m += box(EP_FOND, y0, Z_PRES - JEU, X_DOS, y1, Z_MURS)  # rail derrière le servo
        y0, y1 = sorted((s * (YP - LEVRE - JEU), s * YP)); m += box(X_LEVRE0, y0, Z_LEVRE, X_LEVRE1, y1, Z_MURS)   # lèvre devant
        # lèvre BASSE, devant la partie basse du servo, de chaque côté du palonnier : sans elle le bas du servo n'était tenu
        # que par-derrière et basculait vers l'avant (montage du 21/11/2026)
        y0, y1 = sorted((s * (YP - LEVRE), s * YP)); m += box(X_BAS + 0.2, y0, Z_PRES - JEU, X_BAS + 3.0, y1, Z_HAUTE - 1.5)
        m -= box(EP_FOND, s * YP - 4 if s > 0 else -YP - MUR - 1, CABLE_Z[0], 22, YP + MUR + 1 if s > 0 else -YP + 4, Z_MURS + 1)   # fente du câble, OUVERTE VERS LE HAUT : le servo descend avec ses câbles branchés
        # bossage de l'insert de la barre (dessous en biais : s'imprime sans support)
        y0, y1 = sorted((s * (YP + MUR), s * (YP + MUR + BOSS)))
        b = box(X_BARRE[0] - 1, y0, Z_MURS - 20, X_BARRE[1] + 1, y1, Z_MURS)
        coupe = mf.Manifold.extrude(mf.CrossSection([[(0, 0), (BOSS + 0.1, 0), (BOSS + 0.1, BOSS + 0.1)]]), 14).rotate((90, 0, 90)).translate((X_BARRE[0] - 2, 0, 0))
        coupe = coupe.translate((0, s * (YP + MUR), Z_MURS - 20)) if s > 0 else coupe.mirror((0, 1, 0)).translate((0, -(YP + MUR), Z_MURS - 20))
        m += b - coupe
        m -= cyl_z(sum(X_BARRE) / 2, s * (YP + MUR + BOSS / 2), Z_MURS - INSERT_PROF, Z_MURS + 0.1, M3_INSERT)
    # 2 vis M3 × 30 par le côté +Y. Trous OBLONGS (± 2,5 mm le long du bras) : au premier montage (21/11/2026) les trous ronds
    # ne tombaient pas en face de ceux de l'avant-bras ; la position réelle de ces trous n'a jamais été mesurée.
    for dz in (-VIS_ENT_Y, VIS_ENT_Y):
        for dx in (-OBLONG, OBLONG): m -= cyl_y(YI - 1, YI + MUR + 1, -ENT_B / 2 + dx, dz, M3)
        m -= box(-ENT_B / 2 - OBLONG, YI - 1, dz - M3 / 2, -ENT_B / 2 + OBLONG, YI + MUR + 1, dz + M3 / 2)
    return m
def barre():
    """Ferme le haut du support. Une LANGUETTE descend derrière le haut du servo : les fentes des câbles ont supprimé
    les rails à cet endroit, c'est elle qui empêche le haut du servo de reculer. S'imprime retournée (languette en l'air)."""
    y = YP + MUR + BOSS
    m = box(X_BARRE[0] - 1, -y, Z_MURS, X_BARRE[1] + 1, y, Z_MURS + 4) + box(EP_FOND, -(YP + MUR), Z_MURS, X_BARRE[0], YP + MUR, Z_MURS + 4)
    m += box(EP_FOND + 0.2, -8.0, Z_MURS - 4.5, X_DOS - 0.2, 8.0, Z_MURS)                      # languette (au-dessus du bossage du servo)
    for s in (1, -1): m -= cyl_z(sum(X_BARRE) / 2, s * (YP + MUR + BOSS / 2), Z_MURS - 0.1, Z_MURS + 4.1, M3)
    return m

# ---------------- Base de la pince pour le poignet ----------------
VIS_PAL, SOUS_TETE = 5.3, 2.8            # vis M2,5 du servo (mesurées) ; plastique sous la tête → 2,5 mm de prise dans le palonnier
X_BASE = X_LEVRE1 + 1.5                  # la base de la pince commence 1,5 mm devant les lèvres (44,5)
DEC = X_BASE - (G.PIV_LIBRE[0] - 6.5)    # du repère de la pince au repère du poignet : X + DEC, Z − ZC
X_FOND_PINCE = G.X0S - JEU + DEC         # fond du logement du servo de la pince, où débouchent les 4 puits
TROUS = [(CERCLE_TROUS / 2 * math.cos(math.radians(45 + 90 * k)), CERCLE_TROUS / 2 * math.sin(math.radians(45 + 90 * k))) for k in range(4)]
def vers_poignet(m): return m.translate((DEC, 0, -G.ZC))
def base_pince():
    b = vers_poignet(G.base(manchon=False))
    b += cyl_x(X_PAL + 1.0, X_BASE, 0, 0, 19.8) + cyl_x(X_BASE - 0.5, X_FOND_PINCE, 0, 0, 36)      # col + moyeu
    b += mf.Manifold.cylinder(1.0, 9.0, 9.9, 64).rotate((0, 90, 0)).translate((X_PAL, 0, 0))        # patin en cône sur le palonnier
    b -= vers_poignet(box(G.X0S - JEU, G.SY0 - JEU, 0, G.X0S + SL + JEU, G.SY1 + JEU, 60))          # le logement du servo reste libre
    # L'axe de rotation passe à 15 mm de l'axe du servo de la pince : 2 des 4 vis tombent À CÔTÉ du logement du servo.
    # Pilier de la bride de ce côté élargi vers l'extérieur, car le passage du tournevis le traverse.
    b += vers_poignet(box(G.BRIDE_X0 + 1, G.SY0 - JEU - 3 - 12, G.Z_BASE, G.BRIDE_X0 + 9, G.SY0 - JEU - 3 - 7.9, G.BRIDE_Z))
    for y, z in TROUS:
        b -= cyl_x(X_PAL - 0.1, X_FOND_PINCE + 0.1, y, z, M2_5, 24)
        b -= cyl_x(X_PAL + SOUS_TETE, X_FOND_PINCE + 120, y, z, 5.4, 24)      # puits de la tête, prolongé en passage de tournevis jusqu'à l'avant
    b -= cyl_x(X_PAL - 0.1, X_PAL + 3.0, 0, 0, 7.0)                                                  # vis centrale du palonnier
    return b

SERVO, SUPPORT, BARRE, BASE = servo_poignet(), support(), barre(), base_pince()
def rouler(m, deg): return m.rotate((deg, 0, 0))
def pince_complete(delta):
    pm, mm, _ = V.mobile(delta)
    return [vers_poignet(x) for x in (G.BRIDE, G.SERVO, V.PF, V.MACH_F, pm, mm)]
def mesh(m): return G.mesh(m)

if __name__ == '__main__':
    r = {'etat': 'PROTOTYPE, aucune validation physique'}
    fixe = SUPPORT + BARRE + SERVO + box(-60, -FOURCHE_EP / 2, -FOURCHE_L / 2, 0, FOURCHE_EP / 2, FOURCHE_L / 2)
    assert (SUPPORT ^ SERVO).volume() < 0.01 and (BARRE ^ SERVO).volume() < 0.01, 'le support touche le servo du poignet'
    assert (BASE ^ vers_poignet(G.SERVO)).volume() < 0.01, 'la base touche le servo de la pince'
    # le servo glisse par le haut : aucune matière sur son trajet
    for dz in range(0, 50, 2): assert (SUPPORT ^ SERVO.translate((0, 0, dz))).volume() < 0.01, f'le servo ne glisse pas (bloqué à {dz} mm)'
    # rotation de la pince : rien ne touche le support de −90° à +90° (pince ouverte, au milieu, fermée)
    pire = 0.0
    for delta in (-40.2, -13.1, 14.0):
        mob = [BASE] + pince_complete(delta)
        for a in range(-90, 91, 10):
            for x in mob: pire = max(pire, (rouler(x, a) ^ fixe).volume())
    assert pire < 0.01, f'la pince touche le support en tournant ({pire:.1f} mm3)'
    r['rotation'] = 'aucun contact de −90° à +90°, pince ouverte, au milieu ou fermée'
    # tournevis des 4 vis du palonnier : passage libre par l'avant, servo de la pince retiré
    for y, z in TROUS: assert (cyl_x(X_PAL + SOUS_TETE + 0.05, X_FOND_PINCE + 120, y, z, 4.5, 24) ^ (BASE + vers_poignet(V.PF))).volume() < 0.01, 'le tournevis ne passe pas'
    r['tournevis_palonnier'] = 'libre par l\'avant (servo de la pince retiré, mâchoire mobile non montée)'
    r['prise_des_vis_dans_le_palonnier_mm'] = round(VIS_PAL - SOUS_TETE, 1)
    r['allongement_du_bras_mm'] = round(X_FOND_PINCE + JEU - (MUR + JEU), 1)
    dens = 1.25e-3
    r['masses_g'] = {'support': round(SUPPORT.volume() * dens), 'barre': round(BARRE.volume() * dens, 1), 'base de la pince (poignet)': round(BASE.volume() * dens),
                     'base de la pince (ancienne)': round(G.BASE.volume() * dens), 'servo': 55}
    r['ajout_au_bout_du_bras_g'] = r['masses_g']['support'] + round(r['masses_g']['barre']) + 55 + r['masses_g']['base de la pince (poignet)'] - r['masses_g']['base de la pince (ancienne)']
    r['visserie'] = ['2 vis M3 × 30 (celles de la pince, sur l\'avant-bras)', '2 vis M3 × 10 + 2 inserts M3 (barre)', '4 vis M2,5 du servo (palonnier)']
    # export, pièces posées pour l'impression
    for nom, m in (('poignet_support', SUPPORT.translate((0, 0, -Z_FOND))), ('poignet_barre', BARRE.rotate((180, 0, 0)).translate((0, 0, Z_MURS + 4))),
                   ('poignet_base_pince', BASE.translate((0, 0, G.ZC - G.Z_BASE)))):
        assert len(m.decompose()) == 1, f'{nom} : pièce en plusieurs morceaux'
        mesh(m).export(OUT / f'{nom}.stl'); r.setdefault('stl', []).append(f'{nom}.stl')
    json.dump(r, open(OUT / 'verification_poignet.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False, indent=1))
