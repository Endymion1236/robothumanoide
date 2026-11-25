"""Correction de visée : le bras n'arrive pas exactement où le calcul le dit (il penche, il fléchit, le socle n'est pas
parfaitement aligné avec les marqueurs). Plutôt que de chercher chaque défaut, on APPREND l'écart : sur quelques points de la
table, Nicolas amène la pince pile sur le point visé (touches de décalage de viser_camera) et enregistre. Pour un nouveau point,
on vise à côté de ce qu'il faut, d'après les écarts appris aux points voisins.

Un écart est gardé en « tourner le socle de tant » et « allonger de tant » (et non en millimètres à droite et en avant) : c'est
ainsi que le bras se trompe, donc un seul point appris corrige déjà correctement toute la table.
Calcul seul, sans servo ni caméra. Fichier : correction_point.json, à côté des programmes (reste sur le PC de Nicolas)."""
import json, math
from pathlib import Path

FICHIER = Path(__file__).with_name('correction_point.json')
PORTEE = 60.0      # mm : en dessous de cette distance, un point appris compte presque seul ; plus loin, on fait la moyenne des voisins

def polaire(X, Y): return math.hypot(X, Y), math.atan2(X, Y)                 # distance au socle, angle (0 = droit devant, + = à droite)
def cartesien(r, a): return r * math.sin(a), r * math.cos(a)

def ecart(cible, visee):
    """L'écart appris en un point : de combien il a fallu allonger (mm) et tourner (radians) pour que la pince tombe sur la cible."""
    (rc, ac), (rv, av) = polaire(*cible), polaire(*visee)
    return rv - rc, av - ac

def corriger(X, Y, points):
    """Où viser pour que la pince arrive en (X, Y). points : liste de {'X', 'Y', 'dr', 'da'} appris. Sans point : (X, Y) tel quel."""
    if not points: return X, Y
    poids = [1.0 / ((p['X'] - X) ** 2 + (p['Y'] - Y) ** 2 + PORTEE ** 2) for p in points]; total = sum(poids)
    dr = sum(w * p['dr'] for w, p in zip(poids, points)) / total; da = sum(w * p['da'] for w, p in zip(poids, points)) / total
    r, a = polaire(X, Y); return cartesien(r + dr, a + da)

def charger():
    try: pts = json.loads(FICHIER.read_text(encoding='utf-8'))
    except Exception: return []
    return [p for p in pts if isinstance(p, dict) and all(k in p for k in ('X', 'Y', 'dr', 'da'))] if isinstance(pts, list) else []

def enregistrer(points): FICHIER.write_text(json.dumps(points, indent=1), encoding='utf-8')

def apprendre(points, cible, visee, rayon=25.0):
    """Ajoute l'écart appris en `cible` (la pince y est quand on vise `visee`). Un point appris au même endroit (à `rayon` près) est remplacé."""
    dr, da = ecart(cible, visee)
    garde = [p for p in points if math.hypot(p['X'] - cible[0], p['Y'] - cible[1]) > rayon]
    return garde + [{'X': round(cible[0], 1), 'Y': round(cible[1], 1), 'dr': round(dr, 2), 'da': round(da, 5)}]

def en_clair(cible, visee):
    """L'écart dit comme Nicolas le voit : « 38 mm à droite, 45 mm plus près »."""
    dx, dy = visee[0] - cible[0], visee[1] - cible[1]; mots = []
    if abs(dx) >= 1: mots.append(f"{abs(dx):.0f} mm à {'droite' if dx > 0 else 'gauche'}")
    if abs(dy) >= 1: mots.append(f"{abs(dy):.0f} mm plus {'loin' if dy > 0 else 'près'}")
    return ', '.join(mots) if mots else 'aucun décalage'
