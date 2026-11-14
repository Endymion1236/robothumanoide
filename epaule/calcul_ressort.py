"""Quel ressort pour l'épaule ? Calcul du couple que le servo d'épaule doit fournir, avec et sans ressort.

Le ressort de traction relie un point FIXE du bâti, au-dessus et en arrière de l'axe de l'épaule (12 trous au
choix sur le mât), à une vis plantée dans le haut du bras, à 56 mm de l'axe. Quand le bras descend, le ressort
s'allonge et le retient : il porte une bonne partie du poids du bras, le servo a moins à fournir.
Le point fixe est en ARRIÈRE de l'axe pour que le ressort reste tendu le plus haut possible ; bras presque
vertical, il est détendu (il pend entre ses deux vis) : normal, le bras ne pèse presque plus sur l'épaule.

Masses : pesée du 14/11/2026 (281 g pour coude + avant-bras + pince sans doigts ni bras libres), d'où une
densité apparente de 0,98 g/cm3 pour les pièces imprimées (40 % de remplissage, 4 périmètres).
Lancer : python calcul_ressort.py   → sortie/calcul_ressort.json et sortie/couple_epaule.png
Pour essayer TON ressort : python calcul_ressort.py --fil 1.0 --diametre 8 --longueur 50
ou, si tu l'as mesuré :     python calcul_ressort.py --longueur 50 --raideur 0.75 --force-max 40"""
import math, json, argparse
from pathlib import Path
OUT = Path(__file__).resolve().parent / 'sortie'; OUT.mkdir(exist_ok=True)
G = 9.81
KGCM = 98.1                     # 1 kg·cm = 98,1 N·mm

# ---------------- Le bras (mm, grammes) ----------------
L_BRAS = 120.0                  # axe d'épaule → axe du coude
B_VIS = 56.0                    # vis d'accroche du ressort sur le bras (au milieu de l'entretoise A)
TROUS = [(x, z) for x in (-46.0, -40.0, -34.0) for z in (32.0, 38.0, 44.0, 50.0)]   # points fixes possibles (x vers l'avant, z vers le haut, depuis l'axe)
ALPHA_MIN, ALPHA_MAX = -30.0, 90.0   # course de l'épaule (0 = bras à l'horizontale vers l'avant)
COUPLE_CONTINU = 10.0           # kg·cm que le STS3215 tient sans chauffer (blocage : 30)
# solidaires du haut du bras (masse, distance à l'axe d'épaule)
FIXES = {'haut du bras (2 demi-fourches + platine)': (85, 75), 'berceau + bride + servo du coude': (93, 105.5)}
# solidaires de l'avant-bras (masse, distance à l'axe du COUDE)
MOBILES = {'avant-bras (fourche)': (52, 62), 'pince V3 complète avec son servo': (205, 161)}
D_GOBELET = 230.0               # milieu des mâchoires → axe du coude
CHARGES = {'pince vide': 0, 'gobelet vide (15 g)': 15, 'gobelet plein (300 g)': 300}

def couple_poids(alpha, gamma, charge):
    """Couple du poids sur l'épaule (N·mm). gamma = angle du coude (0 = avant-bras dans le prolongement)."""
    ca, cg = math.cos(math.radians(alpha)), math.cos(math.radians(alpha + gamma))
    t = sum(m * d for m, d in FIXES.values()) * ca
    t += sum(m * (L_BRAS * ca + d * cg) for m, d in MOBILES.values()) + charge * (L_BRAS * ca + D_GOBELET * cg)
    return t / 1000 * G

# ---------------- Le ressort ----------------
def ressort_calcule(fil, diametre, longueur, acier=79000.0, resistance=None):
    """Ressort de traction à spires jointives, d'après ses cotes : fil, diamètre EXTÉRIEUR, longueur hors tout
    (crochets compris). Renvoie raideur (N/mm), force maxi (N), tension initiale (N)."""
    D = diametre - fil; n = max(3.0, (longueur - 2 * (diametre - 2 * fil)) / fil)     # crochets ≈ un diamètre intérieur chacun
    k = acier * fil ** 4 / (8 * D ** 3 * n)
    C = D / fil; wahl = (4 * C - 1) / (4 * C - 4) + 0.615 / C
    rm = resistance or (2200 - 400 * math.log(fil))           # fil ressort : environ 2200 MPa à 1 mm
    fmax = 0.45 * rm * math.pi * fil ** 3 / (8 * D * wahl)   # 45 % de la résistance : limite usuelle en traction
    return {'raideur': k, 'force_max': fmax, 'tension_initiale': 0.08 * fmax, 'spires': round(n)}

def etude(r, longueur, trou, b=B_VIS):
    """Pour un ressort (raideur, force_max, tension_initiale) de longueur au repos donnée, accroché au trou (x, z)."""
    lignes, pire, f_pire, mou_a = [], 0.0, 0.0, None
    a = math.hypot(*trou); beta = math.degrees(math.atan2(trou[1], trou[0]))
    for alpha in range(int(ALPHA_MIN), int(ALPHA_MAX) + 1, 5):
        phi = math.radians(beta - alpha)
        l = math.sqrt(a * a + b * b - 2 * a * b * math.cos(phi))
        tendu = l > longueur
        f = r['tension_initiale'] + r['raideur'] * (l - longueur) if tendu else 0.0
        t_res = f * a * b * math.sin(phi) / l if l > 1 else 0.0
        if not tendu and mou_a is None: mou_a = alpha
        d = {'angle': alpha, 'longueur_ressort': round(l, 1), 'force_N': round(f, 1), 'ressort_kgcm': round(t_res / KGCM, 1)}
        for nom, charge in CHARGES.items():
            for pose, gamma in (('tendu', 0), ('avant-bras horizontal', -alpha)):
                reste = (couple_poids(alpha, gamma, charge) - t_res) / KGCM
                d[f'{nom} / {pose}'] = round(reste, 1)
                pire = max(pire, abs(reste))
        f_pire = max(f_pire, f); lignes.append(d)
    return {'trou': list(trou), 'effort_servo_max_kgcm': round(pire, 1), 'force_ressort_max_N': round(f_pire, 1),
            'usage_du_ressort_pourcent': round(100 * f_pire / r['force_max']), 'ressort_mou_au_dessus_de_deg': mou_a, 'detail': lignes}

CATALOGUE = [(1.0, 8, 50), (1.0, 10, 50), (1.0, 10, 60), (1.2, 10, 50), (1.2, 10, 60), (1.2, 12, 60), (1.5, 12, 60)]

def meilleur_trou(r, longueur):
    essais = [etude(r, longueur, t) for t in TROUS]
    bons = [e for e in essais if e['usage_du_ressort_pourcent'] <= 80] or essais
    return min(bons, key=lambda e: e['effort_servo_max_kgcm'])

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--fil', type=float); p.add_argument('--diametre', type=float)
    p.add_argument('--longueur', type=float); p.add_argument('--raideur', type=float); p.add_argument('--force-max', type=float)
    o = p.parse_args()
    sans = {'tension_initiale': 0, 'raideur': 0, 'force_max': 1}
    ref = etude(sans, 1e9, TROUS[0])
    print('SANS ressort : effort maxi du servo d\'épaule :', ref['effort_servo_max_kgcm'], 'kg·cm',
          f'(le servo tient {COUPLE_CONTINU:.0f} en continu)')
    print(f'   bras tendu à l\'horizontale : {couple_poids(0, 0, 0) / KGCM:.1f} kg·cm à vide, {couple_poids(0, 0, 300) / KGCM:.1f} avec un gobelet plein')
    if o.longueur and (o.raideur or o.fil):
        r = ({'raideur': o.raideur, 'force_max': o.force_max or 1e9, 'tension_initiale': 0.08 * (o.force_max or 40)} if o.raideur
             else ressort_calcule(o.fil, o.diametre, o.longueur))
        candidats = [(f'ton ressort ({o.longueur:.0f} mm)', r, o.longueur)]
    else:
        candidats = [(f'fil {f} × Ø {d} × {l} mm', ressort_calcule(f, d, l), l) for f, d, l in CATALOGUE]
    resultats = []
    for nom, r, l in candidats:
        e = meilleur_trou(r, l)
        resultats.append({'ressort': nom, 'raideur_N_par_mm': round(r['raideur'], 2), 'force_max_N': round(r['force_max']),
                          'allongement_sous_1_kg_mm': round(G / r['raideur'], 1), **{k: v for k, v in e.items() if k != 'detail'}, 'detail': e['detail']})
    resultats.sort(key=lambda x: (x['usage_du_ressort_pourcent'] > 80, x['effort_servo_max_kgcm']))
    print('\nressort                      raideur  s\'allonge   meilleur     effort maxi   ressort   détendu')
    print('                             N/mm     sous 1 kg    trou (x, z)  du servo      utilisé   au-dessus de')
    for x in resultats:
        print(f"{x['ressort']:28s} {x['raideur_N_par_mm']:5.2f}    {x['allongement_sous_1_kg_mm']:5.1f} mm   ({x['trou'][0]:.0f}, {x['trou'][1]:.0f})    "
              f"{x['effort_servo_max_kgcm']:5.1f} kg·cm   {x['usage_du_ressort_pourcent']:4d} %    {x['ressort_mou_au_dessus_de_deg']}°")
    m = resultats[0]
    print(f"\nAvec « {m['ressort']} » au trou {tuple(m['trou'])} : pince vide, le servo fournit au plus "
          f"{max(abs(d[k]) for d in m['detail'] for k in d if k.startswith('pince vide')):.1f} kg·cm ; avec un gobelet plein de 300 g, "
          f"{m['effort_servo_max_kgcm']} kg·cm (sans ressort : {ref['effort_servo_max_kgcm']}).")
    json.dump({'sans_ressort': {k: v for k, v in ref.items() if k != 'detail'}, 'ressorts': resultats},
              open(OUT / 'calcul_ressort.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # graphique : le meilleur
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    x = resultats[0]; ang = [d['angle'] for d in x['detail']]
    fig, ax = plt.subplots(figsize=(10, 6))
    for nom, coul in (('pince vide', '#2c7fb8'), ('gobelet plein (300 g)', '#d95f0e')):
        ax.plot(ang, [d[f'{nom} / avant-bras horizontal'] for d in ref['detail']], '--', color=coul, label=f'{nom}, sans ressort')
        ax.plot(ang, [d[f'{nom} / avant-bras horizontal'] for d in x['detail']], '-', color=coul, lw=2.5, label=f'{nom}, avec ressort')
    ax.axhspan(-COUPLE_CONTINU, COUPLE_CONTINU, color='#2ca25f', alpha=0.12, label='ce que le servo tient en continu')
    ax.axhline(0, color='#444', lw=0.8); ax.set_xlabel('angle du haut du bras (0° = horizontal, 90° = vertical)'); ax.set_ylabel('effort demandé au servo d\'épaule (kg·cm)')
    ax.set_title(f"Épaule, avant-bras horizontal — ressort {x['ressort']}, trou {tuple(x['trou'])}"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / 'couple_epaule.png', dpi=120)
