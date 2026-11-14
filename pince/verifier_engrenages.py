"""Mesure la place entre les dents des deux engrenages, sur un pas de dent complet.
En V2, le fond de dent était en V : la tête de la dent d'en face passait à 0,03 mm du fond. Une fois imprimé,
ça frotte et ça pousse les engrenages à s'écarter. Lancer : python verifier_engrenages.py (il faut python-fcl)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh as tm
import generer_pince as G

JEU_MIN = 0.2             # mm de place qu'il faut garder entre les dents, engrenages bien centrés
DECALAGE_TOLERE = 0.5     # degrés : l'engrenage B peut être en avance ou en retard d'autant sans que les dents se touchent

def distance(prof, th, decalage=0.0):
    a = G.extruder(prof, 0, 2).translate((G.AX, G.AY, 0)); pb = [(x, -y) for x, y in reversed(prof)]
    b = G.extruder(pb, 0, 2).rotate((0, 0, 180 / G.DENTS)).translate((G.AX, -G.AY, 0))
    ma, mb = G.tourner(a, G.AX, G.AY, th), G.tourner(b, G.AX, -G.AY, -th + decalage)
    if (ma ^ mb).volume() > 1e-6: return -1.0
    ca = tm.collision.CollisionManager(); ca.add_object('a', G.mesh(ma)); cb = tm.collision.CollisionManager(); cb.add_object('b', G.mesh(mb))
    return float(ca.min_distance_other(cb))

if __name__ == '__main__':
    prof = G.profil_engrenage(); pas = 360 / G.DENTS
    angles = np.linspace(0, pas, 60, endpoint=False)
    centre = min(distance(prof, t) for t in angles)
    decale = min(distance(prof, t, d) for t in angles for d in (DECALAGE_TOLERE, -DECALAGE_TOLERE))
    r = {'place_entre_les_dents_mm': round(centre, 2), f'avec_B_decale_de_{DECALAGE_TOLERE}_deg_mm': round(decale, 2),
         'jeu_au_bout_du_bras_mm': round(float(2 * centre / (G.R_PRIM * np.cos(np.radians(20))) * G.L_BRAS), 1)}
    print(r)
    json.dump(r, open(G.OUT / 'verification_engrenages.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if centre < JEU_MIN or decale <= 0: sys.exit('Dents trop serrées.')
    print(f'OK : au moins {centre:.2f} mm entre les dents sur tout le pas.')
