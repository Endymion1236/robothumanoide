"""Vérifie que vis, écrous et rondelles ne touchent aucune pièce sur toute la course de la pince
(compare avec l'ancienne visserie : écrou sous le doigt). Lancer après generer_pince.py."""
import sys, math, numpy as np
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generer_pince as G
L_Q2 = 8          # vis du bout des bras libres : M3 x 8 (ou M3 x 10 avec 2 rondelles sous la tête)
cyl = G.cyl
def tete(x, y, z): return cyl(x, y, z, z + 3, 5.5, 24)          # tête de vis CHC M3, posée en z
def tige(x, y, z0, z1): return cyl(x, y, z0, z1, 2.6, 16)        # tige (un peu fine : pas de faux contact dans les trous)
def ecrou(x, y, z1): return cyl(x, y, z1 - 4, z1, 6.4, 24)       # écrou frein (rond de 6,4, prudent)
def rondelle(x, y, z0): return cyl(x, y, z0 + 0.03, z0 + 0.47, 7, 24)
def visserie(th, ancien=False):
    c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
    v = {}
    for k in (1, -1):
        q1 = (G.AX + G.L_BRAS * c, k * (G.AY + G.L_BRAS * s)); q2 = (q1[0] - G.DECAL, q1[1]); piv = G.P_LIBRE[0 if k > 0 else 1]
        zd = G.Z_DOIGT
        v[f'q1 tête {k}'] = tete(*q1, zd + 4); v[f'q1 tige {k}'] = tige(*q1, zd + 4 - 16, zd + 4)
        v[f'q1 rondelle {k}'] = rondelle(*q1, G.Z0 + G.EP_ENG); v[f'q1 écrou {k}'] = ecrou(*q1, G.Z0)
        zl = G.Z_LIBRE + G.EP_LIBRE
        v[f'q2 tête {k}'] = tete(*q2, zl)
        if ancien:   # V2 d'avant : vis M3x12 + écrou frein sous le doigt
            v[f'q2 tige {k}'] = tige(*q2, zl - 12, zl); v[f'q2 écrou {k}'] = ecrou(*q2, zd)
        else:
            v[f'q2 tige {k}'] = tige(*q2, zl - L_Q2 - 0.3, zl)   # +0,3 : tolérance des vis
        v[f'q2 rondelle {k}'] = rondelle(*q2, G.Z_LIBRE - 0.5)
        v[f'pivot tête {k}'] = tete(*piv, G.Z_LIBRE + 4); v[f'pivot tige {k}'] = tige(*piv, G.Z_LIBRE + 4 - 10, G.Z_LIBRE + 4)
    v['B tête'] = tete(G.AX, -G.AY, G.Z0 + 4); v['B tige'] = tige(G.AX, -G.AY, G.Z0 + 4 - 10, G.Z0 + 4)
    for k, y in enumerate((G.SY0 - G.JEU - 3 - 4, G.SY1 + G.JEU + 3 + 4)):
        v[f'bride tête {k}'] = tete(G.BRIDE_X0 + 5, y, G.H_HAUT + 4); v[f'bride tige {k}'] = tige(G.BRIDE_X0 + 5, y, G.H_HAUT + 4 - 10, G.H_HAUT + 4)
    return v
# pièces que chaque vis traverse ou serre normalement (contact voulu, pas une collision)
def permis(nom_vis, piece):
    j, k = nom_vis.split()[0], nom_vis.split()[-1]
    cote = '+Y' if k == '1' else '-Y'
    if j == 'q1': return piece in (f'doigt {cote}', 'engrenage A' if cote == '+Y' else 'engrenage B') and 'tête' not in nom_vis or (piece == f'doigt {cote}' and 'tête' in nom_vis)
    if j == 'q2': return piece in (f'bras libre {cote}', f'doigt {cote}')
    if j == 'pivot': return piece in (f'bras libre {cote}', 'bride' if cote == '+Y' else 'base')
    if j == 'B': return piece in ('engrenage B', 'base')
    if j == 'bride': return piece in ('bride', 'base')
    return False
for ancien in (True, False):
    pires = {}
    for th in np.linspace(G.TH_FERME, G.TH_OUVERT, 30):
        p = G.pose(th); p.update({'base': G.BASE, 'bride': G.BRIDE, 'servo': G.SERVO})
        for nv, mv in visserie(th, ancien).items():
            for np_, mp in p.items():
                if permis(nv, np_): continue
                vol = (mv ^ mp).volume()
                if vol > 0.05:
                    e = 2 * (G.AY + G.L_BRAS * math.sin(math.radians(th)) - G.E_DOIGT)
                    key = (nv, np_); pires.setdefault(key, []).append((round(e), round(vol, 1)))
    print('ANCIENNE visserie' if ancien else 'NOUVELLE visserie', '->', 'aucune collision' if not pires else '')
    for (nv, np_), l in pires.items(): print(f'   {nv} touche {np_} : écart mâchoires {l[0][0]}→{l[-1][0]} mm, jusqu\'à {max(x[1] for x in l)} mm3')
print('marge entre la pointe de la vis du bout du bras libre et le bras de l\'engrenage :', round(G.Z_LIBRE + G.EP_LIBRE - L_Q2 - (G.Z0 + G.EP_ENG), 2), 'mm')
