"""Coude STS3215 V1.1 (écart entre disques mesuré : 36,4 au lieu de 40,2 calculé) : fourche d'avant-bras en deux moitiés (haute / basse).

Chaque moitié se visse sur un disque du servo (palonnier en haut, disque libre en bas),
puis les deux moitiés se serrent l'une sur l'autre par des entretoises vissées (M3 + inserts).
Repère : X = direction de l'avant-bras, axe du coude vertical (Z) en (axe_X, axe_Y).
Z = 0 sous la plaque basse. Prototype : aucune validation physique.
"""
import adsk.core, adsk.fusion, os, json, traceback
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs', 'coude_v1_1'))
P = {}
N = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
J = adsk.fusion.FeatureOperations.JoinFeatureOperation
C = adsk.fusion.FeatureOperations.CutFeatureOperation

# Paramètres : (nom, expression). Les mesures viennent du servo de Nicolas (07/11/2026).
SPECS = [
    # Servo (mesures)
    # V1.1 : l'écart entre les faces extérieures des deux disques est MESURÉ (08/11/2026).
    # La V1 l'additionnait (3 + 32,9 + 4,3 = 40,2) : 3,8 mm de trop, plaques pincées en V.
    ('ecart_mesure', '36.4 mm'),
    ('servo_L', '45.2 mm'), ('servo_W', '24.4 mm'),
    ('axe_bout', '8.1 mm'),          # centre palonnier / cylindre depuis le petit côté
    ('disque_D', '19.7 mm'),
    ('disque_haut_H', '4.3 mm'),     # palonnier au-dessus du boîtier
    ('disque_bas_H', '3 mm'),        # disque libre sous le boîtier
    ('servo_H', 'ecart_mesure-disque_haut_H-disque_bas_H'),  # DÉDUIT (29,1) : hauteur du boîtier à mesurer
    ('cercle_trous', '13.45 mm'),    # diamètre du cercle des 4 trous M2,5 des disques
    ('bossage_H', '2 mm'), ('bossage_L', '11.9 mm'), ('bossage_W', '18.3 mm'), ('bossage_bord', '5 mm'),
    # Fourche (choix de conception)
    ('avant_bras_L', '120 mm'),      # de l'axe du coude au bout de l'avant-bras
    ('plaque_W', '24 mm'), ('plaque_T', '4 mm'), ('bout_R', '12 mm'),
    ('vis_disque_D', '2.9 mm'),      # passage M2,5
    ('lamage_D', '5.2 mm'), ('lamage_P', '1.5 mm'),   # logement des têtes M2,5
    ('centre_D', '7 mm'),            # dégagement de la vis centrale des disques
    ('entretoise_A_X', '50 mm'), ('entretoise_A_L', '12 mm'),  # > 39,1 = rayon du coin le plus loin du servo
    ('entretoise_B_L', '15 mm'),
    ('jeu_serrage', '0.4 mm'),       # écart entre les deux demi-entretoises, fermé au serrage
    ('vis_M3_D', '3.4 mm'), ('vis_M3_Y', '6 mm'),
    ('insert_D', '4 mm'), ('insert_P', '9 mm'),   # V1.1 : 9 pour que la vis M3 x 30 ne touche pas le fond
    ('axe_X', '40 mm'), ('axe_Y', '15 mm'),
    # Dérivés
    ('ecart', 'ecart_mesure'),
    ('demi_H', '(ecart-jeu_serrage)/2'),
    ('z_haut', 'plaque_T+ecart'),
    ('trou_d', 'cercle_trous/2*0.70710678'),
    ('pl_y', 'axe_Y-plaque_W/2'),
    ('ent_B_X', 'avant_bras_L-entretoise_B_L'),
]

def val(expr): return adsk.core.ValueInput.createByString(expr)
def point(x, y, z=0): return adsk.core.Point3D.create(x/10, y/10, z/10)
def v(e): return D.unitsManager.evaluateExpression(e, 'mm')*10
def plane(comp, z):
    ip = comp.constructionPlanes.createInput(); ip.setByOffset(comp.xYConstructionPlane, val(z)); return comp.constructionPlanes.add(ip)
def sketch(comp, z, name):
    s = comp.sketches.add(comp.xYConstructionPlane if z == '0 mm' else plane(comp, z)); s.name = name; return s
def locate(s, p, x, y):
    origin = s.originPoint; dims = s.sketchDimensions; orient = adsk.fusion.DimensionOrientations
    if abs(v(x)) < 1e-8: s.geometricConstraints.addVerticalPoints(origin, p)
    else: dims.addDistanceDimension(origin, p, orient.HorizontalDimensionOrientation, point(v(x)/2, -4)).parameter.expression = x
    if abs(v(y)) < 1e-8: s.geometricConstraints.addHorizontalPoints(origin, p)
    else: dims.addDistanceDimension(origin, p, orient.VerticalDimensionOrientation, point(-4, v(y)/2)).parameter.expression = y
def rect(s, x, y, w, h):
    a, b, c, d = v(x), v(y), v(w), v(h)
    ls = s.sketchCurves.sketchLines.addTwoPointRectangle(point(a, b), point(a+c, b+d))
    dims = s.sketchDimensions; orient = adsk.fusion.DimensionOrientations
    dims.addDistanceDimension(ls.item(0).startSketchPoint, ls.item(0).endSketchPoint, orient.HorizontalDimensionOrientation, point(a+c/2, b-2)).parameter.expression = w
    dims.addDistanceDimension(ls.item(1).startSketchPoint, ls.item(1).endSketchPoint, orient.VerticalDimensionOrientation, point(a+c+2, b+d/2)).parameter.expression = h
    locate(s, ls.item(0).startSketchPoint, x, y)
    return ls
def circle(s, x, y, diam):
    c = s.sketchCurves.sketchCircles.addByCenterRadius(point(v(x), v(y)), v(diam)/20)
    c.isFixed = False; c.centerSketchPoint.isFixed = False
    for constraint in list(c.centerSketchPoint.geometricConstraints): constraint.deleteMe()
    locate(s, c.centerSketchPoint, x, y)
    s.sketchDimensions.addDiameterDimension(c, point(v(x)+v(diam), v(y)+2)).parameter.expression = diam
    return c
def largest(s): return max(list(s.profiles), key=lambda p: p.areaProperties().area)
def ext(comp, s, e, op, name):
    ip = comp.features.extrudeFeatures.createInput(largest(s), op)
    ip.setDistanceExtent(False, val(e)); f = comp.features.extrudeFeatures.add(ip); f.name = name
    if op == N:
        for body in f.bodies: body.name = name
    s.isVisible = False; return f
def component(root, name):
    oc = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); oc.component.name = name; return oc
def box(comp, x, y, w, h, z, t, name, op=N):
    s = sketch(comp, z, name); rect(s, x, y, w, h); return ext(comp, s, t, op, name)
def cyl(comp, x, y, diam, z, h, name, op=N):
    s = sketch(comp, z, name); circle(s, x, y, diam); return ext(comp, s, h, op, name)

def demi_fourche(comp, haut):
    """Une moitié : plaque + demi-entretoises + trous. haut=True : moitié du palonnier."""
    zp = 'z_haut' if haut else '0 mm'                     # dessous de la plaque
    box(comp, 'axe_X', 'pl_y', 'avant_bras_L', 'plaque_W', zp, 'plaque_T', 'Plaque')
    cyl(comp, 'axe_X', 'axe_Y', '2*bout_R', zp, 'plaque_T', 'Bout_rond', J)
    zb = 'plaque_T+demi_H+jeu_serrage' if haut else 'plaque_T'
    for x, l, n in (('axe_X+entretoise_A_X', 'entretoise_A_L', 'Entretoise_A'), ('axe_X+ent_B_X', 'entretoise_B_L', 'Entretoise_B')):
        box(comp, x, 'pl_y', l, 'plaque_W', zb, 'demi_H', n, J)
    # Trous des disques (4 x M2,5 à 45°) + lamage côté extérieur + dégagement central
    zl = 'z_haut+plaque_T-lamage_P' if haut else '0 mm'
    for sx in ('+', '-'):
        for sy in ('+', '-'):
            x, y = 'axe_X' + sx + 'trou_d', 'axe_Y' + sy + 'trou_d'
            cyl(comp, x, y, 'vis_disque_D', zp, 'plaque_T', 'Trou_M2_5', C)
            cyl(comp, x, y, 'lamage_D', zl, 'lamage_P', 'Lamage_M2_5', C)
    cyl(comp, 'axe_X', 'axe_Y', 'centre_D', zp, 'plaque_T', 'Degagement_centre', C)
    # Vis M3 des entretoises : passage en haut, insert en bas
    for xc in ('axe_X+entretoise_A_X+entretoise_A_L/2', 'axe_X+ent_B_X+entretoise_B_L/2'):
        for sy in ('+', '-'):
            if haut:
                cyl(comp, xc, 'axe_Y' + sy + 'vis_M3_Y', 'vis_M3_D', 'plaque_T+demi_H+jeu_serrage', 'demi_H+plaque_T', 'Passage_M3', C)
            else:
                cyl(comp, xc, 'axe_Y' + sy + 'vis_M3_Y', 'insert_D', 'plaque_T+demi_H-insert_P', 'insert_P', 'Insert_M3', C)

def run(context):
    global D
    app = adsk.core.Application.get(); os.makedirs(OUT, exist_ok=True)
    try:
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        D = adsk.fusion.Design.cast(app.activeProduct)
        D.designType = adsk.fusion.DesignTypes.ParametricDesignType
        for n, e in SPECS:
            p = D.userParameters.add(n, val(e), 'mm', 'Coude V1.1 ; prototype a valider'); P[n] = p.value*10
        root = D.rootComponent
        haut = component(root, 'Fourche_haute_V1_1'); demi_fourche(haut.component, True)
        bas = component(root, 'Fourche_basse_V1_1'); demi_fourche(bas.component, False)
        servo = component(root, 'Servo_REFERENCE_non_imprimable'); sc = servo.component
        box(sc, 'axe_X-(servo_L-axe_bout)', 'axe_Y-servo_W/2', 'servo_L', 'servo_W', 'plaque_T+disque_bas_H', 'servo_H', 'Boitier_REFERENCE')
        box(sc, 'axe_X-(servo_L-axe_bout)+bossage_bord', 'axe_Y-bossage_W/2', 'bossage_L', 'bossage_W', 'plaque_T+disque_bas_H-bossage_H', 'bossage_H', 'Bossage_REFERENCE')
        D.computeAll()
        report = {'status': 'PROTOTYPE_NON_VALIDE_PHYSIQUEMENT', 'parameters_mm': {p.name: p.value*10 for p in D.userParameters}}
        report['feature_warnings'] = [{'feature': f.name, 'message': f.errorOrWarningMessage} for oc in root.occurrences for f in oc.component.features if f.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
        checks = []
        for a, z in [(haut, bas), (haut, servo), (bas, servo)]:
            for ba in a.component.bRepBodies:
                for bz in z.component.bRepBodies:
                    objs = adsk.core.ObjectCollection.create()
                    objs.add(ba.createForAssemblyContext(a)); objs.add(bz.createForAssemblyContext(z))
                    ii = D.createInterferenceInput(objs); ii.areCoincidentFacesIncluded = False
                    result = D.analyzeInterference(ii)
                    if result is None: raise RuntimeError('Analyse interference indisponible')
                    for hit in result:
                        checks.append({'a': hit.entityOne.name, 'b': hit.entityTwo.name, 'volume_mm3': hit.interferenceBody.volume*1000})
        report['interferences'] = checks
        report['solid_counts'] = {oc.component.name: oc.component.bRepBodies.count for oc in (haut, bas)}
        assert not report['feature_warnings'], report['feature_warnings']
        assert not checks, checks
        assert haut.component.bRepBodies.count == 1 and bas.component.bRepBodies.count == 1, report['solid_counts']
        for oc, filename in [(haut, 'fourche_haute_V1_1.stl'), (bas, 'fourche_basse_V1_1.stl')]:
            opt = D.exportManager.createSTLExportOptions(oc.component.bRepBodies.item(0), os.path.join(OUT, filename))
            opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            assert D.exportManager.execute(opt)
        assert D.exportManager.execute(D.exportManager.createFusionArchiveExportOptions(os.path.join(OUT, 'Coude_STS3215_V1_1_parametrique.f3d')))
        with open(os.path.join(OUT, 'verification_fusion_coude_V1_1.json'), 'w', encoding='utf-8') as f: json.dump(report, f, ensure_ascii=False, indent=2)
        app.userInterface.messageBox('Coude V1.1 genere et exporte. Prototype : lire la notice avant essai.\n' + OUT)
    except:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, 'error.txt'), 'w', encoding='utf-8') as f: f.write(traceback.format_exc())
        app.userInterface.messageBox(traceback.format_exc())

def stop(context): pass
