"""Le doigt peut-il se retourner ? (le défaut de la V2, vu à l'essai du 14/11/2026)

Chaque doigt est tenu droit par deux bras parallèles : le bras de l'engrenage et le bras libre. Pour un
angle donné, le doigt a en réalité DEUX positions possibles : la bonne (parallèle) et une mauvaise
(retourné). Il ne peut passer de l'une à l'autre qu'au « point mort », là où les deux bras s'alignent
avec le doigt. Ce programme vérifie que le point mort est loin de toute la course, butées dépassées comprises,
et il refait le même calcul sur la V2 pour prouver qu'il aurait détecté le défaut.
Lancer : python verifier_cinematique.py   (sort en erreur si la pince n'est pas sûre)"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import generer_pince as G

DEPASSEMENT = 15.0        # degrés au-delà de chaque butée : butées mal réglées, étalonnage décalé, dents sautées
LEVIER_MIN = 12.0         # mm : en dessous, le doigt est mal tenu (la V2 tombait à 0)
JEU_ARTICULATION = 0.3    # mm de jeu supposé dans une articulation imprimée
FORCE_SERRAGE = 20.0      # N au milieu de la mâchoire (ordre de grandeur, servo limité à 35 %)

def ecart_machoires(th): return 2 * (G.AY + G.L_BRAS * math.sin(math.radians(th)) - G.E_DOIGT)

def etude(nom, g):
    th0, th1 = G.TH_FERME, G.TH_OUVERT
    course = np.linspace(th0, th1, 400); large = np.linspace(th0 - DEPASSEMENT, th1 + DEPASSEMENT, 800)
    levier = [G.bras_de_levier(t, g) for t in course]
    levier_large = [G.bras_de_levier(t, g) for t in large]
    ecart = [G.deux_montages(t, g)[2] for t in large]
    # points morts : angles où le bras de levier s'annule (sur un tour complet)
    tour = np.linspace(-180, 180, 36001); f = [g[0] * math.sin(math.radians(t)) - g[1] * math.cos(math.radians(t)) for t in tour]
    morts = sorted({round(float(tour[i]), 1) for i in range(len(tour) - 1) if f[i] == 0 or f[i] * f[i + 1] < 0})
    marge = min(min(abs(m - th0), abs(m - th1)) if not th0 <= m <= th1 else 0.0 for m in morts)
    i_min = int(np.argmin(levier))
    bras_machoire = G.PAD_DEVANT + G.PAD_LONG / 2                      # du trou avant du doigt au milieu de la mâchoire
    r = {'pince': nom,
         'points_morts_deg': morts,
         'point_mort_dans_la_course': any(th0 <= m <= th1 for m in morts),
         'marge_avant_point_mort_deg': round(marge, 1),
         'levier_min_mm': round(min(levier), 1), 'levier_min_a_ecart_mm': round(ecart_machoires(course[i_min])),
         'levier_min_avec_depassement_mm': round(min(levier_large), 1),
         'ecart_min_entre_bon_et_mauvais_montage_mm': round(min(ecart), 1),
         'par_objet': []}
    for d in (14, 30, 55, 80, 110):
        th = math.degrees(math.asin((d / 2 + G.E_DOIGT - G.AY) / G.L_BRAS)); lv = G.bras_de_levier(th, g)
        r['par_objet'].append({'ecart_machoires_mm': d, 'levier_mm': round(lv, 1),
                               'jeu_du_doigt_deg': round(math.degrees(math.atan2(JEU_ARTICULATION, lv)), 1) if lv > 0.05 else 'libre',
                               'effort_dans_le_bras_libre_N': round(FORCE_SERRAGE * bras_machoire / lv) if lv > 0.5 else 'infini'})
    r['sur'] = (not r['point_mort_dans_la_course']) and r['marge_avant_point_mort_deg'] >= DEPASSEMENT and r['levier_min_mm'] >= LEVIER_MIN
    return r

if __name__ == '__main__':
    v3 = etude('V3', (G.GX, G.GY)); v2 = etude('V2 (pivot 24 mm derrière)', (-24.0, 0.0))
    # butée mécanique : les bouts des mâchoires se touchent avant le point mort
    th_contact = math.degrees(math.asin((G.PAD_FLECHE + G.E_DOIGT - G.AY) / G.L_BRAS))
    v3['machoires_en_contact_a_deg'] = round(th_contact, 1)
    v3['point_mort_cote_ferme_deg'] = min(v3['points_morts_deg'], key=lambda m: abs(m - G.TH_FERME))
    # si un doigt se retournait quand même : de combien tournerait-il, pince ouverte ?
    v2['doigt_retourne_pince_ouverte_deg'] = round(abs(G.angle_doigt(G.TH_OUVERT, mauvaise=True, g=(-24.0, 0.0))))
    for r in (v2, v3):
        print(f"\n{r['pince']} : {'SÛRE' if r['sur'] else 'DÉFAUT'}")
        print(f"   points morts à {r['points_morts_deg']}° ; course de {G.TH_FERME:.1f}° à {G.TH_OUVERT:.1f}°"
              f" ; marge {r['marge_avant_point_mort_deg']}°")
        print(f"   bras de levier qui tient le doigt : au pire {r['levier_min_mm']} mm (à {r['levier_min_a_ecart_mm']} mm d'écart)")
        print('   écart mâchoires → bras de levier, jeu du doigt, effort dans le bras libre :')
        for o in r['par_objet']:
            print(f"      {o['ecart_machoires_mm']:>4} mm → {o['levier_mm']:>5} mm, {o['jeu_du_doigt_deg']}°, {o['effort_dans_le_bras_libre_N']} N")
    print(f"\nV2, doigt retourné, pince ouverte : il tourne de {v2['doigt_retourne_pince_ouverte_deg']}° (ce qu'on voit sur la photo du 14/11/2026)")
    print(f"V3 : les mâchoires se touchent à {v3['machoires_en_contact_a_deg']}°, le point mort est à {v3['point_mort_cote_ferme_deg']}° : inatteignable")
    json.dump({'V3': v3, 'V2_pour_comparaison': v2}, open(G.OUT / 'verification_cinematique.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    assert not v2['sur'], 'le test ne détecte pas le défaut de la V2 : test à revoir'
    if not v3['sur']: sys.exit('La pince n\'est pas sûre : point mort trop près de la course.')
    print('\nOK : le test détecte le défaut de la V2, et la V3 passe.')
