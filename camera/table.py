"""Repérer la table avec la caméra : 4 marqueurs imprimés aux coins de la zone de travail → où se trouve un point de l'image,
en millimètres, par rapport au socle du bras. Calcul seul (pas de caméra ici) : utilisé par voir_table.py et par les essais.

Repère de la table : origine sur l'axe du socle, X vers la DROITE du robot (vu de derrière le bras), Y vers l'AVANT.
Les 4 marqueurs forment un rectangle, vus de derrière le bras :
    3 (au fond à gauche) ---- 2 (au fond à droite)
    0 (près, à gauche)   ---- 1 (près, à droite)
Réglage (table.json, écrit par regler_table.bat) : largeur entre les centres de 0 et 1, profondeur entre les centres de 0 et 3,
et position du centre du marqueur 0 par rapport à l'axe du socle."""
import json, math
from pathlib import Path
import numpy as np, cv2

FICHIER = Path(__file__).with_name('table.json')
DICO = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
IDS = (0, 1, 2, 3)

def coins_table(r):
    """Centres des 4 marqueurs dans le repère de la table (mm), d'après le réglage."""
    x0, y0, l, p = r['x0'], r['y0'], r['largeur'], r['profondeur']
    return {0: (x0, y0), 1: (x0 + l, y0), 2: (x0 + l, y0 + p), 3: (x0, y0 + p)}

def detecter(image):
    """Cherche les marqueurs dans une image. Renvoie {numéro: centre (x, y) en pixels} et {numéro: 4 coins}."""
    gris = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    if hasattr(cv2.aruco, 'ArucoDetector'): coins, ids, _ = cv2.aruco.ArucoDetector(DICO, cv2.aruco.DetectorParameters()).detectMarkers(gris)
    else: coins, ids, _ = cv2.aruco.detectMarkers(gris, DICO)
    centres, contours = {}, {}
    if ids is not None:
        for c, i in zip(coins, ids.flatten()):
            if int(i) in IDS: centres[int(i)] = tuple(c[0].mean(axis=0)); contours[int(i)] = c[0]
    return centres, contours

def passage(centres, reglage):
    """La transformation image → table, si les 4 marqueurs sont vus. Sinon None."""
    if any(i not in centres for i in IDS): return None
    t = coins_table(reglage)
    return cv2.getPerspectiveTransform(np.float32([centres[i] for i in IDS]), np.float32([t[i] for i in IDS]))

def vers_table(h, x, y):
    """Un point de l'image (pixels) → sa position sur la table (mm)."""
    p = cv2.perspectiveTransform(np.float32([[[x, y]]]), h)[0][0]
    return float(p[0]), float(p[1])

def vers_image(h, X, Y):
    p = cv2.perspectiveTransform(np.float32([[[X, Y]]]), np.linalg.inv(h))[0][0]
    return int(round(p[0])), int(round(p[1]))

def pour_le_bras(X, Y):
    """Ce que le bras devra faire pour viser ce point : angle du socle (+ = à droite, vu de derrière) et distance à l'axe du socle."""
    return math.degrees(math.atan2(X, Y)), math.hypot(X, Y)

def charger():
    try: r = json.loads(FICHIER.read_text(encoding='utf-8'))
    except Exception: return None
    return r if all(k in r for k in ('x0', 'y0', 'largeur', 'profondeur')) else None
