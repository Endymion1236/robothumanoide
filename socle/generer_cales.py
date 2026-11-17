"""Cales du plan de travail surélevé : le DESSUS DE LA PLANCHE doit être à 78 mm de la table (hauteur du socle).
Hauteur d'une cale = 78 - épaisseur de la planche. 4 cales par planche, une à chaque coin.
Chaque cale : pied carré de 40 mm à coins arrondis, vis à bois Ø 4 par-dessous (puits Ø 9 pour le tournevis,
la vis traverse les 10 derniers mm et entre dans la planche). S'imprime debout, sans support.
Lancer : python generer_cales.py → sortie/cale_planche_XXmm.stl"""
import json
from pathlib import Path
import numpy as np, manifold3d as mf, trimesh as tm
import generer_socle as S
HAUTEUR_PLAN = S.Z_PLATEAU + S.EP_PLATEAU          # 78 mm : dessus du plateau tournant
PLANCHES = (5, 10, 12, 15, 18)                      # épaisseurs de planche courantes (mm)
COTE, RAYON, TETE, VIS, SOUS_TETE = 40.0, 6.0, 9.0, 4.5, 10.0

def cale(h):
    m = S.arrondi(-COTE / 2, -COTE / 2, COTE / 2, COTE / 2, RAYON, 0, h)
    m -= S.cyl(0, 0, -0.1, h - SOUS_TETE, TETE, 48)             # puits : passage de la tête de vis et du tournevis
    m -= S.cyl(0, 0, h - SOUS_TETE - 0.1, h + 0.1, VIS, 32)     # la vis traverse le dessus
    return m

if __name__ == '__main__':
    r = {'dessus_de_la_planche_mm': HAUTEUR_PLAN, 'cales': {}}
    for ep in PLANCHES:
        h = HAUTEUR_PLAN - ep; t = S.mesh(cale(h)); assert t.is_watertight
        t.export(S.OUT / f'cale_planche_{ep}mm.stl')
        r['cales'][f'planche de {ep} mm'] = {'hauteur_cale_mm': h, 'fichier': f'cale_planche_{ep}mm.stl', 'vis_a_bois': f'4 x {int(SOUS_TETE + min(ep - 2, 15))} au plus',
                                            'masse_g_environ_a_15_pourcent': round(t.volume / 1000 * 1.27 * 0.35)}
    json.dump(r, open(S.OUT / 'cales.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False, indent=1))
