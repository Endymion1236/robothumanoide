"""Largeur réelle entre les mâchoires, d'après la position du servo de la pince. Le calcul de test_pince.ecart_mm vient du dessin ;
au premier tri réel il annonçait 11 mm pour des objets de 28 et 40 mm (Nicolas, 26/11/2026). On l'étalonne donc sur deux objets
connus (etalonner_largeur.bat) : la largeur devient une droite passant par ces deux mesures. Gardé dans largeur_pince.json (PC)."""
import json
from pathlib import Path
import test_pince as PI

FICHIER = Path(__file__).with_name('largeur_pince.json')
def charger():
    try: d = json.loads(FICHIER.read_text(encoding='utf-8')); return d if len(d.get('points', [])) >= 2 else None
    except Exception: return None

def ecart(position, ouvert, etal=None):
    """Écart entre les mâchoires (mm). Avec étalonnage : droite par les points mesurés ; sinon le calcul du dessin."""
    etal = etal if etal is not None else charger()
    if not etal: return PI.ecart_mm(position, ouvert)
    (p1, l1), (p2, l2) = etal['points'][:2]
    return l1 + (position - p1) * (l2 - l1) / (p2 - p1)

def position_pour(mm, ouvert, ferme, etal=None):
    """La position du servo qui donne cet écart (bornée entre fermé et ouvert)."""
    lo, hi = sorted((ouvert, ferme))
    return min(range(lo, hi + 1, 2), key=lambda q: abs(ecart(q, ouvert, etal) - mm))
