"""Pince V4 — SANS ENGRENAGES (19/11/2026). Prototype : aucune validation physique.

Une mâchoire FIXE et une mâchoire MOBILE vissée directement sur le palonnier du servo (principe du SO-101).
On GARDE de la V3 : la base, la bride, le servo et les deux mâchoires (avec leurs inserts). Deux pièces nouvelles :
  - plaque MOBILE : remplace l'engrenage A, son bras et la plaque du doigt +Y ;
  - plaque FIXE  : vissée sur le poteau de l'ancien engrenage B et sur le poteau du bras libre −Y ; porte l'autre mâchoire.
Plus d'engrenage B, de bras libres, de roulements 623, de chapeaux ni de bouchons.

Les mâchoires sont PARALLÈLES pour un objet de 72 mm (gobelet de 70, téléphone de 80 : moins de 8° d'écart) ; plus
petit, les bouts se rapprochent en premier (prise en pincette) ; plus grand, elles s'ouvrent un peu en V.
Tapis antidérapant de 2 mm compté sur chaque mâchoire. L'objet de 72 mm est centré sur l'axe de l'avant-bras.
Lancer : python generer_pince_v4.py → sortie/pince_v4_*.stl, sortie/verification_pince_v4.json"""
import math, json
import numpy as np, manifold3d as mf, trimesh as tm
import generer_pince as G
from generer_pince import box, cyl, extruder, barre, mesh, AX, AY, Z0, Z_DOIGT, Z_LIBRE, EP_RONDELLE, M3, M2_5, PAD_LONG, PAD_EP, PAD_BAS, PAD_R, PAD_FLECHE, VIS_MACH_U, CERCLE_TROUS

TAPIS = 2.0                         # tapis antidérapant collé sur chaque mâchoire (mesuré : 2 mm)
W_PARALLELE = 72.0                  # largeur d'objet pour laquelle les deux mâchoires sont parallèles
W_MAX = 90.0                        # plus gros objet
XC = 117.0                          # milieu des mâchoires, depuis le fond du manchon (comme la V3)
YF = -(W_PARALLELE / 2 + TAPIS)     # face (creux) de la mâchoire fixe : -38
YM = +(W_PARALLELE / 2 + TAPIS)     # face (creux) de la mâchoire mobile, mâchoires parallèles : +38
VIS_PALONNIER = 5.3                 # vis M2,5 fournies avec le servo, sous tête (mesuré)
SOUS_TETE = VIS_PALONNIER - 2.5     # 2,8 mm de plastique sous la tête → 2,5 mm de prise dans le palonnier
ZT = Z_DOIGT + G.EP_COUVRE          # dessus de la plaque mobile (46,6)
ZF0 = Z_LIBRE - EP_RONDELLE         # dessous de la plaque fixe = dessus du poteau du bras libre (44,6)
EP_FIXE = 5.0; ZF1 = ZF0 + EP_FIXE
POT_B, POT_L = (AX, -AY), G.P_LIBRE[1]            # poteaux réutilisés : ancien engrenage B, bras libre −Y
Z_POT_B = Z0 - EP_RONDELLE          # dessus du poteau de B (33,6)
COUDE_X, COUDE_Y = 72.0, 47.0      # coude des deux bras (position parallèle)
INSERT_H = 3.8                      # inserts de Nicolas : Ø 4,7 × 3,8

def machoire(s, yi, xc=XC):
    """La mâchoire de la V3 (pièce déjà imprimée), placée : face creuse à y = yi, côté s (+1 mobile, −1 fixe)."""
    y0, y1 = (yi - PAD_FLECHE, yi + PAD_EP) if s > 0 else (yi - PAD_EP, yi + PAD_FLECHE)
    prof = lambda z0, z1: box(xc - PAD_LONG / 2, y0, z0, xc + PAD_LONG / 2, y1, z1) - cyl(xc, yi - s * PAD_R, z0 - 1, z1 + 1, 2 * PAD_R, 192)
    creux = PAD_R - math.sqrt(PAD_R ** 2 - VIS_MACH_U ** 2)
    vis = [(xc + u, yi + s * (PAD_EP - creux) / 2) for u in (-VIS_MACH_U, VIS_MACH_U)]
    return prof, vis, (y0, y1)

def plaque_mobile():
    """Vissée sur le palonnier (4 vis M2,5 de 5,3 mm, têtes au fond de puits), porte la mâchoire mobile. Dessinée mâchoires parallèles."""
    prof, vis, (y0, y1) = machoire(1, YM)
    m = cyl(AX, AY, Z0, ZT, 26) + cyl(AX, AY, Z0 - 1.0, Z0, 18)                               # moyeu + patin sur le palonnier
    # bras COUDÉ : il part vers l'extérieur puis rejoint l'ARRIÈRE de la mâchoire, pour laisser la place à un verre haut
    # (un bras droit passait au-dessus du verre : un verre plus haut que la pince l'aurait touché)
    coude, bout = (COUDE_X, COUDE_Y), (XC - PAD_LONG / 2 + 3, y1 - 2)
    for p, q in (((AX, AY), coude), (coude, bout)):
        m += extruder(barre(p, q, 16), Z_DOIGT, ZT)
        m += extruder(barre(p, q, 16), Z0, Z_DOIGT) - box(XC - PAD_LONG / 2 - 0.5, y0 - 0.5, Z0 - 1, XC + PAD_LONG / 2 + 0.5, y1 + 30, Z_DOIGT + 1)
    m += prof(Z_DOIGT, ZT)                                                                     # couvercle de la mâchoire
    for k in range(4):
        a = math.radians(45 + 90 * k); x, y = AX + CERCLE_TROUS / 2 * math.cos(a), AY + CERCLE_TROUS / 2 * math.sin(a)
        m -= cyl(x, y, Z0 - 1.1, ZT + 0.1, M2_5, 24); m -= cyl(x, y, Z0 - 1.0 + SOUS_TETE, ZT + 0.1, 5.4, 24)
    m -= cyl(AX, AY, Z0 - 1.1, ZT + 0.1, 7)                                                    # vis centrale du palonnier
    for x, y in vis: m -= cyl(x, y, Z_DOIGT - 0.1, ZT + 0.1, M3, 24)
    return m

def plaque_fixe():
    """Vissée sur deux poteaux de la base (ancien engrenage B, bras libre −Y), porte la mâchoire fixe."""
    prof, vis, (y0, y1) = machoire(-1, YF)
    coude, bout = (COUDE_X, -COUDE_Y), (XC - PAD_LONG / 2 + 3, y0 + 2)
    m = extruder(barre(POT_L, POT_B, 14), ZF0, ZF1) + cyl(*POT_B, Z_POT_B, ZF0, 13) + prof(Z_DOIGT, ZF1)   # pied sur le poteau de B (11 mm) + couvercle de la mâchoire
    for p, q in ((POT_B, coude), (coude, bout)): m += extruder(barre(p, q, 16), ZF0, ZF1)                   # bras coudé, comme la plaque mobile
    m += extruder(barre(coude, bout, 16), Z_DOIGT, ZF0) - box(XC - PAD_LONG / 2 - 0.5, y0 - 30, Z0, XC + PAD_LONG / 2 + 0.5, y1 + 0.5, Z_DOIGT)
    # poteau de B : vis M3 × 16, tête noyée de 4 mm → 4 mm dans l'insert ; poteau libre : M3 × 10, 5 mm dans le poteau
    m -= cyl(*POT_B, Z_POT_B - 0.1, ZF1 + 0.1, M3, 24); m -= cyl(*POT_B, ZF1 - 4.0, ZF1 + 0.1, 6.4, 32)
    m -= cyl(*POT_L, ZF0 - 0.1, ZF1 + 0.1, M3, 24)
    for x, y in vis: m -= cyl(x, y, Z_DOIGT - 0.1, ZF1 + 0.1, M3, 24); m -= cyl(x, y, ZF1 - 3.0, ZF1 + 0.1, 6.4, 32)   # M3 × 10 : 4 mm dans l'insert
    return m

PM, PF = plaque_mobile(), plaque_fixe()
_pm, _vm, _ = machoire(1, YM); MACH_M = _pm(PAD_BAS, Z_DOIGT)
_pf, _vf, _ = machoire(-1, YF); MACH_F = _pf(PAD_BAS, Z_DOIGT)
def tapis(s, yi): return (box(XC - PAD_LONG / 2, yi - 10, PAD_BAS, XC + PAD_LONG / 2, yi + 10, Z_DOIGT) ^ cyl(XC, yi - s * PAD_R, PAD_BAS, Z_DOIGT, 2 * PAD_R, 192)) - cyl(XC, yi - s * PAD_R, PAD_BAS - 1, Z_DOIGT + 1, 2 * (PAD_R - TAPIS), 192)
TAPIS_M, TAPIS_F = tapis(1, YM), tapis(-1, YF)
def mobile(delta):
    """Plaque mobile + sa mâchoire + son tapis, tournées de delta degrés (+ = ouvrir) autour de l'axe du servo."""
    return [G.tourner(x, AX, AY, delta) for x in (PM, MACH_M, TAPIS_M)]
FIXES = {'base': G.BASE, 'bride': G.BRIDE, 'servo': G.SERVO, 'plaque fixe': PF, 'mâchoire fixe': MACH_F}

def ouverture(delta):
    """Écart entre les deux TAPIS au milieu des mâchoires (mm), pour un angle delta depuis la position parallèle."""
    r = math.hypot(XC - AX, YM - AY); phi = math.atan2(YM - AY, XC - AX) + math.radians(delta)
    return AY + r * math.sin(phi) - YF - 2 * TAPIS

def angle_contact():
    """Angle où les tapis se touchent (pince fermée à vide) : par dichotomie sur le volume commun."""
    a, b = -60.0, 0.0
    for _ in range(18):
        c = (a + b) / 2; t = mobile(c)[2]
        if (t ^ TAPIS_F).volume() > 0.01 or (mobile(c)[1] ^ MACH_F).volume() > 0.01: a = c
        else: b = c
    return b

if __name__ == '__main__':
    r = {'version': 'pince V4 (sans engrenages)', 'validation_physique': False}
    d_ferme = angle_contact(); d_ouvert = next(d for d in np.arange(0, 60, 0.1) if ouverture(d) >= W_MAX)
    course = d_ouvert - d_ferme; d_milieu = (d_ouvert + d_ferme) / 2
    r['course'] = {'fermée à vide (les bouts des tapis se touchent)': round(d_ferme, 1), 'ouverte à 90 mm': round(float(d_ouvert), 1), 'course totale (°)': round(float(course), 1),
                   'course permise par les butées 1663–2433 (°)': 67.7, 'milieu de course : écart entre les tapis (mm)': round(ouverture(d_milieu), 1),
                   'milieu de course : écart entre les mâchoires SANS tapis (mm)': round(ouverture(d_milieu) + 2 * TAPIS, 1), 'angle du milieu depuis la position parallèle': round(float(d_milieu), 1)}
    assert course < 67.7, course
    r['inclinaison de la mâchoire mobile selon l\'objet (°)'] = {f'{w} mm': round(float(next(d for d in np.arange(-60, 60, 0.1) if ouverture(d) >= w)), 1) for w in (20, 40, 53, 70, 72, 80, 90)}
    # rien ne se touche sur toute la course, butées dépassées de 2°
    pire = {}
    for d in np.linspace(d_ferme + 0.3, d_ouvert + 2, 50):
        for piece in mobile(d)[:2]:
            for nom, f in FIXES.items():
                v = (piece ^ f).volume()
                if v > 0.01: pire[nom] = max(pire.get(nom, 0), round(v, 1))
    r['contacts sur toute la course (mm3)'] = pire or 'aucun'
    for nom, f in (('base', G.BASE), ('bride', G.BRIDE), ('servo', G.SERVO)): assert (PF ^ f).volume() < 0.01, ('plaque fixe', nom, (PF ^ f).volume())
    assert (PF ^ MACH_F).volume() < 0.01 and (PM ^ MACH_M).volume() < 0.01
    assert not pire, pire
    # un verre HAUT (cylindre de 53 à 90 mm, bien plus haut que la pince) ne touche que les tapis et les mâchoires
    jeu_verre = {}
    for w in (53, 60, 72, 80, 90):
        d = float(next(x for x in np.arange(-60, 60, 0.05) if ouverture(x) >= w)); verre = cyl(XC, YF + TAPIS + w / 2, PAD_BAS, 200, w - 0.6, 128)
        v = (verre ^ mobile(d)[0]).volume() + (verre ^ PF).volume() + (verre ^ G.BASE).volume(); jeu_verre[f'{w} mm'] = round(v, 2); assert v < 0.01, (w, v)
    r['verre haut contre les plaques et la base (mm3)'] = jeu_verre
    r['vis'] = {'palonnier : 4 × M2,5 de 5,3 mm (fournies)': f'{SOUS_TETE:.1f} mm de plastique, 2,5 mm dans le palonnier', 'mâchoires : 4 × M3 × 10': '4 mm dans l\'insert',
                'plaque fixe sur le poteau de B : 1 × M3 × 16': '4 mm dans l\'insert', 'plaque fixe sur le poteau du bras libre : 1 × M3 × 10': '5 mm dans le poteau'}
    R180 = tm.transformations.rotation_matrix(math.pi, (1, 0, 0)); masse = {}
    for nom, m in (('pince_v4_plaque_mobile', PM), ('pince_v4_plaque_fixe', PF)):
        t = mesh(m); assert t.is_watertight and len(t.split(only_watertight=False)) == 1, nom
        t.apply_transform(R180); t.apply_translation(-t.bounds[0]); t.export(G.OUT / f'{nom}.stl'); masse[nom] = round(t.volume / 1000 * 1.27 * 0.6)
    r['masse des 2 pièces nouvelles (g, environ)'] = masse
    json.dump(r, open(G.OUT / 'verification_pince_v4.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False, indent=1))
