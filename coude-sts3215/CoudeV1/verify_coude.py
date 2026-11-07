"""Construction indépendante du coude V1 (sans Fusion) + contrôles.

Lit le même tableau SPECS que CoudeV1.py, construit les deux moitiés avec manifold3d,
vérifie : aucune collision au montage, rotation complète du servo dans la fourche,
pièces fermées et d'un seul volume. Exporte des STL prêts à imprimer (plaque sur le plateau).
"""
from pathlib import Path
import json, ast, math
import numpy as np, trimesh as tm, manifold3d as mf
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ICI = Path(__file__).resolve().parent
OUT = ICI.parent/'outputs'/'coude_v1'; OUT.mkdir(parents=True, exist_ok=True)
tree = ast.parse((ICI/'CoudeV1.py').read_text(encoding='utf-8'))
SPECS = next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SPECS' for t in n.targets))
p = {}
for n, e in SPECS: p[n] = eval(e.replace(' mm', ''), {'__builtins__': {}}, p)
g = type('P', (), p)

def box(x, y, z, l, w, h): return mf.Manifold.cube((l, w, h)).translate((x, y, z))
def cyl(x, y, z, d, h): return mf.Manifold.cylinder(h, d/2, d/2, 96).translate((x, y, z))
def mesh(m):
    a = m.to_mesh(); return tm.Trimesh(vertices=a.vert_properties[:, :3], faces=a.tri_verts, process=True)

def demi(haut):
    zp = g.z_haut if haut else 0
    m = box(g.axe_X, g.pl_y, zp, g.avant_bras_L, g.plaque_W, g.plaque_T) + cyl(g.axe_X, g.axe_Y, zp, 2*g.bout_R, g.plaque_T)
    zb = g.plaque_T + g.demi_H + g.jeu_serrage if haut else g.plaque_T
    for x, l in ((g.axe_X + g.entretoise_A_X, g.entretoise_A_L), (g.axe_X + g.ent_B_X, g.entretoise_B_L)):
        m += box(x, g.pl_y, zb, l, g.plaque_W, g.demi_H)
    zl = g.z_haut + g.plaque_T - g.lamage_P if haut else 0
    for sx in (1, -1):
        for sy in (1, -1):
            x, y = g.axe_X + sx*g.trou_d, g.axe_Y + sy*g.trou_d
            m -= cyl(x, y, zp, g.vis_disque_D, g.plaque_T)
            m -= cyl(x, y, zl, g.lamage_D, g.lamage_P)
    m -= cyl(g.axe_X, g.axe_Y, zp, g.centre_D, g.plaque_T)
    for xc in (g.axe_X + g.entretoise_A_X + g.entretoise_A_L/2, g.axe_X + g.ent_B_X + g.entretoise_B_L/2):
        for sy in (1, -1):
            if haut: m -= cyl(xc, g.axe_Y + sy*g.vis_M3_Y, g.plaque_T + g.demi_H + g.jeu_serrage, g.vis_M3_D, g.demi_H + g.plaque_T)
            else: m -= cyl(xc, g.axe_Y + sy*g.vis_M3_Y, g.plaque_T + g.demi_H - g.insert_P, g.insert_D, g.insert_P)
    return m

def servo(angle_deg):
    """Boîtier + bossage du servo, tourné autour de l'axe du coude (les disques tournent avec la fourche)."""
    z0 = g.plaque_T + g.disque_bas_H
    x0 = g.axe_X - (g.servo_L - g.axe_bout)
    s = box(x0, g.axe_Y - g.servo_W/2, z0, g.servo_L, g.servo_W, g.servo_H)
    s += box(x0 + g.bossage_bord, g.axe_Y - g.bossage_W/2, z0 - g.bossage_H, g.bossage_L, g.bossage_W, g.bossage_H)
    return s.translate((-g.axe_X, -g.axe_Y, 0)).rotate((0, 0, angle_deg)).translate((g.axe_X, g.axe_Y, 0))

def disques():
    return (cyl(g.axe_X, g.axe_Y, g.plaque_T, g.disque_D, g.disque_bas_H)
            + cyl(g.axe_X, g.axe_Y, g.z_haut - g.disque_haut_H, g.disque_D, g.disque_haut_H))

H, B = demi(True), demi(False)
rapport = {'methode': 'manifold3d, memes expressions que CoudeV1.py ; Fusion non execute', 'validation_physique': False,
           'parametres_mm': {k: round(v, 4) for k, v in p.items()}, 'pieces': {}, 'collisions_mm3': {}}
for nom, a, b in [('haute_basse', H, B), ('haute_servo', H, servo(0)), ('basse_servo', B, servo(0)),
                  ('haute_disques', H, disques()), ('basse_disques', B, disques())]:
    vol = (a ^ b).volume(); rapport['collisions_mm3'][nom] = vol; assert abs(vol) < 1e-6, (nom, vol)

# Rotation : le servo tourne de -180 à +180° dans la fourche (en vrai c'est l'inverse, même résultat).
bloque = []
for ang in range(-180, 181, 2):
    s = servo(ang)
    if (H ^ s).volume() > 1e-6 or (B ^ s).volume() > 1e-6: bloque.append(ang)
rapport['rotation'] = {'pas_deg': 2, 'angles_en_collision': bloque, 'tour_complet_libre': not bloque,
                       'rayon_coin_servo_le_plus_loin_mm': math.hypot(g.servo_L - g.axe_bout, g.servo_W/2),
                       'entretoise_A_debut_mm': g.entretoise_A_X}
rapport['marges_mm'] = {'bossage_plaque_basse': g.disque_bas_H - g.bossage_H,
                        'boitier_plaque_haute': g.disque_haut_H, 'boitier_plaque_basse': g.disque_bas_H,
                        'paroi_sous_tete_M2_5': g.plaque_T - g.lamage_P,
                        'longueur_vis_M3_conseillee': g.plaque_T + g.demi_H + g.jeu_serrage + 5}

def compo(t): return len(t.split(only_watertight=False))
for nom, m, retourner in [('fourche_haute_V1', H, True), ('fourche_basse_V1', B, False)]:
    t = mesh(m)
    if retourner: t.apply_transform(tm.transformations.rotation_matrix(math.pi, (1, 0, 0)))
    t.apply_translation(-t.bounds[0])           # plaque sur le plateau, coin en (0,0,0)
    t.export(OUT/(nom + '.stl'))
    t = tm.load_mesh(OUT/(nom + '.stl'))
    d = {'fermee': bool(t.is_watertight), 'orientation_coherente': bool(t.is_winding_consistent), 'volumes': compo(t),
         'encombrement_mm': [round(x, 2) for x in t.extents], 'volume_cm3': round(t.volume/1000, 1)}
    rapport['pieces'][nom] = d
    assert d['fermee'] and d['orientation_coherente'] and d['volumes'] == 1, d
(OUT/'verification_coude_V1.json').write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding='utf-8')

fig = plt.figure(figsize=(13, 6)); fig.patch.set_facecolor('#f5f5f2')
for k, (titre, ang) in enumerate([('Coude V1 — monté, avant-bras dans l\'axe', 0), ('Coude V1 — avant-bras replié à 150°', 150)]):
    ax = fig.add_subplot(1, 2, k+1, projection='3d')
    for solide, couleur in [(B, '#397c92'), (H, '#e1a64a'), (servo(ang), '#444444'), (disques(), '#bbbbbb')]:
        t = mesh(solide)
        ax.add_collection3d(Poly3DCollection(t.vertices[t.faces], facecolor=couleur, edgecolor='#222', linewidth=.08, alpha=.85))
    ax.set(xlim=(0, 170), ylim=(-50, 80), zlim=(-40, 90), xlabel='X · avant-bras (mm)', ylabel='Y', zlabel='Z', title=titre)
    ax.set_box_aspect((170, 130, 130)); ax.view_init(elev=24, azim=-60)
fig.text(.5, .02, 'Orange : moitié haute (palonnier) · bleu : moitié basse (disque libre) · gris : servo · Prototype non validé', ha='center')
fig.tight_layout(rect=(0, .05, 1, 1)); fig.savefig(OUT/'apercu_coude_V1.png', dpi=150)
print(json.dumps({k: rapport[k] for k in ('pieces', 'collisions_mm3', 'rotation', 'marges_mm')}, indent=1, ensure_ascii=False))
