import adsk.core, adsk.fusion, math, os, json, traceback
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs', 'servo_cradle_v4_1'))
P = {}
N = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
J = adsk.fusion.FeatureOperations.JoinFeatureOperation
C = adsk.fusion.FeatureOperations.CutFeatureOperation

def val(expr): return adsk.core.ValueInput.createByString(expr)
def point(x,y,z=0): return adsk.core.Point3D.create(x/10,y/10,z/10)
def param(d,n,e,c='Prototype; a valider sur exemplaire'):
    p=d.userParameters.add(n,val(e),'mm',c); P[n]=p.value*10; return p
def v(e):
    return D.unitsManager.evaluateExpression(e,'mm')*10
def plane(comp,z):
    ip=comp.constructionPlanes.createInput(); ip.setByOffset(comp.xYConstructionPlane,val(z)); return comp.constructionPlanes.add(ip)
def sketch(comp,z,name):
    s=comp.sketches.add(comp.xYConstructionPlane if z=='0 mm' else plane(comp,z)); s.name=name; return s
def locate(s,p,x,y):
    origin=s.originPoint; dims=s.sketchDimensions; orient=adsk.fusion.DimensionOrientations
    with open(os.path.join(OUT,'sketch_debug.txt'),'a',encoding='utf-8') as f:
        f.write(str((s.name,x,y,(p.geometry.x,p.geometry.y),p.isFixed,p.isReference,[(c.objectType) for c in p.geometricConstraints]))+'\n')
    if abs(v(x))<1e-8: s.geometricConstraints.addVerticalPoints(origin,p)
    else: dims.addDistanceDimension(origin,p,orient.HorizontalDimensionOrientation,point(v(x)/2,-4)).parameter.expression=x
    if abs(v(y))<1e-8: s.geometricConstraints.addHorizontalPoints(origin,p)
    else: dims.addDistanceDimension(origin,p,orient.VerticalDimensionOrientation,point(-4,v(y)/2)).parameter.expression=y
def rect(s,x,y,w,h):
    a,b,c,d=v(x),v(y),v(w),v(h)
    ls=s.sketchCurves.sketchLines.addTwoPointRectangle(point(a,b),point(a+c,b+d))
    dims=s.sketchDimensions; orient=adsk.fusion.DimensionOrientations
    dims.addDistanceDimension(ls.item(0).startSketchPoint,ls.item(0).endSketchPoint,orient.HorizontalDimensionOrientation,point(a+c/2,b-2)).parameter.expression=w
    dims.addDistanceDimension(ls.item(1).startSketchPoint,ls.item(1).endSketchPoint,orient.VerticalDimensionOrientation,point(a+c+2,b+d/2)).parameter.expression=h
    locate(s,ls.item(0).startSketchPoint,x,y)
    return ls
def circle(s,x,y,diam):
    c=s.sketchCurves.sketchCircles.addByCenterRadius(point(v(x),v(y)),v(diam)/20)
    c.isFixed=False
    c.centerSketchPoint.isFixed=False
    for constraint in list(c.centerSketchPoint.geometricConstraints):
        constraint.deleteMe()
    locate(s,c.centerSketchPoint,x,y)
    s.sketchDimensions.addDiameterDimension(c,point(v(x)+v(diam),v(y)+2)).parameter.expression=diam
    return c
def profiles(s):
    o=adsk.core.ObjectCollection.create()
    for p in s.profiles: o.add(p)
    return o
def largest(s): return max(list(s.profiles),key=lambda p:p.areaProperties().area)
def ext(comp,s,e,op,name,all=False):
    ip=comp.features.extrudeFeatures.createInput(profiles(s) if all else largest(s),op)
    ip.setDistanceExtent(False,val(e)); f=comp.features.extrudeFeatures.add(ip); f.name=name
    if op==N:
        for body in f.bodies: body.name=name
    s.isVisible=False; return f
def component(root,name):
    oc=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); oc.component.name=name; return oc
def box(comp,x,y,w,h,z,t,name,op=N):
    s=sketch(comp,z,name); rect(s,x,y,w,h); return ext(comp,s,t,op,name)
def cylinder(comp,x,y,diam,z,h,name):
    s=sketch(comp,z,name); circle(s,x,y,diam); return ext(comp,s,h,N,name)

def run(context):
    global D
    app=adsk.core.Application.get(); os.makedirs(OUT,exist_ok=True)
    try:
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        D=adsk.fusion.Design.cast(app.activeProduct)
        D.designType=adsk.fusion.DesignTypes.ParametricDesignType
        specs=[('base_L','80 mm'),('base_W','60 mm'),('base_T','5 mm'),
          ('servo_L','45.2 mm'),('servo_W','24.4 mm'),('servo_H','32.9 mm'),
          ('jeu','0.2 mm'),('relief_H','2 mm'),('cyl_D','5.5 mm'),('cyl_offset','8.1 mm'),
          ('boss_L','11.9 mm'),('boss_W','18.3 mm'),('boss_edge','5 mm'),('boss_shift_Y','0 mm'),
          ('rail_H','7 mm'),('rail_W','2 mm'),('wall_T','3 mm'),('wall_H','17 mm'),
          ('cable_x_REF','18 mm'),('cable_L_REF','8 mm'),('cable_W_REF','20 mm'),('cable_H_REF','5 mm'),
          ('cable_margin','1 mm'),('brace_x_REF','33 mm'),('brace_L','8 mm'),('brace_T','4 mm'),
          ('post_W','8 mm'),('screw_D','3.4 mm'),('insert_D','4 mm'),('insert_depth','7 mm'),
          ('brace_gap_REF','1 mm'),('mount_D','4.5 mm'),('mount_offset','8 mm'),
          ('sx','(base_L-servo_L)/2'),('sy','(base_W-servo_W)/2'),
          ('cx','sx-jeu'),('cy','sy-jeu'),('cavity_L','servo_L+2*jeu'),('cavity_W','servo_W+2*jeu'),
          ('support_Z','base_T+rail_H'),('top_Z','support_Z+servo_H+brace_gap_REF'),
          ('boss_x','sx+servo_L-boss_edge-boss_L'),('boss_y','sy+(servo_W-boss_W)/2+boss_shift_Y'),
          ('brace_x','sx+brace_x_REF-brace_L/2'),('post_y0','cy-wall_T-post_W'),('post_y1','cy+cavity_W+wall_T')]
        confirmed={'jeu','cyl_D','cyl_offset','boss_L','boss_W','boss_edge','relief_H'}
        for n,e in specs:
            param(D,n,e,'Mesure utilisateur; orientation bossage d apres photo' if n in confirmed else 'Conception ou reference V2/V3; voir notice V4')
        root=D.rootComponent
        base=component(root,'Berceau_V4_1_TEST'); b=base.component
        box(b,'0 mm','0 mm','base_L','base_W','0 mm','base_T','Socle_80x60')
        for y in ('cy-wall_T','cy+cavity_W'):
            box(b,'cx',y,'cavity_L','wall_T','base_T','wall_H','Guide_lateral',J)
        # End stops both sides; cable exits through the lateral windows.
        for x in ('cx-wall_T','cx+cavity_L'):
            box(b,x,'cy-wall_T','wall_T','cavity_W+2*wall_T','base_T','wall_H','Butee_extremite',J)
        # V4.1 : appuis colles aux parois et aux butees (plus de fente de 0,2 mm non imprimable) ;
        # la partie qui porte le servo reste la bande de rail_W sous son bord.
        for y in ('cy','sy+servo_W-rail_W'):
            box(b,'cx',y,'cavity_L','rail_W+jeu','base_T','rail_H','Appui_plan_lateral',J)
        # Full width window removes both rails and both guides locally.
        box(b,'sx+cable_x_REF-cable_margin','cy-wall_T-1 mm','cable_L_REF+2*cable_margin','cavity_W+2*wall_T+2 mm','base_T','wall_H','Sorties_cables_deux_cotes',C)
        for y in ('post_y0','post_y1'):
            box(b,'brace_x',y,'brace_L','post_W','base_T','top_Z-base_T','Colonne_bride',J)
            # V4.1 : insert filete M3 pose a chaud en haut de colonne, vis courte M3x10.
            s=sketch(b,'top_Z-insert_depth','Logement_insert_M3');circle(s,'sx+brace_x_REF',y+'+post_W/2','insert_D');ext(b,s,'insert_depth',C,'Logement_insert_M3')
        for x in ('mount_offset','base_L-mount_offset'):
            for y in ('mount_offset','base_W-mount_offset'):
                s=sketch(b,'0 mm','Fixation_socle');circle(s,x,y,'mount_D');ext(b,s,'base_T',C,'Trou_fixation')
        brace=component(root,'Bride_V4_1_TEST');bc=brace.component
        box(bc,'brace_x','post_y0','brace_L','post_y1+post_W-post_y0','top_Z','brace_T','Bride_demontable')
        for y in ('post_y0','post_y1'):
            s=sketch(bc,'top_Z','Vis_bride');circle(s,'sx+brace_x_REF',y+'+post_W/2','screw_D');ext(bc,s,'brace_T',C,'Passage_M3_bride')
        servo=component(root,'Servo_REFERENCE_non_imprimable');sc=servo.component
        box(sc,'sx','sy','servo_L','servo_W','support_Z','servo_H','Boitier_REFERENCE')
        cylinder(sc,'sx+cyl_offset','base_W/2','cyl_D','support_Z-relief_H','relief_H','Cylindre_mesure')
        box(sc,'boss_x','boss_y','boss_L','boss_W','support_Z-relief_H','relief_H','Bossage_mesure_centrage_ESTIME')
        cable=component(root,'Connecteurs_REFERENCE_ESTIMEE');cc=cable.component
        box(cc,'sx+cable_x_REF','base_W/2-cable_W_REF/2','cable_L_REF','cable_W_REF','support_Z-cable_H_REF','cable_H_REF','Fiches_ENVELOPPE_ESTIMEE')
        box(cc,'sx+cable_x_REF','2 mm','cable_L_REF','base_W-4 mm','base_T+1 mm','3 mm','Cable_ENVELOPPE_ESTIMEE')
        D.computeAll()
        report={'status':'PROTOTYPE_DIMENSIONNEL_NON_VALIDE_PHYSIQUEMENT','parameters_mm':{p.name:p.value*10 for p in D.userParameters},'orientation':'X=longueur; X- cylindre; X+ bossage; bossage 11.9 selon X et18.3 selon Y; Z+ vers dessus servo','relief_floor_gap_mm':v('rail_H-relief_H'),'boss_to_rail_gap_mm':v('(servo_W-boss_W)/2-rail_W'),'cavity_mm':[v('cavity_L'),v('cavity_W')],'support_area_mm2':2*v('rail_W')*v('servo_L-cable_L_REF-2*cable_margin'),'brace_gap_mm':v('brace_gap_REF'),'insert_hole':{'diameter_mm':v('insert_D'),'depth_mm':v('insert_depth'),'wall_left_in_post_mm':v('(post_W-insert_D)/2')}}
        # Exercise size AND fit parameters, then restore nominal design.
        trials=[]
        for name,expr in [('base_L','82 mm'),('jeu','0.3 mm')]:
            p=D.userParameters.itemByName(name); old=p.expression;p.expression=expr;D.computeAll()
            bb=b.bRepBodies.item(0).boundingBox
            trials.append({'parameter':name,'value':expr,'body_length_mm':(bb.maxPoint.x-bb.minPoint.x)*10,'cavity_L_mm':v('cavity_L')})
            p.expression=old;D.computeAll()
        assert abs(trials[0]['body_length_mm']-82)<0.001
        assert abs(trials[1]['cavity_L_mm']-45.8)<0.001
        report['recompute_trials']=trials
        report['feature_warnings']=[{'feature':f.name,'message':f.errorOrWarningMessage} for oc in root.occurrences for f in oc.component.features if f.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
        # Only pair printable parts against references: reference cable overlaps its plug intentionally.
        checks=[]
        for a,z in [(base,brace),(base,servo),(base,cable),(brace,servo),(brace,cable)]:
            for ba in a.component.bRepBodies:
                for bz in z.component.bRepBodies:
                    objs=adsk.core.ObjectCollection.create()
                    objs.add(ba.createForAssemblyContext(a));objs.add(bz.createForAssemblyContext(z))
                    ii=D.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False
                    result=D.analyzeInterference(ii)
                    if result is None: raise RuntimeError('Analyse interference indisponible')
                    for hit in result:
                        checks.append({'a':hit.entityOne.name,'b':hit.entityTwo.name,'volume_mm3':hit.interferenceBody.volume*1000})
        report['interferences']=checks
        report['solid_counts']={oc.component.name:oc.component.bRepBodies.count for oc in (base,brace)}
        assert not report['feature_warnings'],report['feature_warnings']
        assert not checks,checks
        assert b.bRepBodies.count==1 and bc.bRepBodies.count==1
        assert v('rail_H-relief_H')>0 and v('(servo_W-boss_W)/2-rail_W')>0
        for oc,filename in [(base,'berceau_V4_1_TEST.stl'),(brace,'bride_V4_1_TEST.stl')]:
            opt=D.exportManager.createSTLExportOptions(oc.component.bRepBodies.item(0),os.path.join(OUT,filename));opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            assert D.exportManager.execute(opt)
        servo.isLightBulbOn=False;cable.isLightBulbOn=False
        app.activeViewport.fit();app.activeViewport.saveAsImageFile(os.path.join(OUT,'V4_1_support_bride.png'),1600,1000)
        brace.isLightBulbOn=False
        app.activeViewport.fit();app.activeViewport.saveAsImageFile(os.path.join(OUT,'V4_1_appuis.png'),1600,1000)
        brace.isLightBulbOn=True
        assert D.exportManager.execute(D.exportManager.createFusionArchiveExportOptions(os.path.join(OUT,'STS3215_berceau_V4_1_parametrique.f3d')))
        with open(os.path.join(OUT,'verification_V4_1.json'),'w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
        app.userInterface.messageBox('V4.1 generee et exportee. Prototype dimensionnel: consulter la notice avant essai.\n'+OUT)
    except:
        with open(os.path.join(OUT,'error.txt'),'w',encoding='utf-8') as f:f.write(traceback.format_exc())
        app.userInterface.messageBox(traceback.format_exc())

def stop(context): pass



