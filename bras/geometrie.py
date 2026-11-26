"""Aller à un point de la table : quels angles donner au socle, à l'épaule, au coude et au poignet pour que la pince,
tenue À L'HORIZONTALE, arrive au-dessus d'un point (X, Y) de la table. Calcul seul, sans servo.

Repère de la table (le même que la caméra) : origine sur l'axe du socle, X vers la droite du robot (vu de derrière), Y vers l'avant.
Le bras ne tourne pas autour de son propre plan : il est DÉCALÉ de 53,5 mm à GAUCHE de l'axe du socle, vu de derrière
(photo de Nicolas du 23/11/2026). Le calcul en tient compte.
Il faut le poignet complet (flexion, servo n° 6) : c'est lui qui garde la pince à plat."""
import math
import piloter_bras as B, test_epaule as E

DECALAGE_BRAS = -53.5          # mm : position du plan du bras par rapport à l'axe du socle, + = à droite vu de derrière
H_PRISE = 62.0                 # hauteur de l'axe de la pince au-dessus de la table pour saisir : le bas des mâchoires est alors, par le
                               # calcul, à 22 mm ; en vrai plus bas, car le bras fléchit (garde de 20 mm, voir MARGE_TABLE)
H_SURVOL = 130.0               # hauteur de l'axe de la pince pour arriver au-dessus d'un objet sans le toucher
EPAULE_MAX = E.REPOS           # au-delà, l'épaule bute contre le ressort

class HorsDePortee(Exception): pass

def angles_plan(s, z, inclinaison=0.0, hauteur_epaule=179.0, coude_en_haut=True):
    """Dans le plan du bras : les angles (épaule, coude, flexion) pour amener le milieu des mâchoires à la distance s devant l'axe de
    l'épaule et à la hauteur z au-dessus de la table, la pince inclinée de `inclinaison` degrés (0 = à plat, −90 = pointée vers le bas)."""
    L1, L2, L3 = B.L_BRAS, B.L_COUDE_FLEXION, B.L_APRES_FLEXION; t = math.radians(inclinaison)
    xw, zw = s - L3 * math.cos(t), z - L3 * math.sin(t) - hauteur_epaule          # l'axe de flexion du poignet, vu depuis l'épaule
    d2 = xw * xw + zw * zw
    c = (d2 - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    if c > 1: raise HorsDePortee('trop loin pour le bras')
    if c < -1 or xw < 20: raise HorsDePortee('trop près du socle')
    g = -math.acos(c) if coude_en_haut else math.acos(c)             # coude « en haut » : le haut du bras monte, l'avant-bras redescend ; « en bas » : l'inverse
    a = math.atan2(zw, xw) - math.atan2(L2 * math.sin(g), L1 + L2 * math.cos(g))
    r = {'epaule': math.degrees(a), 'coude': math.degrees(g), 'flexion': inclinaison - math.degrees(a + g)}
    if not E.BAS <= r['epaule'] <= EPAULE_MAX: raise HorsDePortee(f"épaule à {r['epaule']:+.0f}° : hors de {E.BAS}° à {EPAULE_MAX}° ({'trop loin ou trop bas' if r['epaule'] < E.BAS else 'trop près ou trop haut'})")
    if abs(r['coude']) > B.COUDE_MAX: raise HorsDePortee(f"coude à {r['coude']:+.0f}° : hors de ±{B.COUDE_MAX}° (trop près)")
    if abs(r['flexion']) > B.FLEXION_MAX: raise HorsDePortee(f"poignet à {r['flexion']:+.0f}° : hors de ±{B.FLEXION_MAX}°")
    return r

def au_plus_pres(s, z, inclinaison, hauteur_epaule, glisser, coude_en_haut=True, maxi=150):
    """Si le point (s, z) n'est pas atteignable, cherche le point atteignable le plus proche en glissant le long d'un seul axe
    (`glisser` = 'avance' : on avance ou recule ; 'hauteur' : on monte ou descend). Renvoie (angles, décalage en mm) ou lève HorsDePortee."""
    erreur = None
    for d in [0] + [k * sg for k in range(5, maxi + 1, 5) for sg in (1, -1)]:
        try: return angles_plan(s + (d if glisser == 'avance' else 0), z + (d if glisser == 'hauteur' else 0), inclinaison, hauteur_epaule, coude_en_haut), d
        except HorsDePortee as e: erreur = erreur or e
    raise erreur

def position_plan(epaule, coude, flexion, hauteur_epaule=179.0):
    """L'inverse : (distance devant l'épaule, hauteur au-dessus de la table, inclinaison de la pince) d'après les angles."""
    a, ag, t = math.radians(epaule), math.radians(epaule + coude), math.radians(epaule + coude + flexion)
    return (B.L_BRAS * math.cos(a) + B.L_COUDE_FLEXION * math.cos(ag) + B.L_APRES_FLEXION * math.cos(t),
            hauteur_epaule + B.L_BRAS * math.sin(a) + B.L_COUDE_FLEXION * math.sin(ag) + B.L_APRES_FLEXION * math.sin(t), math.degrees(t))

INCLINAISONS = (0, -15, -30, -45, -60, -75, -90)     # essayées dans cet ordre : la pince la plus à plat possible d'abord
def hauteur_prise(inclinaison=0.0):
    """Hauteur du MILIEU des mâchoires pour saisir, la pince inclinée de `inclinaison` degrés : celle qui laisse le point le plus bas
    de la pince 2 mm au-dessus de la garde de la table (22 mm par le calcul). À plat : 62 mm (H_PRISE). Pointée vers le bas : 57 mm."""
    t = math.radians(inclinaison)
    return B.MARGE_TABLE + 2.0 + B.SOUS_PINCE_DROITE * abs(math.cos(t)) + B.BOUT_MACHOIRES * abs(math.sin(t))

def angles_pour(X, Y, hauteur_axe=None, hauteur_epaule=179.0, inclinaison=0.0):
    """Renvoie {'socle', 'epaule', 'coude', 'flexion'} en degrés, la pince inclinée de `inclinaison` (0 = à l'horizontale, −90 = pointée
    vers le bas), ou lève HorsDePortee avec la raison. hauteur_axe : hauteur du milieu des mâchoires (par défaut, celle de la prise)."""
    if hauteur_axe is None: hauteur_axe = hauteur_prise(inclinaison)
    R = math.hypot(X, Y)
    if R <= abs(DECALAGE_BRAS) + 1: raise HorsDePortee('point trop près du socle')
    s = math.sqrt(R * R - DECALAGE_BRAS ** 2)                       # distance à parcourir dans le plan du bras, depuis l'axe de l'épaule
    socle = math.degrees(math.atan2(X, Y) - math.atan2(DECALAGE_BRAS, s))
    if abs(socle) > B.SOCLE_MAX: raise HorsDePortee(f'il faudrait tourner le socle de {socle:+.0f}° (limite ±{B.SOCLE_MAX}°)')
    try: return dict(angles_plan(s, hauteur_axe, inclinaison, hauteur_epaule), socle=socle)
    except HorsDePortee as e: raise HorsDePortee(f'{e} ({R:.0f} mm du socle)')

def prise_et_approche(X, Y, hauteur_epaule=179.0, inclinaison=0.0):
    """Les deux positions d'un geste de prise, pour une inclinaison donnée : (prise, approche). Lève HorsDePortee si l'une des deux est
    impossible ou si la descente de l'une à l'autre frôlerait la table.
    Pince à plat : l'approche est la position d'avant (épaule relevée de 25°), essayée en vrai le 24/11/2026.
    Pince inclinée : on cherche d'abord une approche À LA VERTICALE du point (7, puis 5,5, puis 4 cm plus haut)."""
    prise = angles_pour(X, Y, None, hauteur_epaule, inclinaison)
    if B.bas_de_pince(hauteur_epaule, prise['epaule'], prise['coude'], prise['flexion'], roulis=0.0) < B.MARGE_TABLE: raise HorsDePortee('la pince toucherait la table')
    # tout près du socle, pince pointée vers le bas, le poignet n'a plus assez de course pour monter à la verticale sans changer
    # d'inclinaison : on accepte alors une approche un peu moins raide (5, 10 puis 15° de moins), toujours au-dessus du point.
    essais = [] if abs(inclinaison) < 1 else [lambda dz=dz, di=di: angles_pour(X, Y, hauteur_prise(inclinaison) + dz, hauteur_epaule, min(0.0, inclinaison + di))
                                              for di in (0.0, 5.0, 10.0, 15.0) for dz in (70.0, 55.0, 40.0)]
    erreur = None
    for essai in essais + [lambda: au_dessus(prise)]:
        try: haut = essai()
        except HorsDePortee as e: erreur = erreur or e; continue
        cles = ('epaule', 'coude', 'flexion')
        gain = position_plan(*[haut[k] for k in cles], hauteur_epaule)[1] - position_plan(*[prise[k] for k in cles], hauteur_epaule)[1]
        if gain < 30: erreur = erreur or HorsDePortee('l\'approche ne serait pas assez haute au-dessus du point'); continue
        if trajet_sur([haut[k] for k in cles], [prise[k] for k in cles], hauteur_epaule): return prise, haut
        erreur = erreur or HorsDePortee('la descente passerait trop près de la table')
    raise HorsDePortee(f'pas de position d\'approche ({erreur})')

def choisir_inclinaison(X, Y, hauteur_epaule=179.0, imposee=None):
    """Choisit l'inclinaison de la pince pour saisir en (X, Y) : la plus à plat qui marche (0°, puis −15°, −30°… jusqu'à −90°).
    `imposee` : n'essayer que celle-là. Renvoie (inclinaison, prise, approche) ou lève HorsDePortee (la raison donnée est celle de la
    pince à plat si le point est loin, celle de la pince pointée vers le bas s'il est près)."""
    erreurs = {}
    for incl in (INCLINAISONS if imposee is None else (float(imposee),)):
        try: return (incl,) + prise_et_approche(X, Y, hauteur_epaule, incl)
        except HorsDePortee as e: erreurs[incl] = e
    if imposee is not None: raise erreurs[float(imposee)]
    pres = 'trop près' in str(erreurs[0]) or 'coude' in str(erreurs[0])
    raise HorsDePortee(f"{erreurs[-90] if pres else erreurs[0]} ; aucune inclinaison de la pince ne convient")

def au_dessus(angles, leve=25.0):
    """La position d'approche : la même, épaule relevée de `leve` degrés, le poignet compensant pour garder la pince à plat.
    La pince se retrouve plus haut et un peu en arrière : de là, elle descend sur l'objet en avançant."""
    e = min(angles['epaule'] + leve, EPAULE_MAX); f = angles['flexion'] - (e - angles['epaule'])
    if abs(f) > B.FLEXION_MAX: raise HorsDePortee(f'poignet à {f:+.0f}° pour l\'approche : hors de ±{B.FLEXION_MAX}°')
    return dict(angles, epaule=e, flexion=f)

def ou_est_la_pince(socle, epaule, coude, flexion, hauteur_epaule=179.0):
    """L'inverse, pour vérifier : (X, Y, hauteur de l'axe de la pince, inclinaison de la pince) d'après les angles."""
    a, ag, t = math.radians(epaule), math.radians(epaule + coude), math.radians(epaule + coude + flexion)
    s = B.L_BRAS * math.cos(a) + B.L_COUDE_FLEXION * math.cos(ag) + B.L_APRES_FLEXION * math.cos(t)
    z = hauteur_epaule + B.L_BRAS * math.sin(a) + B.L_COUDE_FLEXION * math.sin(ag) + B.L_APRES_FLEXION * math.sin(t)
    th = math.radians(socle)
    return (DECALAGE_BRAS * math.cos(th) + s * math.sin(th), -DECALAGE_BRAS * math.sin(th) + s * math.cos(th), z, math.degrees(t))

def trajet_sur(depart, arrivee, hauteur_epaule=179.0, pas=12):
    """Vrai si, en passant en ligne droite d'un jeu d'angles (épaule, coude, flexion) à l'autre, la pince ne passe jamais sous la
    garde de la table. Si elle est DÉJÀ sous la garde au départ (le bras fléchit sous son poids : ses angles réels sont plus bas que
    ceux demandés), un trajet qui ne fait que MONTER reste permis : sinon le bras resterait bloqué en bas, « m » et « r » refusés
    (arrivé à Nicolas le 24/11/2026)."""
    h = [B.bas_de_pince(hauteur_epaule, *[d + (f - d) * k / pas for d, f in zip(depart, arrivee)], roulis=0.0) for k in range(pas + 1)]
    if h[0] >= B.MARGE_TABLE: return min(h) >= B.MARGE_TABLE
    return h[-1] >= B.MARGE_TABLE and all(y >= x - 0.5 for x, y in zip(h, h[1:]))

def point_dans_direction(angle, R):
    """Le point de la table à la distance R de l'axe du socle, dans la direction `angle` (degrés, + = à droite, 0 = droit devant)."""
    a = math.radians(angle); return R * math.sin(a), R * math.cos(a)

def bande(inclinaison, hauteur_epaule=179.0, angle=0.0):
    """Distances au socle (mini, maxi), dans la direction `angle`, où la pince peut SAISIR ou POSER avec cette inclinaison.
    Un objet pris pince inclinée doit être reposé avec la MÊME inclinaison, sinon il penche (Nicolas, 26/11/2026)."""
    ok = []
    for R in range(150, 520, 5):
        try: prise_et_approche(*point_dans_direction(angle, R), hauteur_epaule, inclinaison); ok.append(R)
        except HorsDePortee: pass
    return (min(ok), max(ok)) if ok else None

def zone_toutes(hauteur_epaule=179.0):
    """Distances au socle, droit devant, que la pince atteint en choisissant son inclinaison : (mini, maxi) en mm."""
    ok = []
    for r in range(100, 700, 2):
        th = math.atan2(DECALAGE_BRAS, math.sqrt(max(r * r - DECALAGE_BRAS ** 2, 1)))
        try: choisir_inclinaison(r * math.sin(th), r * math.cos(th), hauteur_epaule); ok.append(r)
        except HorsDePortee: pass
    return (min(ok), max(ok)) if ok else None

def zone(hauteur_axe=H_PRISE, hauteur_epaule=179.0):
    """Distances au socle, droit devant, entre lesquelles la pince peut se poser à plat à cette hauteur : (mini, maxi) en mm."""
    ok = []
    for r in range(100, 700, 2):
        th = math.atan2(DECALAGE_BRAS, math.sqrt(max(r * r - DECALAGE_BRAS ** 2, 1)))        # point visé droit devant le bras
        try: angles_pour(r * math.sin(th), r * math.cos(th), hauteur_axe, hauteur_epaule); ok.append(r)
        except HorsDePortee: pass
    return (min(ok), max(ok)) if ok else None
