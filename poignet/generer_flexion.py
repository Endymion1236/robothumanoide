"""Poignet du bras de Câlin : FLEXION (servo n° 6), placée AVANT la rotation. Prototype : aucune validation physique.

On reprend ce qui marche déjà au coude : un petit coude au bout de l'avant-bras.
  - SUPPORT DE FLEXION : un manchon qui s'enfile sur le bout de l'avant-bras (comme la pince) + le BERCEAU du coude
    (mêmes cotes, socle raccourci), en une seule pièce. Le servo n° 6 s'y pose comme au coude, tenu par la même BRIDE.
  - FOURCHE COURTE en deux moitiés, vissée sur les deux disques du servo (4 vis M2,5 de 5,3 mm par côté, comme
    l'avant-bras). Son bout a exactement la forme du bout de l'avant-bras : le support de rotation (ou la pince)
    s'y enfile sans modification, tenu par les 2 vis M3 × 30 qui ferment la fourche.
Repère : X dans l'axe de l'avant-bras (0 = bout de l'avant-bras), Y = axe du coude, Z vers le haut.
L'axe de flexion est parallèle à Y, à X_AXE du bout de l'avant-bras.
Lancer : python generer_flexion.py → sortie/flexion_*.stl, sortie/verification_flexion.json"""
import sys, os, json, math
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'epaule'))
_argv, sys.argv = sys.argv, ['x']
import generer_epaule as EP, generer_poignet as P
sys.argv = _argv
from generer_epaule import F, B, box, cyl_y, mesh, placer, tourner_y
import manifold3d as mf

OUT = P.OUT
MUR, JEU = 3.0, 0.2
YI, ZI = P.YI, P.ZI                               # intérieur du manchon : celui de la pince et du support de rotation
EP_F = F.z_haut + F.plaque_T                      # épaisseur de la fourche : 45,3
Y_BAS = -EP_F / 2                                 # dessous de la fourche (plaque basse) : −22,65
Y_SOCLE = Y_BAS - 2.0 - B.base_T                  # dessous du socle du berceau : la fourche passe 2 mm au-dessus, comme au coude
AR_BERCEAU = 66.0 - EP.AXE_BERCEAU                # le berceau s'étend 40,5 mm derrière l'axe
X_AXE = AR_BERCEAU + 0.5                          # axe de flexion : 41 mm après le bout de l'avant-bras
AV_SOCLE = 13.5                                   # socle gardé 13,5 mm devant l'axe (sous le bout du servo)
R_SOCLE = 25.5                                    # devant l'axe, le socle est arrondi : rien au-delà de ce rayon
L_FOURCHE = 42.0                                  # de l'axe au bout de la fourche (cherché : le plus court sans contact)
ENT_L = F.entretoise_B_L                          # entretoise du bout : 15, comme l'avant-bras
FLEX_MAX = 90

def vers_poignet(m): return placer(m, EP.R_BERCEAU, (X_AXE + EP.AXE_BERCEAU, Y_SOCLE, -B.base_W / 2))
SERVO, BRIDE = vers_poignet(EP.SERVO_C), vers_poignet(EP.BRIDE_C)

def support():
    garde = box(X_AXE - AR_BERCEAU, Y_SOCLE - 1, -25.0, X_AXE + AV_SOCLE, Y_SOCLE + 60, 25.0)
    garde -= box(X_AXE, Y_SOCLE - 1, -40, X_AXE + 40, Y_SOCLE + B.base_T + 0.01, 40) - cyl_y(X_AXE, 0, Y_SOCLE - 2, Y_SOCLE + B.base_T + 1, 2 * R_SOCLE, 128)
    m = vers_poignet(EP.BERCEAU_C) ^ garde                                                   # le berceau du coude, socle raccourci
    m += box(-ENT_L, -(YI + MUR), -(ZI + MUR), 0, YI + MUR, ZI + MUR) - box(-ENT_L - 1, -YI, -ZI, 0.01, YI, ZI)   # manchon
    m += box(-ENT_L, Y_SOCLE, -25.0, X_AXE - AR_BERCEAU + 0.1, -YI, 25.0)                     # le socle se prolonge sous le manchon
    for s in (1, -1):                                                                         # deux équerres entre le manchon et le socle
        z0, z1 = sorted((s * (ZI + MUR), s * 25.0)); m += box(-ENT_L, Y_SOCLE, z0, 0, -YI + 8, z1)
    for dz in (-F.vis_M3_Y, F.vis_M3_Y): m -= cyl_y(-ENT_L / 2, dz, YI - 1, YI + MUR + 1, 3.4, 24)   # 2 vis M3 × 30, par le côté +Y (manchon fermé, comme la pince)
    return m - box(-ENT_L - 1, -YI, -ZI, 0.01, YI, ZI)

def moitie(haute):
    """Une moitié de la fourche courte, axe à l'origine, vers +X. Mêmes cotes que l'avant-bras V1.2 (validé au coude)."""
    g = F; y0 = Y_BAS + (g.z_haut if haute else 0); x0 = L_FOURCHE - ENT_L
    m = box(0, y0, -g.plaque_W / 2, L_FOURCHE, y0 + g.plaque_T, g.plaque_W / 2) + cyl_y(0, 0, y0, y0 + g.plaque_T, 2 * g.bout_R, 96)
    if haute:
        m += cyl_y(0, 0, y0 - g.surelev, y0, 2 * g.patin_R, 64)                               # patin sur le palonnier
        yb = Y_BAS + g.plaque_T + g.demi_H + g.jeu_serrage
        m += box(x0, yb, -g.plaque_W / 2, L_FOURCHE, y0 + 0.1, g.plaque_W / 2)
        for s in (1, -1): m -= cyl_y(x0 + ENT_L / 2, s * g.vis_M3_Y, yb - 0.1, y0 + g.plaque_T + 0.1, g.vis_M3_D, 24)
        ya, yl0, yl1 = y0 - g.surelev - 0.1, y0 + g.plaque_T - g.lamage_P, y0 + g.plaque_T + 0.1
    else:
        yh = y0 + g.plaque_T + g.demi_H
        m += box(x0, y0 + g.plaque_T - 0.1, -g.plaque_W / 2, L_FOURCHE, yh, g.plaque_W / 2)
        for s in (1, -1): m -= cyl_y(x0 + ENT_L / 2, s * g.vis_M3_Y, yh - 5.0, yh + 0.1, g.insert_D, 24)    # inserts de 3,8 mm de haut
        ya, yl0, yl1 = y0 - 0.1, y0 - 0.1, y0 + g.lamage_P
    for sx in (1, -1):
        for sz in (1, -1):
            m -= cyl_y(sx * g.trou_d, sz * g.trou_d, ya, y0 + g.plaque_T + 0.1, g.vis_disque_D, 24)
            m -= cyl_y(sx * g.trou_d, sz * g.trou_d, yl0, yl1, g.lamage_D, 24)
    return (m - cyl_y(0, 0, ya, y0 + g.plaque_T + 0.1, g.centre_D, 32)).translate((X_AXE, 0, 0))

SUPPORT, BASSE, HAUTE = support(), moitie(False), moitie(True)
def flechir(m, angle): return tourner_y(m, angle, (X_AXE, 0.0))
def au_bout(m): return m.translate((X_AXE + L_FOURCHE, 0, 0))          # une pièce du repère du poignet (rotation), posée au bout de la fourche
def suite(delta=-13.1, roulis=0):
    """Tout ce que porte la fourche : support de rotation, barre, servo n° 5, base de la pince, pince V4."""
    return [au_bout(x) for x in [P.SUPPORT, P.BARRE, P.SERVO] + [P.rouler(y, roulis) for y in [P.BASE] + P.pince_complete(delta)]]

if __name__ == '__main__':
    r = {'etat': 'PROTOTYPE, aucune validation physique'}
    avb = box(-70, -EP_F / 2, -F.plaque_W / 2, 0, EP_F / 2, F.plaque_W / 2)
    fixe = SUPPORT + BRIDE + SERVO + avb
    assert len(SUPPORT.decompose()) == 1, 'support en plusieurs morceaux'
    assert (SUPPORT ^ SERVO).volume() < 0.01 and (SUPPORT ^ avb).volume() < 0.01, 'le support touche le servo ou l\'avant-bras'
    assert ((BASSE + HAUTE) ^ SERVO).volume() < 0.5, 'la fourche touche le servo'
    pire = 0.0
    for roulis, delta in ((0, -13.1), (90, 14.0), (-90, -40.2)):
        mob = [BASSE, HAUTE] + suite(delta, roulis)
        for a in range(-FLEX_MAX, FLEX_MAX + 1, 10):
            for x in mob: pire = max(pire, (flechir(x, a) ^ fixe).volume())
    assert pire < 0.5, f'contact pendant la flexion ({pire:.1f} mm3)'
    r['flexion'] = f'aucun contact de −{FLEX_MAX}° à +{FLEX_MAX}°, pince droite ou tournée de ±90°'
    dens = 1.25e-3
    r['masses_g'] = {'support de flexion': round(SUPPORT.volume() * dens), 'moitié basse': round(BASSE.volume() * dens), 'moitié haute': round(HAUTE.volume() * dens), 'bride': 2, 'servo': 55}
    r['ajout_au_bout_du_bras_g'] = sum(r['masses_g'].values())
    r['allongement_du_bras_mm'] = round(X_AXE + L_FOURCHE, 1)
    r['axe_de_flexion_apres_le_bout_de_l_avant_bras_mm'] = X_AXE
    r['visserie'] = ['2 vis M3 × 30 (manchon, sur l\'avant-bras)', '8 vis M2,5 du servo (4 par disque)', '2 vis M3 × 30 + 2 inserts M3 (bout de la fourche)', '2 vis M3 × 10 + 2 inserts M3 (bride)']
    R_IMPR = [[1, 0, 0], [0, 0, 1], [0, 1, 0]]                           # Y devient la verticale : socle du berceau sur le plateau
    for nom, m, dy in (('flexion_support', SUPPORT, -Y_SOCLE), ('flexion_fourche_basse', BASSE, -Y_BAS), ('flexion_fourche_haute', HAUTE.mirror((0, 1, 0)), -Y_BAS)):
        mesh(placer(m.translate((0, dy, 0)), R_IMPR, (0, 0, 0))).export(OUT / f'{nom}.stl'); r.setdefault('stl', []).append(f'{nom}.stl')
    r['stl'].append('bride : epaule/sortie/bride_berceau.stl (la même qu\'au coude)')
    json.dump(r, open(OUT / 'verification_flexion.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False, indent=1))
