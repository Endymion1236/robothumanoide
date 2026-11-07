"""Le coude V1 monté sur le bras V1 : jusqu'où l'avant-bras peut-il tourner ?

Construit le bras et sa bride (verify_bras.py), la fourche (mêmes expressions que CoudeV1.py),
place la fourche sur l'axe du servo, puis la fait tourner par pas de 1°. 0° = avant-bras dans le
prolongement du servo, côté opposé au bras. Sans Fusion, sans validation physique.
"""
from pathlib import Path
import ast, json, math, io, contextlib, runpy
import manifold3d as mf, trimesh as tm
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ICI = Path(__file__).resolve().parent
with contextlib.redirect_stdout(io.StringIO()):
    V = runpy.run_path(str(ICI/'verify_bras.py'))
pb, bras, bride, servo_ref = V['p'], V['b'], V['brace'], V['servo']

tree = ast.parse((ICI.parent/'CoudeV1'/'CoudeV1.py').read_text(encoding='utf-8'))
SPECS = next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SPECS' for t in n.targets))
pc = {}
for n, e in SPECS: pc[n] = eval(e.replace(' mm', ''), {'__builtins__': {}}, pc)
g = type('P', (), pc)
def box(x, y, z, l, w, h): return mf.Manifold.cube((l, w, h)).translate((x, y, z))
def cyl(x, y, z, d, h): return mf.Manifold.cylinder(h, d/2, d/2, 96).translate((x, y, z))
def demi(haut):  # même construction que verify_coude.py, trous inutiles pour les collisions
    zp = g.z_haut if haut else 0
    m = box(g.axe_X, g.pl_y, zp, g.avant_bras_L, g.plaque_W, g.plaque_T) + cyl(g.axe_X, g.axe_Y, zp, 2*g.bout_R, g.plaque_T)
    zb = g.plaque_T + g.demi_H + g.jeu_serrage if haut else g.plaque_T
    for x, l in ((g.axe_X + g.entretoise_A_X, g.entretoise_A_L), (g.axe_X + g.ent_B_X, g.entretoise_B_L)):
        m += box(x, g.pl_y, zb, l, g.plaque_W, g.demi_H)
    return m
fourche = demi(True) + demi(False)

# Axe du servo dans le repère du bras ; dessous de la plaque basse = appui - disque bas - plaque.
ax, ay = pb['sx'] + g.axe_bout, pb['base_W']/2
z0 = pb['support_Z'] - g.disque_bas_H - g.plaque_T
def fourche_a(angle):
    # Dans CoudeV1 l'avant-bras part vers +X ; ici 0° = vers -X (à l'opposé du bras), d'où +180°.
    return fourche.translate((-g.axe_X, -g.axe_Y, 0)).rotate((0, 0, 180 + angle)).translate((ax, ay, z0))

fixe = bras + bride + servo_ref
libre = []
for a in range(-180, 181):
    if (fourche_a(a) ^ (bras + bride)).volume() < 1e-6: libre.append(a)
def plage(l):
    if 0 not in l: return None
    lo = hi = 0
    while lo - 1 in l: lo -= 1
    while hi + 1 in l: hi += 1
    return [lo, hi]
r = plage(libre)
rapport = {'methode': 'manifold3d, pas de 1°, fourche pleine (sans trous) contre bras + bride ; servo non compté (il tourne avec, contrôlé dans verify_coude.py)',
           'plage_libre_deg': r, 'marge_plaque_basse_socle_mm': z0 - pb['base_T'],
           'validation_physique': False}
OUT = ICI.parent/'outputs'/'bras_v1'
(OUT/'verification_rotation_coude_bras_V1.json').write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding='utf-8')

def mesh(m):
    a = m.to_mesh(); return tm.Trimesh(vertices=a.vert_properties[:, :3], faces=a.tri_verts, process=True)
fig = plt.figure(figsize=(14, 6)); fig.patch.set_facecolor('#f5f5f2')
for k, ang in enumerate([0, r[1] if r else 90]):
    axp = fig.add_subplot(1, 2, k+1, projection='3d')
    for solide, c in [(bras, '#9ccc8c'), (bride, '#e1a64a'), (servo_ref, '#444444'), (fourche_a(ang), '#397c92')]:
        t = mesh(solide); axp.add_collection3d(Poly3DCollection(t.vertices[t.faces], facecolor=c, edgecolor='#222', linewidth=.06, alpha=.8))
    axp.set(xlim=(-110, 90), ylim=(-70, 130), zlim=(0, 80), title=f'Coude sur bras V1 — avant-bras à {ang}°')
    axp.set_box_aspect((200, 200, 80)); axp.view_init(elev=35, azim=-60)
fig.text(.5, .02, 'Vert : bras · orange : bride · gris : servo · bleu : fourche du coude · Prototype non validé', ha='center')
fig.tight_layout(rect=(0, .05, 1, 1)); fig.savefig(OUT/'apercu_coude_sur_bras_V1.png', dpi=140)
print(json.dumps(rapport, indent=1, ensure_ascii=False))
