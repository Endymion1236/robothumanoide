import sys, math, json; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import generer_pince as G, manifold3d as mf
res = []
for D in (55.0, 80.0, 90.0):
    # les mâchoires se ferment jusqu'au contact : le gobelet touche le creux de l'arc (son rayon < 45)
    th = math.degrees(math.asin((D / 2 + G.E_DOIGT - G.AY) / G.L_BRAS))
    q1x = G.AX + G.L_BRAS * math.cos(math.radians(th))
    xc = q1x + G.PAD_DEVANT + G.PAD_LONG / 2                     # centre de l'arc = centre du gobelet
    p = G.pose(math.degrees(math.asin((D / 2 + 1 + G.E_DOIGT - G.AY) / G.L_BRAS)))   # mâchoires à 1 mm du gobelet
    for zb, zh, ou in ((-40, 70, 'tenu au milieu'), (-70, 40, 'tenu par le haut')):
        gob = mf.Manifold.cylinder(zh - zb, D / 2, D / 2, 128).translate((xc, 0, zb))
        t = {n: round((m ^ gob).volume(), 1) for n, m in ({'base': G.BASE, 'bride': G.BRIDE, 'servo': G.SERVO, 'avant-bras': G.AVB} | p).items()}
        res.append({'diametre': D, 'prise': ou, 'touche': {n: v for n, v in t.items() if v > 0.1},
                    'marge_arriere_mm': round(xc - D / 2 - (G.AX + 16.5), 1)})
    # marge d'approche : mâchoires grandes ouvertes autour du gobelet
    res[-1]['marge_approche_par_cote_mm'] = round((G.ECART_MAX - D) / 2, 1)
for r in res: print(r)
json.dump(res, open(G.OUT / 'test_gobelets.json', 'w'), ensure_ascii=False, indent=1)
