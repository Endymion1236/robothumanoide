"""Le bras va-t-il heurter un autre objet de la table ? Calcul seul, sans servo (demande de Nicolas, 26/11/2026).

Le bras est représenté par des points (avec un rayon) le long de ses segments : épaule → coude → axe de flexion → milieu des
mâchoires, et le volume des mâchoires ouvertes. Un objet posé est un cylindre debout (centre, rayon, hauteur). On essaie chaque
position du geste, et les positions intermédiaires (les servos y passent en ligne droite, angle par angle).
Un objet TENU dans la pince est aussi vérifié : il tourne avec la pince et pend sous elle.

Repère de la table (le même que la caméra) : X à droite (vu de derrière), Y en avant, Z vers le haut, origine sur l'axe du socle."""
import math
import piloter_bras as B, geometrie as G

RAYON_BRAS = 28.0              # mm : demi-largeur des segments du bras (fourches de 45 mm, berceaux), avec la visserie
RAYON_MACHOIRE = 8.0           # mm : demi-épaisseur d'une mâchoire avec son tapis
GARDE = 8.0                    # mm de marge autour de chaque objet
MACHOIRES_ARRIERE, MACHOIRES_AVANT, MACHOIRES_BAS = 20.0, 35.0, 40.0   # étendue des mâchoires autour du milieu, le long et sous l'axe

def _vers_table(socle, s, z, v=0.0):
    """Un point du plan du bras (s devant l'épaule, hauteur z, v en travers du plan) → (X, Y, Z) sur la table."""
    th = math.radians(socle); d = G.DECALAGE_BRAS + v
    return d * math.cos(th) + s * math.sin(th), -d * math.sin(th) + s * math.cos(th), z

def points_du_bras(socle, epaule, coude, flexion, hauteur_epaule=179.0, ouverture=0.0, tenu=None, roulis=0.0):
    """Liste de (X, Y, Z, rayon). ouverture : écart des mâchoires (mm). tenu : (inclinaison à la prise, hauteur de prise, hauteur et
    rayon de l'objet) si la pince tient un objet. roulis : rotation de la pince sur elle-même (degrés, + = le haut part à gauche vu de
    derrière) : les mâchoires ne sont plus de part et d'autre du plan du bras, l'une passe au-dessus, l'autre en dessous."""
    a, ag, t = math.radians(epaule), math.radians(epaule + coude), math.radians(epaule + coude + flexion)
    e = (0.0, hauteur_epaule)
    c = (e[0] + B.L_BRAS * math.cos(a), e[1] + B.L_BRAS * math.sin(a))
    f = (c[0] + B.L_COUDE_FLEXION * math.cos(ag), c[1] + B.L_COUDE_FLEXION * math.sin(ag))
    m = (f[0] + B.L_APRES_FLEXION * math.cos(t), f[1] + B.L_APRES_FLEXION * math.sin(t))
    pts = []
    for p, q, n in ((e, c, 6), (c, f, 8), (f, (m[0] - (MACHOIRES_ARRIERE + 10) * math.cos(t), m[1] - (MACHOIRES_ARRIERE + 10) * math.sin(t)), 8)):
        for k in range(n + 1):
            s_, z_ = p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n
            pts.append((*_vers_table(socle, s_, z_), RAYON_BRAS))
    u, d = (math.cos(t), math.sin(t)), (math.sin(t), -math.cos(t))            # le long de la pince, et « sous » la pince
    cr, sr = math.cos(math.radians(roulis)), math.sin(math.radians(roulis))
    for dv in ((-1, 1) if ouverture else (0,)):
        v = dv * (ouverture / 2 + RAYON_MACHOIRE)
        # pince tournée : l'écart des mâchoires se partage entre le travers (cos) et le « dessus » de la pince (sin), qui est -d
        vt, vh = v * cr, v * sr
        for du in (-MACHOIRES_ARRIERE, 0.0, MACHOIRES_AVANT / 2, MACHOIRES_AVANT):
            for dd in (0.0, MACHOIRES_BAS / 2, MACHOIRES_BAS):
                pts.append((*_vers_table(socle, m[0] + du * u[0] + (dd - vh) * d[0], m[1] + du * u[1] + (dd - vh) * d[1], vt), RAYON_MACHOIRE))
    if tenu:
        t0, h_prise, h_obj, r_obj = tenu
        dt = t - math.radians(t0)                                            # l'objet a tourné avec la pince depuis la prise
        vert = (-math.sin(dt), math.cos(dt))                                 # la verticale de l'objet, tournée de dt dans le plan
        for k in range(7):
            l = -h_prise + (h_obj) * k / 6                                   # du pied (sur la table à la prise) au sommet
            pts.append((*_vers_table(socle, m[0] + l * vert[0], m[1] + l * vert[1]), r_obj))
    return pts

def heurte(points, obstacles):
    """Le premier obstacle touché par un des points, ou None. obstacles : liste de dicts X, Y, rayon, hauteur (+ nom)."""
    for o in obstacles:
        for x, y, z, r in points:
            if z < o['hauteur'] + GARDE + r * 0.5 and math.hypot(x - o['X'], y - o['Y']) < o['rayon'] + r + GARDE:
                return o
    return None

def geste_libre(socle, positions, obstacles, hauteur_epaule=179.0, ouverture=0.0, tenu=None, pas=6, roulis=0.0):
    """positions : suite de dicts (epaule, coude, flexion) parcourus dans l'ordre, en ligne droite d'un à l'autre.
    Renvoie l'obstacle heurté, ou None si tout le geste est libre."""
    cles = ('epaule', 'coude', 'flexion')
    for p, q in zip(positions, positions[1:]):
        for k in range(pas + 1):
            ang = [p[c] + (q[c] - p[c]) * k / pas for c in cles]
            o = heurte(points_du_bras(socle, *ang, hauteur_epaule, ouverture, tenu, roulis), obstacles)
            if o: return o
    return None
