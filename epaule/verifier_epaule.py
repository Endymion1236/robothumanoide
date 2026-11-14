"""Contrôles de l'épaule V1 : rien ne se touche sur toute la course, le ressort passe partout, les trous sont en face.
Lancer : python verifier_epaule.py (après generer_epaule.py). Sort en erreur si un contrôle échoue."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh as tm, manifold3d as mf
import generer_epaule as E

E.PINCE = E.pince_ouverte()
JEU_MIN = 1.0                   # mm de place exigée entre ce qui bouge et ce qui est fixe
def gest(m):
    c = tm.collision.CollisionManager(); c.add_object('p', E.mesh(m)); return c
def dist(a, b): return float(a.min_distance_other(b))
erreurs = []
rapport = {}
fixes = {'bâti': E.BATI, 'berceau de l\'épaule': E.BERCEAU_E, 'bride de l\'épaule': E.BRIDE_E, 'servo de l\'épaule': E.SERVO_E}
gf = {n: gest(m) for n, m in fixes.items()}

# 1. ce qui est fixe ne se traverse pas
for a, b in (('bâti', 'berceau de l\'épaule'), ('bâti', 'servo de l\'épaule'), ('bâti', 'bride de l\'épaule')):
    v = (fixes[a] ^ fixes[b]).volume()
    if v > 0.01: erreurs.append(f'{a} traverse {b} : {v:.1f} mm3')

# 2. le haut du bras (avec le berceau et le servo du coude) sur toute la course de l'épaule
VOULU = {('bras bas', 'servo de l\'épaule'), ('bras haut', 'servo de l\'épaule')}          # vissés sur les deux disques du servo (même montage qu'au coude, validé)
pire = {}
for alpha in np.arange(E.ALPHA_MIN, E.ALPHA_MAX + 0.1, 5):
    p = E.bras_complet(alpha, 0, avec_pince=False); p.pop('avant-bras et pince')
    for n, m in p.items():
        g = gest(m)
        for nf, mfix in fixes.items():
            d = dist(g, gf[nf]) if (m ^ mfix).volume() < 0.01 else -1.0
            if (n, nf) not in pire or d < pire[(n, nf)][0]: pire[(n, nf)] = (round(d, 2), float(alpha))
rapport['jeu_mini_haut_du_bras_mm'] = {f'{a} / {b}': {'jeu': d, 'a_l_angle': al} for (a, b), (d, al) in sorted(pire.items(), key=lambda kv: kv[1][0]) if d < 8}
for (a, b), (d, al) in pire.items():
    if (a, b) not in VOULU and d < JEU_MIN: erreurs.append(f'{a} / {b} : {d} mm à {al}°')

# 3. avant-bras + pince grande ouverte : où peuvent-ils aller sans toucher le bâti, la table, ni le haut du bras ?
table = E.box(-400, -300, -E.H_AXE - E.EP_PIED - 50, 500, 400, -E.H_AXE - E.EP_PIED)
carte = {}
gammas = list(range(-90, 91, 15)); alphas = list(range(int(E.ALPHA_MIN), int(E.ALPHA_MAX) + 1, 15))
for alpha in alphas:
    for gamma in gammas:
        p = E.bras_complet(alpha, gamma); av = p.pop('avant-bras et pince'); touche = []
        for nf, mfix in list(fixes.items()) + [('table', table)]:
            if (av ^ mfix).volume() > 0.5: touche.append(nf)
        for n, m in p.items():
            if n in ('berceau du coude', 'servo du coude', 'bride du coude'): continue      # l'avant-bras tourne autour : contrôlé au coude
            if (av ^ m).volume() > 0.5: touche.append(n)
        for n in ('bras haut', 'berceau du coude'):
            if (p[n] ^ table).volume() > 0.5: touche.append(f'{n} dans la table')
        carte[(alpha, gamma)] = touche
rapport['positions_interdites'] = {f'épaule {a}°, coude {g}°': t for (a, g), t in carte.items() if t}
print('Épaule (lignes) et coude (colonnes), pince grande ouverte : . = libre, T = touche la table, X = touche le bâti ou le bras')
print('        ' + ''.join(f'{g:>5}' for g in gammas))
def signe(t): return '.' if not t else ('T' if all('table' in x for x in t) else 'X')
for a in alphas: print(f'{a:>6}° ' + ''.join(f"{signe(carte[(a, g)]):>5}" for g in gammas))
rapport['contacts_avec_le_bati_ou_le_bras'] = {k: t for k, t in rapport['positions_interdites'].items() if not all('table' in x for x in t)}
if rapport['contacts_avec_le_bati_ou_le_bras']: erreurs.append(f"l'avant-bras ou la pince touche le bâti ou le bras : {rapport['contacts_avec_le_bati_ou_le_bras']}")

# 4. le ressort : tendu entre chaque trou et la vis du bras, il ne doit rien toucher
tout_fixe = E.BATI + E.BERCEAU_E + E.BRIDE_E + E.SERVO_E
pb, lmin, lmax = [], 1e9, 0
for trou in E.TROUS_RESSORT:
    for alpha in np.arange(E.ALPHA_MIN, E.ALPHA_MAX + 0.1, 10):
        r, l = E.ressort(alpha, trou); lmin, lmax = min(lmin, l), max(lmax, l)
        p = E.bras_complet(alpha, 0, avec_pince=False)
        v = (r ^ tout_fixe).volume() + sum((r ^ m).volume() for m in p.values())
        if v > 0.5: pb.append((trou, float(alpha), round(v, 1)))
rapport['ressort'] = {'longueur_entre_vis_mm': [round(lmin), round(lmax)], 'contacts': pb}
if pb: erreurs.append(f'le ressort touche quelque chose : {pb[:4]}')

# 5. les trous sont en face : une tige de 2,4 mm passe à travers les pièces assemblées
def tige(x, z, y0, y1): return E.cyl_y(x, z, y0, y1, 2.4, 16)
bras = E.BRAS_BAS + E.BRAS_HAUT
tiges = {'berceau sur le mur': [(tige(x, z, -E.EP_MUR - 1, E.B.base_T + 1), E.BATI + E.BERCEAU_E) for x, z in E.TROUS_MUR],
         'berceau du coude sur la platine': [(tige(x, z, E.Y_PL_HAUT - 1, E.Y_FACE + E.B.base_T + 1), bras + E.BERCEAU_COUDE) for x, z in E.TROUS_PLATINE],
         'vis des entretoises': [(tige(x + l / 2, s * E.VIS_ENT_Z, E.Y_FOURCHE + E.F.plaque_T + E.F.demi_H - E.F.insert_P + 0.5, E.Y_FACE + 1), bras)
                                 for x, l in ((E.ENT_A, E.ENT_A_L), (E.ENT_B, E.ENT_B_L)) for s in (1, -1)],
         'vis des disques du servo': [(tige(sx * E.F.trou_d, sz * E.F.trou_d, E.Y_FOURCHE - 1, E.Y_FACE + 1), bras) for sx in (1, -1) for sz in (1, -1)],
         'trous du ressort dans le mât': [(tige(x, z, E.Y_MAT - 1, E.Y_MAT + E.EP_MUR + 1), E.BATI) for x, z in E.TROUS_RESSORT]}
rapport['trous_en_face'] = {}
for nom, liste in tiges.items():
    v = max((t ^ m).volume() for t, m in liste); rapport['trous_en_face'][nom] = v < 0.01
    if v >= 0.01: erreurs.append(f'trous pas en face : {nom} ({v:.2f} mm3)')
# la tige doit bien rencontrer de la matière juste à côté (preuve que le contrôle regarde au bon endroit)
assert (tige(E.TROUS_MUR[0][0] + 5, E.TROUS_MUR[0][1], -E.EP_MUR - 1, E.B.base_T + 1) ^ (E.BATI + E.BERCEAU_E)).volume() > 10

# 5 bis. les 4 trous du pied débouchent vraiment (un tournevis passe au-dessus, rien au-dessus du trou)
for x, y in ((-84, -15), (-84, E.Y_MAT + E.EP_MUR), (22, -15), (22, E.Y_MAT + E.EP_MUR)):
    passage = mf.Manifold.cylinder(60, 3.5, 3.5, 24).translate((x, y, -E.H_AXE + 0.05))            # la tête de vis et le tournevis, au-dessus du pied
    passage += mf.Manifold.cylinder(E.EP_PIED + 2, 2.0, 2.0, 24).translate((x, y, -E.H_AXE - E.EP_PIED - 1))   # la vis, à travers le pied
    if (passage ^ E.BATI).volume() > 0.01: erreurs.append(f'trou du pied bouché ou sous un mur : ({x}, {y})')

# 6. longueurs de vis
prise_m3x30 = (E.Y_FACE - 3.0 - 30) ; dessus_bloc_bas = E.Y_FOURCHE + E.F.plaque_T + E.F.demi_H
rapport['vis'] = {'M3x30 des entretoises : prise dans l\'insert (mm)': round(dessus_bloc_bas - prise_m3x30, 2), 'fond du trou d\'insert sous la pointe (mm)': round(prise_m3x30 - (dessus_bloc_bas - E.F.insert_P), 2),
                  'M3x10 du berceau sur le mur : prise dans le socle (mm)': round(10 - E.EP_MUR, 1), 'M3x10 du berceau du coude : prise dans le socle (mm)': round(10 - (E.EP_HAUT - 1.2), 1)}
if not 5 <= dessus_bloc_bas - prise_m3x30 <= E.F.insert_P - 0.5: erreurs.append('vis M3x30 : mauvaise prise')

rapport['erreurs'] = erreurs
json.dump(rapport, open(E.OUT / 'verification_mouvements.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: rapport[k] for k in ('jeu_mini_haut_du_bras_mm', 'ressort', 'trous_en_face', 'vis')}, ensure_ascii=False, indent=1))
if erreurs:
    print('ÉCHEC :'); [print('  ', e) for e in erreurs]; sys.exit(1)
print('OK : aucun contact imprévu.')
