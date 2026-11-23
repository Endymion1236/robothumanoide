"""Aller à un point de la table : quels angles donner au socle, à l'épaule, au coude et au poignet pour que la pince,
tenue À L'HORIZONTALE, arrive au-dessus d'un point (X, Y) de la table. Calcul seul, sans servo.

Repère de la table (le même que la caméra) : origine sur l'axe du socle, X vers la droite du robot (vu de derrière), Y vers l'avant.
Le bras ne tourne pas autour de son propre plan : il est DÉCALÉ de 53,5 mm à GAUCHE de l'axe du socle, vu de derrière
(photo de Nicolas du 23/11/2026). Le calcul en tient compte.
Il faut le poignet complet (flexion, servo n° 6) : c'est lui qui garde la pince à plat."""
import math
import piloter_bras as B, test_epaule as E

DECALAGE_BRAS = -53.5          # mm : position du plan du bras par rapport à l'axe du socle, + = à droite vu de derrière
H_PRISE = 45.0                 # hauteur de l'axe de la pince au-dessus de la table pour saisir : le bas des mâchoires est alors à 10 mm
H_SURVOL = 130.0               # hauteur de l'axe de la pince pour arriver au-dessus d'un objet sans le toucher
EPAULE_MAX = E.REPOS           # au-delà, l'épaule bute contre le ressort

class HorsDePortee(Exception): pass

def angles_plan(s, z, inclinaison=0.0, hauteur_epaule=179.0):
    """Dans le plan du bras : les angles (épaule, coude, flexion) pour amener le milieu des mâchoires à la distance s devant l'axe de
    l'épaule et à la hauteur z au-dessus de la table, la pince inclinée de `inclinaison` degrés (0 = à plat, −90 = pointée vers le bas)."""
    L1, L2, L3 = B.L_BRAS, B.L_COUDE_FLEXION, B.L_APRES_FLEXION; t = math.radians(inclinaison)
    xw, zw = s - L3 * math.cos(t), z - L3 * math.sin(t) - hauteur_epaule          # l'axe de flexion du poignet, vu depuis l'épaule
    d2 = xw * xw + zw * zw
    c = (d2 - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    if c > 1: raise HorsDePortee('trop loin pour le bras')
    if c < -1 or xw < 20: raise HorsDePortee('trop près du socle')
    g = -math.acos(c)                                                # coude « en haut » : le haut du bras monte, l'avant-bras redescend
    a = math.atan2(zw, xw) - math.atan2(L2 * math.sin(g), L1 + L2 * math.cos(g))
    r = {'epaule': math.degrees(a), 'coude': math.degrees(g), 'flexion': inclinaison - math.degrees(a + g)}
    if not E.BAS <= r['epaule'] <= EPAULE_MAX: raise HorsDePortee(f"épaule à {r['epaule']:+.0f}° : hors de {E.BAS}° à {EPAULE_MAX}° ({'trop loin ou trop bas' if r['epaule'] < E.BAS else 'trop près ou trop haut'})")
    if abs(r['coude']) > B.COUDE_MAX: raise HorsDePortee(f"coude à {r['coude']:+.0f}° : hors de ±{B.COUDE_MAX}° (trop près)")
    if abs(r['flexion']) > B.FLEXION_MAX: raise HorsDePortee(f"poignet à {r['flexion']:+.0f}° : hors de ±{B.FLEXION_MAX}°")
    return r

def position_plan(epaule, coude, flexion, hauteur_epaule=179.0):
    """L'inverse : (distance devant l'épaule, hauteur au-dessus de la table, inclinaison de la pince) d'après les angles."""
    a, ag, t = math.radians(epaule), math.radians(epaule + coude), math.radians(epaule + coude + flexion)
    return (B.L_BRAS * math.cos(a) + B.L_COUDE_FLEXION * math.cos(ag) + B.L_APRES_FLEXION * math.cos(t),
            hauteur_epaule + B.L_BRAS * math.sin(a) + B.L_COUDE_FLEXION * math.sin(ag) + B.L_APRES_FLEXION * math.sin(t), math.degrees(t))

def angles_pour(X, Y, hauteur_axe=H_PRISE, hauteur_epaule=179.0):
    """Renvoie {'socle', 'epaule', 'coude', 'flexion'} en degrés, pince à l'horizontale, ou lève HorsDePortee avec la raison."""
    R = math.hypot(X, Y)
    if R <= abs(DECALAGE_BRAS) + 1: raise HorsDePortee('point trop près du socle')
    s = math.sqrt(R * R - DECALAGE_BRAS ** 2)                       # distance à parcourir dans le plan du bras, depuis l'axe de l'épaule
    socle = math.degrees(math.atan2(X, Y) - math.atan2(DECALAGE_BRAS, s))
    if abs(socle) > B.SOCLE_MAX: raise HorsDePortee(f'il faudrait tourner le socle de {socle:+.0f}° (limite ±{B.SOCLE_MAX}°)')
    try: return dict(angles_plan(s, hauteur_axe, 0.0, hauteur_epaule), socle=socle)
    except HorsDePortee as e: raise HorsDePortee(f'{e} ({R:.0f} mm du socle)')

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
    """Vrai si, en passant en ligne droite d'un jeu d'angles (épaule, coude, flexion) à l'autre, la pince ne descend jamais sous la table."""
    return all(B.bas_de_pince(hauteur_epaule, *[d + (f - d) * k / pas for d, f in zip(depart, arrivee)], roulis=0.0) >= 3 for k in range(pas + 1))

def zone(hauteur_axe=H_PRISE, hauteur_epaule=179.0):
    """Distances au socle, droit devant, entre lesquelles la pince peut se poser à plat à cette hauteur : (mini, maxi) en mm."""
    ok = []
    for r in range(100, 700, 2):
        th = math.atan2(DECALAGE_BRAS, math.sqrt(max(r * r - DECALAGE_BRAS ** 2, 1)))        # point visé droit devant le bras
        try: angles_pour(r * math.sin(th), r * math.cos(th), hauteur_axe, hauteur_epaule); ok.append(r)
        except HorsDePortee: pass
    return (min(ok), max(ok)) if ok else None
