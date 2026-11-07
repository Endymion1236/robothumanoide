from pathlib import Path
import json
import numpy as np
import trimesh as tm
OUT=Path(__file__).resolve().parent.parent/'outputs'/'servo_cradle_v4_1'
def components(t):
    p=list(range(len(t.vertices)))
    def root(i):
        while p[i]!=i:p[i]=p[p[i]];i=p[i]
        return i
    for a,b,c in t.faces:p[root(b)]=root(a);p[root(c)]=root(a)
    return len({root(i) for i in range(len(p))})
r={}
ref=json.loads((OUT/'verification_maillage_V4_1.json').read_text())
for n,expected in [('berceau_V4_1_TEST',[80,60,45.9]),('bride_V4_1_TEST',[8,46.8,4])]:
    m=tm.load_mesh(OUT/(n+'.stl'))
    r[n]={'watertight':bool(m.is_watertight),'consistent_winding':bool(m.is_winding_consistent),'connected_bodies':components(m),'bounds_mm':m.bounds.tolist(),'volume_mm3':float(m.volume),'extents_mm':m.extents.tolist()}
    assert m.is_watertight and m.is_winding_consistent and components(m)==1
    assert np.allclose(m.extents,expected,atol=.001),r[n]
    r[n]['relative_volume_difference_to_independent_model']=abs(m.volume-ref['parts'][n]['volume_mm3'])/m.volume
    assert r[n]['relative_volume_difference_to_independent_model']<.001
f=json.loads((OUT/'verification_V4_1.json').read_text(encoding='utf-8'))
assert not f['feature_warnings'] and not f['interferences']
assert (OUT/'STS3215_berceau_V4_1_parametrique.f3d').stat().st_size>10000
(OUT/'verification_STL_Fusion.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2))
