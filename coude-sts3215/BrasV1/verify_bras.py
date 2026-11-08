"""Independent nominal mesh construction and checks; no Fusion API required."""
from pathlib import Path
import json, ast
import numpy as np
import trimesh as tm
import manifold3d as mf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT=Path(__file__).resolve().parent.parent/'outputs'/'bras_v1'
OUT.mkdir(exist_ok=True,parents=True)
def box(x,y,z,l,w,h):return mf.Manifold.cube((l,w,h)).translate((x,y,z))
def cyl(x,y,z,d,h):return mf.Manifold.cylinder(h,d/2,d/2,96).translate((x,y,z))
def mesh(m):
    a=m.to_mesh();return tm.Trimesh(vertices=a.vert_properties[:,:3],faces=a.tri_verts,process=True)
def body_count(t):
    parent=list(range(len(t.vertices)))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for a,b,c in t.faces:
        parent[root(b)]=root(a);parent[root(c)]=root(a)
    return len({root(i) for i in range(len(parent))})

# Read the same expression table as the Fusion script, rather than maintaining duplicate defaults.
tree=ast.parse((Path(__file__).parent/'BrasV1.py').read_text(encoding='utf-8-sig'))
specs=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='specs' for t in n.targets))
def build(overrides=None):
    p={}
    for n,e in specs:p[n]=eval((overrides or {}).get(n,e).replace(' mm',''),{'__builtins__':{}},p)
    globals().update(p)
    b=box(0,0,0,base_L,base_W,base_T)
    for y in (cy-wall_T,cy+cavity_W):b+=box(cx,y,base_T,cavity_L,wall_T,wall_H)
    for x in (cx-wall_T,cx+cavity_L):b+=box(x,cy-wall_T,base_T,wall_T,cavity_W+2*wall_T,wall_H)
    for y in (cy,sy+servo_W-rail_W):b+=box(cx,y,base_T,cavity_L,rail_W+jeu,rail_H)
    b-=box(0,cy-wall_T-1,base_T,sx+cable_x_REF+cable_L_REF+cable_margin,cavity_W+2*wall_T+2,wall_H)
    b+=box(boss_x-nervure_jeu-nervure_T,sy+(servo_W-nervure_W)/2,base_T,nervure_T,nervure_W,rail_H-nervure_jeu)
    for y in (post_y0,post_y1):
        b+=box(brace_x,y,base_T,brace_L,post_W,top_Z-base_T)
        b-=cyl(sx+brace_x_REF,y+post_W/2,top_Z-insert_depth,insert_D,insert_depth)
    for x in (mount_offset,base_L-mount_offset):
        for y in (mount_offset,base_W-mount_offset):b-=cyl(x,y,0,mount_D,base_T)
    brace=box(brace_x,post_y0,top_Z,brace_L,post_y1+post_W-post_y0,brace_T)
    brace+=box(brace_x,sy+2,top_Z-bride_pied_H,brace_L,servo_W-4,bride_pied_H)
    for y in (post_y0,post_y1):brace-=cyl(sx+brace_x_REF,y+post_W/2,top_Z,screw_D,brace_T)
    servo=box(sx,sy,support_Z,servo_L,servo_W,servo_H)+cyl(sx+cyl_offset,base_W/2,support_Z-relief_H,cyl_D,relief_H)+box(boss_x,boss_y,support_Z-relief_H,boss_L,boss_W,relief_H)
    cable=box(sx+cable_x_REF,base_W/2-cable_W_REF/2,support_Z-cable_H_REF,cable_L_REF,cable_W_REF,cable_H_REF)+box(sx+cable_x_REF,2,base_T+1,cable_L_REF,base_W-4,3)
    return p,b,brace,servo,cable

p,b,brace,servo,cable=build()
report={'method':'Independent manifold mesh booleans, from Fusion parameter expressions; Fusion execution recorded separately','parameters_mm':p,'physical_validation':False,'parts':{},'intersection_mm3':{}}
for label,a,c in [('base_servo',b,servo),('base_bride',b,brace),('base_cable',b,cable),('bride_servo',brace,servo),('bride_cable',brace,cable)]:
    vol=(a^c).volume();report['intersection_mm3'][label]=vol;assert abs(vol)<1e-6,(label,vol)
for name,m in [('bras_V1_TEST',b),('bride_bras_V1_1_TEST',brace)]:
    t=mesh(m)
    # Place exported meshes on z=0 for printing. XY retained for faithful assembly alignment.
    zmin=float(t.bounds[0,2])
    if name.startswith('bride'):  # bride V1.1 : dessus sur le plateau, pied vers le haut (pas de surplomb)
        t.apply_transform(tm.transformations.rotation_matrix(np.pi,(1,0,0)))
    t.apply_translation((0,0,-float(t.bounds[0,2])))
    t.export(OUT/(name+'.stl'))
    t=tm.load_mesh(OUT/(name+'.stl'))
    data={'watertight':bool(t.is_watertight),'winding_consistent':bool(t.is_winding_consistent),'connected_bodies':body_count(t),'extents_mm':t.extents.tolist(),'volume_mm3':float(t.volume),'assembly_z_offset_mm':zmin}
    report['parts'][name]=data
    assert t.is_watertight and t.is_winding_consistent and body_count(t)==1 and t.volume>0,data
assert np.allclose(mesh(b).extents[:2],[80,60])
trials=[]
for override in ({'base_L':'82 mm'},{'jeu':'0.3 mm'},{'boss_shift_Y':'0.5 mm'}):
    q,bb,br,ss,cc=build(override)
    vol=(bb^ss).volume();assert abs(vol)<1e-6
    trials.append({'override':override,'base_extents_mm':mesh(bb).extents.tolist(),'cavity_mm':[q['cavity_L'],q['cavity_W']],'servo_intersection_mm3':vol})
report['recompute_trials']=trials
p,b,brace,servo,cable=build()
report['clearances_mm']={'below_reliefs':rail_H-relief_H,'boss_to_rail_centered':(servo_W-boss_W)/2-rail_W,'lateral_per_side':jeu,'below_plug_envelope':rail_H-cable_H_REF,'brace_gap':brace_gap_REF,'insert_wall':(post_W-insert_D)/2}
report['support_area_mm2']=2*rail_W*(servo_L-cable_x_REF-cable_L_REF-cable_margin)
(OUT/'verification_bras_V1.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
fig=plt.figure(figsize=(13,6));fig.patch.set_facecolor('#f5f5f2')
for k,title in enumerate(['Bras V1 — côté axe dégagé, nervure du bossage','Bras V1 — avec la bride V1.1 (pied de 4,1)']):
    ax=fig.add_subplot(1,2,k+1,projection='3d')
    for solid,color,alpha in [(b,'#397c92',1)]+([(brace,'#e1a64a',1)] if k else []):
        t=mesh(solid);coll=Poly3DCollection(t.vertices[t.faces],facecolor=color,edgecolor='#23424b',linewidth=.12,alpha=alpha);ax.add_collection3d(coll)
    ax.set(xlim=(0,80),ylim=(0,60),zlim=(0,55),xlabel='X · longueur (mm)',ylabel='Y (mm)',zlabel='Z (mm)',title=title)
    ax.set_box_aspect((80,60,55));ax.view_init(elev=32,azim=-55)
fig.text(.5,.02,'X− : axe du coude (dégagé)  |  X+ : bossage, bride  •  Prototype, sans validation physique',ha='center')
fig.tight_layout(rect=(0,.05,1,1));fig.savefig(OUT/'apercu_bras_V1.png',dpi=160)
print(json.dumps(report,indent=2))
