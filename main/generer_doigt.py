"""Doigt d'essai pour la future main de Câlin (mécanisme « deux fils », décision du 18/11/2026). Prototype : rien n'est imprimé.

Ce doigt s'essaie À LA MAIN, sans servo : on tire sur le fil du dessous pour le fermer, sur celui du dessus pour l'ouvrir.
Il sert à valider les charnières, les butées et le passage des fils AVANT de dessiner la poulie et le support du petit servo
(qui ne sont pas dessinés : le servo n'est pas encore reçu ni mesuré).

4 pièces : une base (vissée sur une planchette par 2 vis M3) et 3 phalanges. Chaque charnière est une languette prise dans
une fourche ; l'axe est un morceau de FILAMENT de 1,75 mm (serré dans la fourche, libre dans la languette).
Butées : doigt tendu (0°) et doigt plié. Deux canaux de fil traversent tout le doigt, à 3,6 mm de part et d'autre des axes.
Repère d'une phalange : X le long du doigt, Y = axe des charnières, Z vers le dos de la main.
Lancer : python generer_doigt.py → sortie/doigt_*.stl, sortie/verification_doigt.json"""
import json, math
from pathlib import Path
import numpy as np, manifold3d as mf, trimesh as tm

OUT = Path(__file__).resolve().parent / 'sortie'; OUT.mkdir(exist_ok=True)
LARGEUR, HAUTEUR = 14.0, 14.0; R = HAUTEUR / 2
LONGUEURS = [30.0, 22.0, 18.0]            # 3 phalanges, d'axe en axe (la dernière : de son axe au bout)
L_BASE = 32.0                             # base : du bord arrière à l'axe de la première charnière
EP_LANGUETTE, JEU = 5.0, 0.25             # languette de 5 mm dans une fente de 5,5
D_AXE_SERRE, D_AXE_LIBRE = 1.9, 2.3       # filament de 1,75 : serré dans la fourche, libre dans la languette
BAISSE = 2.0                              # la languette est plus basse de 2 mm côté dos : un pont de la fourche vient buter dessus (doigt tendu)
Z_FIL, D_FIL = 3.6, 1.6                   # canaux des fils : à 3,6 mm au-dessus et au-dessous des axes
PLI_MAX = 85.0                            # angle de pliage visé à chaque charnière

def box(x0, y0, z0, x1, y1, z1): return mf.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))
def cyl_y(x, z, y0, y1, d, n=48): return mf.Manifold.cylinder(y1 - y0, d / 2, d / 2, n).rotate((-90, 0, 0)).translate((x, y0, z))
def cyl_x(x0, x1, y, z, d, n=24): return mf.Manifold.cylinder(x1 - x0, d / 2, d / 2, n).rotate((0, 90, 0)).translate((x0, y, z))
def cyl_z(x, y, z0, z1, d, n=24): return mf.Manifold.cylinder(z1 - z0, d / 2, d / 2, n).translate((x, y, z0))
def mesh(m):
    g = m.to_mesh(); return tm.Trimesh(vertices=np.asarray(g.vert_properties)[:, :3], faces=np.asarray(g.tri_verts), process=True)
def plier(m, angle, x_axe): return m.translate((-x_axe, 0, 0)).rotate((0, angle, 0)).translate((x_axe, 0, 0))   # angle > 0 : le doigt se ferme (vers −Z)

R_L = R - BAISSE                          # rayon de la languette autour de l'axe : elle tourne SOUS le pont de butée

def languette():
    """Bout arrière d'une phalange : une languette arrondie autour de l'axe (x = 0), dont le dessus est plat et abaissé."""
    e = EP_LANGUETTE / 2
    m = cyl_y(0, 0, -e, e, 2 * R_L, 64) + box(0, -e, -R, R + 1.0, e, R_L)
    return m - cyl_y(0, 0, -e - 1, e + 1, D_AXE_LIBRE, 32)

def fourche(x):
    """Bout avant (axe en x) : deux oreilles, une fente pour la languette, et un petit pont côté dos, juste devant l'axe :
    doigt tendu, le dessus plat de la languette vient buter dessous."""
    e = EP_LANGUETTE / 2 + JEU
    m = box(x - R - 3, -LARGEUR / 2, -R, x, LARGEUR / 2, R) + cyl_y(x, 0, -LARGEUR / 2, LARGEUR / 2, 2 * R, 64)
    fente = cyl_y(x, 0, -e, e, 2 * (R_L + 0.6), 64) + box(x, -e, -R - 1, x + R + 2, e, R + 1)
    fente += box(x - R - 0.6, -e, -R - 1, x + 1, e, 0)                           # dégagement côté paume : la languette y descend quand le doigt plie
    fente -= box(x + 0.5, -e - 1, R_L + 0.15, x + 3.5, e + 1, R + 1)               # le pont de butée
    return m - fente - cyl_y(x, 0, -LARGEUR / 2 - 1, LARGEUR / 2 + 1, D_AXE_SERRE, 32)

def canaux(m, x0, x1):
    for s in (1, -1): m -= cyl_x(x0 - 1, x1 + 1, 0, s * Z_FIL, D_FIL)
    return m

def phalange(L, dernier=False):
    corps0, corps1 = R + 1.0, (L - R * 0.6 if dernier else L - R - 3)
    m = languette() + box(corps0, -LARGEUR / 2, -R, corps1, LARGEUR / 2, R)
    if dernier:
        m += cyl_y(L - R * 0.6, 0, -LARGEUR / 2, LARGEUR / 2, 2 * R, 64) ^ box(corps1, -LARGEUR / 2, -R, L + R, LARGEUR / 2, R)   # bout arrondi
        m = canaux(m, -R - 1, L - 9.0)
        m -= cyl_z(L - 9.0, 0, -R - 1, R + 1, 2.6)                                 # puits vertical : les deux fils s'y rejoignent et s'y nouent
    else:
        m = canaux(m + fourche(L), -R - 1, L + R + 2)
    return m

def base():
    m = box(-L_BASE, -LARGEUR / 2, -R, -R - 3, LARGEUR / 2, R) + fourche(0.0)
    m += box(-L_BASE, -LARGEUR / 2 - 9, -R, -L_BASE + 12, LARGEUR / 2 + 9, -R + 4)   # deux pattes pour visser la base sur une planchette
    for s in (1, -1): m -= cyl_z(-L_BASE + 6, s * (LARGEUR / 2 + 4.5), -R - 1, -R + 5, 3.4)
    return canaux(m, -L_BASE - 1, R + 2)

BASE, PHALANGES = base(), [phalange(L, k == 2) for k, L in enumerate(LONGUEURS)]
def doigt(angles):
    """Les 4 pièces en place pour 3 angles de pliage (degrés). Renvoie la liste des pièces."""
    pieces, m_tr = [BASE], []
    x = 0.0
    out = [BASE]
    # on place de la base vers le bout : chaque phalange est tournée autour de son propre axe, puis emportée par les précédentes
    transf = []
    for k, ph in enumerate(PHALANGES):
        p = ph.rotate((0, angles[k], 0))
        for (a, L) in reversed(transf): p = p.translate((L, 0, 0)).rotate((0, a, 0))
        out.append(p); transf.append((angles[k], LONGUEURS[k]))
    return out

if __name__ == '__main__':
    r = {'etat': 'PROTOTYPE, rien n\'est imprimé'}
    # course de chaque charnière : on cherche les deux butées par le calcul (première position où les pièces se touchent)
    courses = []
    for k, ph in enumerate(PHALANGES):
        avant = BASE if k == 0 else PHALANGES[k - 1].translate((-LONGUEURS[k - 1], 0, 0))
        libre = lambda a: (ph.rotate((0, a, 0)) ^ avant).volume() < 0.05
        assert libre(5.0), f'charnière {k + 1} : coincée dès le départ'
        plie = next((a - 1 for a in range(5, 131) if not libre(a)), 130); tendu = next((a + 1 for a in range(5, -41, -1) if not libre(a)), -40)
        courses.append((tendu, plie))
        assert tendu >= -3, f'charnière {k + 1} : le doigt se retourne de {-tendu}° avant de buter'
        assert plie >= PLI_MAX - 5, f'charnière {k + 1} : ne plie que de {plie}°'
    r['courses_des_charnieres_deg'] = [{'butée doigt tendu': t, 'butée doigt plié': p} for t, p in courses]
    plis = [min(p, PLI_MAX) for _, p in courses]
    pcs = doigt(plis)
    for i in range(len(pcs)):
        for j in range(i + 2, len(pcs)): assert (pcs[i] ^ pcs[j]).volume() < 0.05, f'doigt plié : les pièces {i} et {j} se touchent'
    r['doigt_plie'] = f'plié de {plis} : aucune pièce ne touche une pièce non voisine'
    r['fil_a_tirer_mm'] = {'pour plier à fond': round(Z_FIL * math.radians(sum(plis)), 1), 'bras de levier du fil': Z_FIL}
    r['longueur_du_doigt_mm'] = sum(LONGUEURS) + R * 0.4
    r['masse_g'] = round(sum(m.volume() for m in [BASE] + PHALANGES) * 1.25e-3, 1)
    r['il_faut'] = ['3 morceaux de filament de 1,75 mm, de 14 mm de long (les axes)', 'du fil de pêche tressé (un seul brin, environ 40 cm)', '2 vis à bois ou M3 pour fixer la base sur une planchette']
    R_IMPR = [[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, LARGEUR / 2]]                 # couché sur le flanc : les trous des axes sont verticaux
    for nom, m in [('doigt_base', BASE)] + [(f'doigt_phalange_{k + 1}', p) for k, p in enumerate(PHALANGES)]:
        assert len(m.decompose()) == 1, f'{nom} en plusieurs morceaux'
        pose = m.transform(R_IMPR) if nom != 'doigt_base' else m.translate((0, 0, R))
        mesh(pose).export(OUT / f'{nom}.stl'); r.setdefault('stl', []).append(f'{nom}.stl')
    json.dump(r, open(OUT / 'verification_doigt.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False, indent=1))
