"""Mesure le jeu (distance la plus courte) entre toutes les pièces, sur toute la course de la pince.
Le contrôle de collision de generer_pince.py dit seulement « ça ne se traverse pas » ; ici on vérifie qu'il
reste de la place : une impression 3D n'est jamais exacte à mieux que 0,2 à 0,3 mm.
Lancer : python verifier_jeux.py   (il faut : pip install python-fcl). Sort en erreur si un jeu est trop faible."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh as tm
import generer_pince as G

JEU_MIN = 0.45            # mm : en dessous, risque de frottement une fois imprimé
# paires qui se touchent ou se frôlent EXPRÈS (appui d'un roulement, dents en prise, rondelle de 0,5 mm entre deux pièces)
VOULU = {('base', 'servo'): 'servo dans son logement', ('bride', 'servo'): 'la bride serre le servo',
         ('base', 'bride'): 'bride vissée sur ses piliers', ('avant-bras', 'base'): 'manchon enfilé sur l\'avant-bras',
         ('engrenage A', 'servo'): 'vissé sur le palonnier', ('base', 'engrenage B'): 'tourne sur son poteau',
         ('base', 'bras libre +Y'): 'tourne sur son poteau', ('base', 'bras libre -Y'): 'tourne sur son poteau',
         ('engrenage A', 'engrenage B'): 'dents en prise',
         ('doigt +Y', 'engrenage A'): 'articulation', ('doigt -Y', 'engrenage B'): 'articulation',
         ('bras libre +Y', 'doigt +Y'): 'articulation', ('bras libre -Y', 'doigt -Y'): 'articulation'}

def gestionnaire(m):
    c = tm.collision.CollisionManager(); c.add_object('p', G.mesh(m)); return c

if __name__ == '__main__':
    fixes = {'base': G.BASE, 'bride': G.BRIDE, 'servo': G.SERVO, 'avant-bras': G.AVB}
    gf = {n: gestionnaire(m) for n, m in fixes.items()}
    pire = {}
    angles = np.linspace(G.TH_FERME, G.TH_OUVERT, 14)
    for th in angles:
        p = G.pose(th); gm = {n: gestionnaire(m) for n, m in p.items()}
        tous = gm | gf; noms = sorted(tous)
        e = round(2 * (G.AY + G.L_BRAS * math.sin(math.radians(th)) - G.E_DOIGT))
        for i, a in enumerate(noms):
            for b in noms[i + 1:]:
                if a in fixes and b in fixes: continue
                d = tous[a].min_distance_other(tous[b])
                if (a, b) not in pire or d < pire[(a, b)][0]: pire[(a, b)] = (round(float(d), 2), e)
    alertes, lignes = [], []
    for (a, b), (d, e) in sorted(pire.items(), key=lambda kv: kv[1][0]):
        voulu = VOULU.get((a, b))
        if not voulu and d < JEU_MIN: alertes.append((a, b, d, e))
        if d < 3: lignes.append({'pieces': f'{a} / {b}', 'jeu_min_mm': d, 'a_ecart_machoires_mm': e, 'voulu': voulu or ''})
    for l in lignes:
        print(f"   {l['pieces']:32s} {l['jeu_min_mm']:5.2f} mm (à {l['a_ecart_machoires_mm']} mm d'écart)  {l['voulu']}")
    print(f'   (les autres paires ont plus de 3 mm de jeu ; {len(pire)} paires mesurées sur {len(angles)} positions)')
    json.dump({'jeu_minimum_exige_mm': JEU_MIN, 'paires_a_moins_de_3_mm': lignes, 'alertes': alertes},
              open(G.OUT / 'verification_jeux.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if alertes:
        for a, b, d, e in alertes: print(f'JEU TROP FAIBLE : {a} / {b} : {d} mm à {e} mm d\'écart')
        sys.exit(1)
    print(f'OK : aucune paire imprévue à moins de {JEU_MIN} mm.')
