"""Trouver les objets posés sur la table, avec la caméra du dessus. Calcul seul (pas de caméra ici) : utilisé par bras/trier.py.

Le principe : on garde une photo de la table VIDE (le « fond »), bras au repos. Ensuite, tout ce qui a changé par rapport à ce fond
est un objet. Les deux images sont d'abord redressées en vue de dessus, 1 point = 1 mm, grâce aux 4 marqueurs.

Un objet haut, vu par une caméra qui n'est pas juste au-dessus, « penche » sur l'image : on voit son sommet décalé, à l'opposé de la
caméra. Son milieu apparent n'est donc pas son pied. Le programme calcule où est la caméra (à partir des 4 marqueurs) et corrige
ce décalage pour des objets de hauteur connue (HAUTEUR_OBJETS, 60 mm pour les objets d'essai).

Limites connues :
  - un objet de la couleur du bois se voit mal ; les objets gris ou noirs sont reconnus parce qu'ils n'ont pas la couleur du bois ;
    les ombres, qui foncent le bois sans lui ôter sa couleur, sont écartées ;
  - deux objets qui se touchent sont vus comme un seul ;
  - la forme (rond, carré, hexagone) se lit mal sur un objet qui penche : on se sert surtout de la TAILLE, mesurée par la pince."""
import math
import numpy as np, cv2
import table as T

HAUTEUR_OBJETS = 60.0                     # mm
MARGE = 40.0                              # mm : on regarde aussi un peu autour du rectangle des marqueurs
SEUIL_COULEUR, SEUIL_CLAIR = 18.0, 28.0
SEUIL_FONCE, SEUIL_JAUNE, SEUIL_NOIR = 12.0, 0.06, 45.0  # objet gris : 12 plus foncé, et nettement moins jaune pour sa luminosité   # différences avec le fond (échelle Lab d'OpenCV) au-delà desquelles c'est un objet
DEMI_MARQUEUR = 38.0                      # mm : carré ignoré autour du centre de chaque marqueur (papier et scotch compris). Nicolas,
                                          # 26/11/2026 : un faux objet de 57 mm sur le marqueur n° 3 (lumière changée depuis la photo du fond)
AIRE_MIN = 250.0                          # mm² : en dessous, c'est une poussière ou un reflet
F_PAR_DEFAUT = 1537.0                     # points, pour une image de 1280 de large : C270 (55° en diagonale, fiche du fabricant)

def cadre(reglage):
    """Le rectangle de table regardé, en mm : (Xmin, Ymin, Xmax, Ymax)."""
    t = T.coins_table(reglage).values(); xs, ys = [p[0] for p in t], [p[1] for p in t]
    return min(xs) - MARGE, min(ys) - MARGE, max(xs) + MARGE, max(ys) + MARGE

def redresser(image, h, reglage):
    """L'image vue de dessus, 1 point par mm. La ligne 0 est au FOND de la table (Y le plus grand), la colonne 0 à gauche."""
    x0, y0, x1, y1 = cadre(reglage)
    vers_vue = np.array([[1, 0, -x0], [0, -1, y1], [0, 0, 1]], float) @ h        # image → table (mm) → vue de dessus
    return cv2.warpPerspective(image, vers_vue, (int(x1 - x0), int(y1 - y0)), flags=cv2.INTER_LINEAR)
def vue_vers_table(reglage, u, v):
    x0, y0, x1, y1 = cadre(reglage); return x0 + u, y1 - v

def camera(h, taille_image):
    """Où est la caméra au-dessus de la table : (X, Y, hauteur) en mm, et la focale utilisée. Calculé à partir des marqueurs.
    La focale est tirée de la déformation du rectangle si la caméra est assez penchée, sinon celle de la fiche de la C270."""
    w, hh = taille_image; cx, cy = w / 2, hh / 2
    Hm = np.linalg.inv(h)                                                        # table → image
    Hc = np.array([[1, 0, -cx], [0, 1, -cy], [0, 0, 1]]) @ Hm                    # point principal au centre
    f = F_PAR_DEFAUT * w / 1280
    den = Hc[2, 0] * Hc[2, 1]
    if abs(den) > 1e-12:
        f2 = -(Hc[0, 0] * Hc[0, 1] + Hc[1, 0] * Hc[1, 1]) / den
        if f2 > 0 and 0.5 * f < math.sqrt(f2) < 2.0 * f: f = math.sqrt(f2)
    K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]], float)
    obj = np.float32([[x, y, 0] for x, y in [(0, 0), (400, 0), (400, 300), (0, 300), (200, 150)]])
    img = cv2.perspectiveTransform(obj[:, :2].reshape(-1, 1, 2), Hm).reshape(-1, 2)
    ok, rvec, tvec = cv2.solvePnP(obj, img.astype(np.float32), K, None, flags=cv2.SOLVEPNP_ITERATIVE)
    R, _ = cv2.Rodrigues(rvec); C = (-R.T @ tvec).ravel()
    if C[2] < 0: C = -C                                                          # la caméra est au-dessus de la table
    return float(C[0]), float(C[1]), float(abs(C[2])), f

def masque(vue, fond):
    """Ce qui a changé par rapport au fond. Une ombre (le bois seulement plus foncé, sans changer de teinte) n'est pas un objet."""
    a = cv2.cvtColor(cv2.GaussianBlur(vue, (5, 5), 0), cv2.COLOR_BGR2LAB).astype(np.float32)
    b = cv2.cvtColor(cv2.GaussianBlur(fond, (5, 5), 0), cv2.COLOR_BGR2LAB).astype(np.float32)
    teinte = np.hypot(a[..., 1] - b[..., 1], a[..., 2] - b[..., 2]); clair = a[..., 0] - b[..., 0]
    # objets GRIS FONCÉ (ceux de Nicolas, photo du 26/11/2026) : plus foncés que le bois ET moins JAUNES que lui (le bois de sa
    # table est jaune pâle, le plastique gris tire légèrement vers le bleu) ; les faces très sombres sont prises sur leur seule
    # luminosité. Une ombre légère fonce le bois sans lui ôter son jaune : elle n'est pas prise.
    # le jaune est compté RAPPORTÉ à la luminosité : une ombre, même forte, fonce le bois sans changer ce rapport ; un plastique
    # gris le fait chuter. Les faces très sombres (moins de 50 sur 255) sont prises sur leur seule luminosité.
    jaune = lambda x: (x[..., 2] - 128) / np.maximum(x[..., 0], 20)
    gris = (clair < -SEUIL_FONCE) & (jaune(a) - jaune(b) < -SEUIL_JAUNE)
    noir = (clair < -SEUIL_NOIR) & (a[..., 0] < 50)
    m = ((teinte > SEUIL_COULEUR) | (clair > SEUIL_CLAIR) | gris | noir).astype(np.uint8) * 255
    m[(vue.sum(axis=2) == 0) | (fond.sum(axis=2) == 0)] = 0                      # hors de l'image de la caméra
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

def trouver(image, fond, h, reglage, hauteur=HAUTEUR_OBJETS, exclure=()):
    """Les objets sur la table. image et fond : images de la caméra (le fond = table vide). exclure : cercles (X, Y, rayon) à
    ignorer (zones de dépôt). Renvoie une liste de dicts : X, Y (pied de l'objet, mm), largeur et longueur vues (mm), aire,
    allonge (longueur / largeur), contour (mm, pour dessiner)."""
    vue, vfond = redresser(image, h, reglage), redresser(fond, h, reglage)
    m = masque(vue, vfond)
    x0, y0, x1, y1 = cadre(reglage)
    for X, Y in T.coins_table(reglage).values():                                # les marqueurs eux-mêmes ne sont jamais des objets
        cv2.rectangle(m, (int(X - x0 - DEMI_MARQUEUR), int(y1 - Y - DEMI_MARQUEUR)), (int(X - x0 + DEMI_MARQUEUR), int(y1 - Y + DEMI_MARQUEUR)), 0, -1)
    for X, Y, r in exclure:
        x0, y0, x1, y1 = cadre(reglage); cv2.circle(m, (int(X - x0), int(y1 - Y)), int(r), 0, -1)
    cX, cY, cZ, _ = camera(h, (image.shape[1], image.shape[0]))
    k = cZ / max(cZ - hauteur, 1.0)                                              # le sommet est vu « agrandi » de k depuis la caméra
    objets = []
    for c in cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        if cv2.contourArea(c) < AIRE_MIN: continue
        c = cv2.convexHull(c)                                                    # les objets d'essai sont convexes : on bouche les creux du contour
        mo = cv2.moments(c); gu, gv = mo['m10'] / mo['m00'], mo['m01'] / mo['m00']
        gX, gY = vue_vers_table(reglage, gu, gv)
        # on voit le pied et le sommet ; leur milieu apparent est à mi-chemin entre le pied (facteur 1) et le sommet (facteur k)
        s = 2 / (1 + k); X, Y = cX + (gX - cX) * s, cY + (gY - cY) * s
        pts = np.array([vue_vers_table(reglage, u, v) for u, v in c.reshape(-1, 2)], float)
        d = np.array([gX - cX, gY - cY]); d /= max(np.linalg.norm(d), 1e-6); n = np.array([-d[1], d[0]])
        larg = float(np.ptp(pts @ n)) / ((1 + k) / 2)                             # en travers du « penché » : la vraie largeur
        long_ = float(np.ptp(pts @ d)) - (k - 1) * math.hypot(X - cX, Y - cY)     # le long : on retire l'allongement dû à la hauteur
        (_, _), (a1, a2), _ = cv2.minAreaRect(pts.astype(np.float32))
        objets.append({'X': X, 'Y': Y, 'largeur': larg, 'longueur': max(long_, 1.0), 'aire': cv2.contourArea(c),
                       'allonge': max(long_, larg) / max(min(long_, larg), 1.0), 'contour': pts})
    return sorted(objets, key=lambda o: -o['Y'])
