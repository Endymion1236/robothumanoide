"""Charge sur l'épaule, le coude et le poignet si on ajoute la rotation et/ou la flexion du poignet.
Reprend le modèle de calcul_ressort.py (pesée du 14/11/2026) et le ressort 70 x 10 x 1,2 (0,66 N/mm).
Les masses et longueurs des modules de poignet sont des ESTIMATIONS (rien n'est dessiné) :
  rotation : servo 55 g + support et platine 30 g, allonge le bras de 50 mm ;
  flexion  : servo 55 g + étrier 40 g, allonge le bras de 45 mm (placée avant la rotation, comme sur le SO-101).
Lancer : python calcul_poignet.py  → sortie/calcul_poignet.json"""
import json
import calcul_ressort as R

RESSORT = {'raideur': 0.66, 'force_max': 61.0, 'tension_initiale': 0.08 * 61.0}; L_RESSORT = 70.0
AVB, PINCE, D_PINCE, D_GOB = (52, 62), 205, 161.0, 230.0        # distances depuis l'axe du coude (mm)
ROT, D_ROT, L_ROT = 85, 148.0, 50.0                              # module de rotation : masse, centre, allongement
FLEX, D_FLEX, L_FLEX, AXE_FLEX = 95, 150.0, 45.0, 145.0          # module de flexion ; son axe est à 145 du coude
CONFIGS = {'aujourd\'hui (sans poignet)': (False, False), 'avec la rotation': (True, False),
           'avec la flexion': (False, True), 'avec rotation + flexion': (True, True)}
CHARGES = {'pince vide': 0, 'objet léger (100 g)': 100, 'gobelet plein (300 g)': 300}

def modele(rot, flex):
    dec = (L_ROT if rot else 0) + (L_FLEX if flex else 0)
    m = {'avant-bras': AVB, 'pince': (PINCE, D_PINCE + dec)}
    if flex: m['flexion'] = (FLEX, D_FLEX)
    if rot: m['rotation'] = (ROT, D_ROT + (L_FLEX if flex else 0))
    return m, D_GOB + dec

resultat = {}
for nom, (rot, flex) in CONFIGS.items():
    mob, dg = modele(rot, flex)
    R.MOBILES, R.D_GOBELET, R.CHARGES = mob, dg, CHARGES
    sans = R.etude({'tension_initiale': 0, 'raideur': 0, 'force_max': 1}, 1e9, R.TROUS[0])
    avec = R.meilleur_trou(RESSORT, L_RESSORT)
    pire = lambda e, c: max(abs(v) for l in e['detail'] for k, v in l.items() if k.startswith(c))
    ligne = {'longueur épaule → milieu des mâchoires (mm)': round(R.L_BRAS + dg), 'masse ajoutée au bout (g)': (ROT if rot else 0) + (FLEX if flex else 0),
             'trou du ressort': avec['trou'], 'épaule': {}, 'coude': {}, 'flexion du poignet': {}}
    for c, g in CHARGES.items():
        ligne['épaule'][c] = {'sans ressort': round(pire(sans, c), 1), 'avec ressort': round(pire(avec, c), 1)}
        ligne['coude'][c] = round((sum(m * d for m, d in mob.values()) + g * dg) / 1000 * R.G / R.KGCM, 1)
        if flex:
            au_dela = [(PINCE, mob['pince'][1])] + ([mob['rotation']] if rot else [])
            ligne['flexion du poignet'][c] = round((sum(m * (d - AXE_FLEX) for m, d in au_dela) + g * (dg - AXE_FLEX)) / 1000 * R.G / R.KGCM, 1)
    resultat[nom] = ligne
json.dump(resultat, open(R.OUT / 'calcul_poignet.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f"{'':28}{'long.':>6} | épaule sans / AVEC ressort (vide, 100 g, 300 g) | coude (vide, 100, 300) | flexion (vide, 100, 300)")
for nom, l in resultat.items():
    ep = '  '.join(f"{v['sans ressort']:>4}/{v['avec ressort']:<4}" for v in l['épaule'].values())
    co = ' '.join(f'{v:>5}' for v in l['coude'].values()); fl = ' '.join(f'{v:>5}' for v in l['flexion du poignet'].values()) or '   —'
    print(f"{nom:28}{l['longueur épaule → milieu des mâchoires (mm)']:>6} | {ep} | {co} | {fl}")
print('Repères : le STS3215 tient environ 10 kg·cm en continu (estimation), 30 en blocage.')
