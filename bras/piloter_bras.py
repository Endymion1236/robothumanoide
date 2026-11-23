"""Piloter le bras entier : épaule (n° 2), coude (n° 1), pince (n° 4), sur le même câble.

Avant : tester_epaule.bat (étalonnage de l'épaule), tester_coude.bat et tester_pince.bat au moins une fois.
Au premier lancement, le programme apprend le sens du coude, à la main, sans moteur.

Angles : épaule = angle du haut du bras par rapport à l'horizontale (−30° à +90°) ;
         coude  = angle de l'avant-bras par rapport au haut du bras (0° = dans le prolongement, + = il remonte).
Commandes (plusieurs à la suite, séparées par des espaces) :
  e30   épaule à +30°            c-45  coude à −45°           plat  avant-bras remis à l'horizontale
  n20   épaule à +20° en gardant l'avant-bras à l'horizontale (les deux servos bougent ensemble)
  o     ouvrir la pince          s / S serrer doucement / plus fort
  poser descend lentement, avant-bras à l'horizontale, jusqu'à sentir la table, ouvre la pince et remonte
  t45   socle tourné à +45° (de −90 à +90 ; seulement si le socle est monté : servo n° 1, coude au n° 3)
  repos bras à la verticale      i     infos                  q     quitter
Sécurités : butées de chaque servo, chaleur, blocage (le servo RETIENT le bras au lieu de le lâcher), et refus
d'un geste qui enverrait la pince dans la table. Avec le socle tournant : ajouter --hauteur 179."""
import argparse, json, math, re, sys, time
from pathlib import Path
from servos import numero_coude, numero_socle
from servos import Bus, ErreurServo, degres, pas, TEMP_MAX, CHARGE_MAX, VITESSE_DOUCE, ACCEL_DOUCE, SMS_STS_MOVING
import test_epaule as E, test_pince as P

MILIEU = 2048
ID_EPAULE, ID_COUDE, ID_PINCE = 2, 1, 4
BUTEES_COUDE = (908, 3188); COUDE_MAX = 90
# Socle : angle POSITIF = le bras part À DROITE quand on est DERRIÈRE lui : c'est la droite du robot (constaté par Nicolas le 20/11/2026). Vu de face, c'est donc à gauche.
BUTEES_SOCLE = (1024, 3072); SOCLE_MAX = 90           # un quart de tour de chaque côté            # ± 90° utilisés (vérifiés sans contact dans epaule/verifier_epaule.py)
L_BRAS, L_AVANT, SOUS_PINCE = 120.0, 230.0, 40.0       # épaule→coude, coude→milieu des mâchoires, bas des mâchoires sous l'axe (mm)
# Poignet : angle POSITIF = le haut de la pince part À GAUCHE, vu de derrière le bras (constaté par Nicolas le 21/11/2026).
ID_POIGNET, BUTEES_POIGNET, POIGNET_MAX = 5, (1024, 3072), 90
ALLONGE_POIGNET, SOUS_PINCE_POIGNET = 48.7, 60.0      # la rotation du poignet allonge le bras de 48,7 mm ; pince tournée, son point le plus bas est à 60 mm sous l'axe
# Flexion du poignet (servo n° 6) : son axe est à 161 mm du coude (avant-bras de 120 + 41) ; de cet axe au milieu des mâchoires :
# 42 (fourche) + 110 (pince), plus 48,7 si la rotation est montée. Angle positif = la pince remonte.
ID_FLEXION, BUTEES_FLEXION, FLEXION_MAX = 6, (1024, 3072), 90
L_COUDE_FLEXION, L_FLEXION_PINCE, BOUT_MACHOIRES = 161.0, 152.0, 30.0
FLEXION, L_APRES_FLEXION = False, 152.0
def regler_longueurs(trouves):
    """Avec le poignet (servos n° 5 et 6), le bras est plus long : la sécurité « la pince irait dans la table » doit le savoir.
    Renvoie True si la rotation (n° 5) est montée ; la variable FLEXION dit si la flexion (n° 6) l'est."""
    global L_AVANT, SOUS_PINCE, FLEXION, L_APRES_FLEXION
    poignet = ID_POIGNET in trouves; FLEXION = ID_FLEXION in trouves
    SOUS_PINCE = SOUS_PINCE_POIGNET if poignet else 40.0
    L_APRES_FLEXION = L_FLEXION_PINCE + (ALLONGE_POIGNET if poignet else 0.0)
    L_AVANT = L_COUDE_FLEXION + L_APRES_FLEXION if FLEXION else 230.0 + (ALLONGE_POIGNET if poignet else 0.0)
    return poignet
SENS_COUDE = Path(__file__).with_name('sens_coude.json')
TOL = E.TOLERANCE
SEUIL_CONTACT = 10          # points de charge : variation qui signale que le verre touche la table (à ajuster à l'essai)

def bas_de_pince(h, a, g, f=0.0):
    """Hauteur du point le plus bas de la pince au-dessus de la table (mm), pour épaule a, coude g et flexion du poignet f (degrés)."""
    if not FLEXION: return h + L_BRAS * math.sin(math.radians(a)) + L_AVANT * math.sin(math.radians(a + g)) - SOUS_PINCE
    t = math.radians(a + g + f)                        # inclinaison de la pince ; penchée, le bout des mâchoires descend plus bas que leur milieu
    return h + L_BRAS * math.sin(math.radians(a)) + L_COUDE_FLEXION * math.sin(math.radians(a + g)) + L_APRES_FLEXION * math.sin(t) - SOUS_PINCE - BOUT_MACHOIRES * abs(math.sin(t))

def apprendre_sens_coude(bus):
    print('\n--- Sens du coude (le moteur ne bouge pas) ---')
    input('TIENS l\'avant-bras d\'une main (la force du coude va être coupée), puis Entrée... ')
    bus.relacher(ID_COUDE)
    while True:
        avant = bus.etat(ID_COUDE)['position']
        input('PLIE le coude pour que l\'avant-bras REMONTE d\'environ 20° (la pince monte), garde-le là, puis Entrée... ')
        ecart = bus.etat(ID_COUDE)['position'] - avant
        if abs(ecart) >= pas(10): break
        print(f'   il n\'a presque pas bougé ({degres(ecart):+.0f}°). Recommence franchement.')
    sens = 1 if ecart > 0 else -1
    SENS_COUDE.write_text(json.dumps({'haut': sens}), encoding='utf-8')
    bus.retenir(ID_COUDE)
    print(f"   compris : quand l'avant-bras remonte, la position du coude {'augmente' if sens > 0 else 'diminue'}. Le coude tient : tu peux lâcher doucement.")
    return sens

def aller_ensemble(bus, cibles, delai_max=14.0, synchro=False, vitesse=None, accel=None, arret=None):
    """Envoie plusieurs servos à leur cible EN MÊME TEMPS (même vitesse) et les surveille. Renvoie un compte rendu.
    synchro : les servos doivent avancer ENSEMBLE (geste « n » : l'avant-bras reste à l'horizontale). Si l'un prend
    plus de 80 pas (7°) de retard sur l'autre, tout s'arrête : sinon le coude continuerait seul et pencherait la pince."""
    depart = {i: bus.etat(i)['position'] for i, _ in cibles}
    for i, c in cibles:
        e = bus.etat(i)
        if not e['butee_min'] <= c <= e['butee_max']: raise ErreurServo(f"servo n° {i} : cible {c} hors des butées {e['butee_min']}–{e['butee_max']}")
        if bus.trop_chaud(i, e): raise ErreurServo(f"servo n° {i} trop chaud ({e['temperature']} °C)")
    for i, c in cibles:
        res, err = bus.p.WritePosEx(i, c, vitesse or VITESSE_DOUCE, accel or ACCEL_DOUCE); bus._ok(res, err, 'ordre de position')
    if vitesse: delai_max *= max(1.0, VITESSE_DOUCE / vitesse)          # plus lent : plus de temps laissé
    debut = time.time(); suivi = {i: {'avant': None, 'immobile': None, 'effort': None, 'fini': False} for i, _ in cibles}
    def stop(cause):
        for i, _ in cibles: bus.retenir(i, 40)
        return f'ARRÊT : {cause}. Les servos RETIENNENT le bras sur place (force réduite à 40 %).'
    while True:
        time.sleep(0.1)
        if arret and arret(): return stop('arrêt demandé')
        for i, c in cibles:
            e, s = bus.etat(i), suivi[i]
            if bus.trop_chaud(i, e): return stop(f"servo n° {i} trop chaud ({e['temperature']} °C)")
            if abs(e['charge']) >= CHARGE_MAX:
                s['effort'] = s['effort'] or time.time()
                if time.time() - s['effort'] > 0.5: return stop(f"le servo n° {i} force ({e['charge']:.0f} %)")
            else: s['effort'] = None
            loin = abs(e['position'] - c) > TOL
            if s['avant'] is not None and abs(e['position'] - s['avant']) <= 2:
                s['immobile'] = s['immobile'] or time.time()
                if loin and time.time() - s['immobile'] > 0.7: return stop(f"le servo n° {i} n'avance plus (position {e['position']}, charge {e['charge']:.0f} %)")
            else: s['immobile'] = None
            s['avant'] = e['position']
            arrete = s['immobile'] is not None and time.time() - s['immobile'] > 0.3      # immobile près de la cible : arrivé, même si le servo pousse encore (verre sur la table)
            s['fini'] = not loin and (arrete or not bus.lire1(i, SMS_STS_MOVING, 'en mouvement')); s['fait'] = abs(e['position'] - depart[i])
        if synchro:
            faits = [s.get('fait', 0) for s in suivi.values()]
            if max(faits) - min(faits) > 80: return stop(f'les servos n\'avancent plus ensemble (écart de {degres(max(faits) - min(faits)):.0f}°)')
        if all(s['fini'] for s in suivi.values()): return f'arrivé en {time.time() - debut:.1f} s'
        if time.time() - debut > delai_max: return stop(f"pas arrivé en {delai_max:.0f} s")

def main():
    ap = argparse.ArgumentParser(description='Piloter le bras : épaule, coude, pince')
    ap.add_argument('--maintien', type=int, default=P.FORCE_MAINTIEN, help='force gardée une fois l\'objet saisi, en %% (0 = pas de baisse)')
    ap.add_argument('--port'); ap.add_argument('--hauteur', type=float, default=None, help='hauteur de l\'axe de l\'épaule au-dessus de la table (101 ; 179 avec le socle)')
    a = ap.parse_args()
    try: bus = Bus(a.port)
    except ErreurServo as e: sys.exit(str(e))
    tenus = []
    global ID_COUDE
    try:
        trouves = bus.chercher(); print('Servos trouvés :', trouves or 'aucun')
        ID_COUDE, socle = numero_coude(trouves), numero_socle(trouves)
        if a.hauteur is None: a.hauteur = 179.0 if socle else 101.0
        poignet = regler_longueurs(trouves)
        sf, ang_f = 1, (lambda: 0.0)
        if FLEXION:
            import test_flexion as TF
            ef = bus.etat(ID_FLEXION)
            if (ef['butee_min'], ef['butee_max']) != BUTEES_FLEXION or not TF.SENS.exists(): sys.exit('Flexion du poignet pas étalonnée : lancer tester_flexion.bat')
            sf = json.loads(TF.SENS.read_text(encoding='utf-8'))['haut']; ang_f = lambda: degres(bus.etat(ID_FLEXION)['position'] - MILIEU) * sf
            bus.limiter_force(ID_FLEXION, 100); bus.retenir(ID_FLEXION); tenus.append(ID_FLEXION)
            print('Flexion du poignet : n° 6, tenue. Commande : f30 = pince relevée de 30° (de −90 à +90).')
        if poignet:
            ew = bus.etat(ID_POIGNET)
            if (ew['butee_min'], ew['butee_max']) != BUTEES_POIGNET or not Path(__file__).with_name('poignet_etalonne.json').exists(): sys.exit('Poignet pas étalonné : lancer tester_poignet.bat')
            bus.limiter_force(ID_POIGNET, 50); bus.retenir(ID_POIGNET)
            print(f'Poignet (rotation) : n° 5 · bras compté plus long de {ALLONGE_POIGNET} mm. Commande : p45 = pince tournée de 45° (de −90 à +90).')
        print(f"Coude : n° {ID_COUDE} · socle tournant : {'n° 1' if socle else 'pas monté'} · axe de l'épaule à {a.hauteur:.0f} mm de la table")
        for i, nom in ((ID_EPAULE, 'épaule'), (ID_COUDE, 'coude'), (ID_PINCE, 'pince')):
            if i not in trouves: sys.exit(f'Servo n° {i} ({nom}) introuvable : vérifier les câbles.')
        if not E.SENS.exists(): sys.exit('Épaule pas encore étalonnée : lancer d\'abord tester_epaule.bat --coude 1')
        haut = json.loads(E.SENS.read_text(encoding='utf-8'))['haut']
        ee, ec, ep = bus.etat(ID_EPAULE), bus.etat(ID_COUDE), bus.etat(ID_PINCE)
        if (ee['butee_min'], ee['butee_max']) != E.butees(haut): sys.exit('Butées de l\'épaule différentes : relancer tester_epaule.bat --coude 1 (étalonnage).')
        if (ec['butee_min'], ec['butee_max']) != BUTEES_COUDE: sys.exit('Butées du coude pas réglées : lancer tester_coude.bat')
        if socle:
            es = bus.etat(socle)
            if (es['butee_min'], es['butee_max']) != BUTEES_SOCLE: sys.exit('Butées du socle pas réglées (1024–3072) : lancer tester_socle.bat')
            bus.limiter_force(socle, 100); bus.retenir(socle)
        if (ep['butee_min'], ep['butee_max']) != P.BUTEES_PINCE or not P.SENS.exists(): sys.exit('Pince pas réglée : lancer tester_pince.bat')
        ouvert = json.loads(P.SENS.read_text())['ouvert']; ferme = sum(P.BUTEES_PINCE) - ouvert
        for i in (ID_EPAULE, ID_COUDE):
            bus.limiter_force(i, 100); bus.retenir(i); tenus.append(i)
        print('L\'épaule et le coude tiennent le bras là où il est.')
        sc = json.loads(SENS_COUDE.read_text(encoding='utf-8'))['haut'] if SENS_COUDE.exists() else apprendre_sens_coude(bus)
        ang_e = lambda: E.angle(bus.etat(ID_EPAULE)['position'], haut)
        ang_c = lambda: degres(bus.etat(ID_COUDE)['position'] - MILIEU) * sc
        pos_e = lambda x: E.position(x, haut); pos_c = lambda x: MILIEU + sc * pas(x)
        def etat():
            ae, ac = ang_e(), ang_c(); e1, e2, e3 = bus.etat(ID_EPAULE), bus.etat(ID_COUDE), bus.etat(ID_PINCE)
            print(f"   épaule {ae:+.0f}° · coude {ac:+.0f}° · avant-bras {ae + ac:+.0f}° par rapport à l'horizontale · bas de la pince à {bas_de_pince(a.hauteur, ae, ac, ang_f()):.0f} mm de la table"
                  f" · mâchoires ≈ {P.ecart_mm(e3['position'], ouvert):.0f} mm")
            if socle: print(f"   socle {degres(bus.etat(socle)['position'] - MILIEU):+.0f}° · charge {bus.etat(socle)['charge']:+.0f} % · {bus.etat(socle)['temperature']} °C")
            print(f"   charges : épaule {e1['charge']:+.0f} %, coude {e2['charge']:+.0f} %, pince {e3['charge']:+.0f} % · températures : {e1['temperature']}, {e2['temperature']}, {e3['temperature']} °C")
        def verifier(ae, ac, f=None):
            # 3° de marge : un servo arrêté en butée lit parfois 90,3° (essai du 18/11/2026 : tout geste refusé bras à la verticale)
            if not E.BAS - 3 <= ae <= E.HAUT + 3: raise ErreurServo(f'épaule à {ae:+.0f}° : hors de −30° à +90°')
            if abs(ac) > COUDE_MAX + 3: raise ErreurServo(f'coude à {ac:+.0f}° : hors de ±{COUDE_MAX}°')
            z = bas_de_pince(a.hauteur, ae, ac, ang_f() if f is None else f)
            if z < 3: raise ErreurServo(f'la pince irait dans la table (bas des mâchoires à {z:.0f} mm)')
        etat()
        if socle: print('\nSocle : t45 = tourner à +45° (de −90 à +90), t0 = revenir en face.', end='')
        print('\nCommandes : e30 = épaule à 30° · c-45 = coude à −45° · n20 = épaule à 20°, avant-bras gardé à l\'horizontale · plat = avant-bras à l\'horizontale')
        print('            poser = descendre jusqu\'à la table, lâcher, remonter · o = ouvrir · s / S = serrer doucement / fort · repos = bras à la verticale · i = infos · q = quitter. Plusieurs à la suite : « n0 o s n40 ».')
        while True:
            mots = input('> ').replace(',', ' ').split()
            faux = [m for m in mots if not re.fullmatch(r'[ecntpf]-?\d+|plat|repos|poser|[osSiq]', m)]
            if faux: print('   commande inconnue :', ' '.join(faux), '(rien n\'a bougé)'); continue
            if 'q' in mots: break
            for m in mots:
                try:
                    if m == 'i': pass
                    elif m == 'o':
                        bus.tenir(ID_PINCE); bus.limiter_force(ID_PINCE, P.FORCE_MOUVEMENT); print('   ouvrir...', bus.aller(ID_PINCE, ouvert, charge_max=P.CHARGE_BLOCAGE))
                    elif m == 'poser':
                        ae, ac = ang_e(), ang_c()
                        if abs(ae + ac) > 3: print('   d\'abord l\'avant-bras à l\'horizontale...', aller_ensemble(bus, [(ID_COUDE, pos_c(-ae))]))
                        print('   descente lente, avant-bras à l\'horizontale, jusqu\'à sentir la table...')
                        v, lus, pose = round(ang_e()), [], False
                        while True:
                            v -= 1
                            if v < E.BAS or bas_de_pince(a.hauteur, v, -v, ang_f()) < 5:
                                print('   arrivé en bas sans sentir la table : je n\'ouvre pas. (o pour ouvrir quand même)'); break
                            texte = aller_ensemble(bus, [(ID_EPAULE, pos_e(v)), (ID_COUDE, pos_c(-v))], synchro=True)
                            if texte.startswith('ARRÊT'): print('  ', texte); break
                            time.sleep(0.25)
                            ce = sum(bus.etat(ID_EPAULE)['charge'] for _ in range(3)) / 3; cc = sum(bus.etat(ID_COUDE)['charge'] for _ in range(3)) / 3
                            lus.append((ce, cc))
                            if len(lus) <= 3: continue
                            re_, rc = sum(x[0] for x in lus[:3]) / 3, sum(x[1] for x in lus[:3]) / 3
                            if abs(ce - re_) >= SEUIL_CONTACT or abs(cc - rc) >= SEUIL_CONTACT:
                                print(f'   contact senti à {v:+d}° (charge épaule {re_:+.0f} → {ce:+.0f} %, coude {rc:+.0f} → {cc:+.0f} %)'); pose = True; break
                        if pose:
                            aller_ensemble(bus, [(ID_EPAULE, pos_e(v + 1)), (ID_COUDE, pos_c(-v - 1))], synchro=True)      # relâche l'appui
                            bus.tenir(ID_PINCE); bus.limiter_force(ID_PINCE, P.FORCE_MOUVEMENT); print('   ouvrir...', bus.aller(ID_PINCE, ouvert, charge_max=P.CHARGE_BLOCAGE))
                            h = min(E.HAUT, v + 20); print('   remonter...', aller_ensemble(bus, [(ID_EPAULE, pos_e(h)), (ID_COUDE, pos_c(-h))], synchro=True))
                    elif m in 'sS':
                        bus.tenir(ID_PINCE); texte, pos, tenu = bus.serrer(ID_PINCE, ferme, P.FORCE_DOUCE if m == 's' else P.FORCE_FERME, maintien=a.maintien or None); print('   serrer...', texte)
                    else:
                        ae, ac = ang_e(), ang_c()
                        if m == 'plat': cible = [(ID_COUDE, pos_c(-ae))]; verifier(ae, -ae); nom = 'avant-bras à l\'horizontale'
                        elif m == 'repos': cible = [(ID_EPAULE, pos_e(E.REPOS)), (ID_COUDE, pos_c(0))]; nom = f'bras au repos ({E.REPOS}°)'
                        elif m[0] == 'e': v = int(m[1:]); verifier(v, ac); cible = [(ID_EPAULE, pos_e(v))]; nom = f'épaule à {v:+d}°'
                        elif m[0] == 'f':
                            v = int(m[1:])
                            if not FLEXION: raise ErreurServo('pas de flexion du poignet branchée (servo n° 6)')
                            if abs(v) > FLEXION_MAX: raise ErreurServo('flexion hors de ±90°')
                            verifier(ae, ac, v); cible = [(ID_FLEXION, MILIEU + sf * pas(v))]; nom = f'pince relevée de {v:+d}°'
                        elif m[0] == 'p':
                            v = int(m[1:])
                            if not poignet: raise ErreurServo('pas de poignet branché (servo n° 5)')
                            if abs(v) > POIGNET_MAX: raise ErreurServo('poignet hors de ±90°')
                            cible = [(ID_POIGNET, MILIEU + pas(v))]; nom = f'pince tournée de {v:+d}°'
                        elif m[0] == 't':
                            v = int(m[1:])
                            if not socle: raise ErreurServo('pas de socle tournant branché (servo n° 1, avec le coude au n° 3)')
                            if abs(v) > SOCLE_MAX: raise ErreurServo(f'socle à {v:+d}° : hors de ±{SOCLE_MAX}°')
                            cible = [(socle, MILIEU + pas(v))]; nom = f'socle à {v:+d}°'
                        elif m[0] == 'c': v = int(m[1:]); verifier(ae, v); cible = [(ID_COUDE, pos_c(v))]; nom = f'coude à {v:+d}°'
                        else:
                            v = int(m[1:]); verifier(v, -v); verifier(ae, -ae); nom = f'épaule à {v:+d}°, avant-bras à l\'horizontale'
                            if abs(ae + ac) > 3: print('   d\'abord l\'avant-bras à l\'horizontale...', aller_ensemble(bus, [(ID_COUDE, pos_c(-ae))]))
                            cible = [(ID_EPAULE, pos_e(v)), (ID_COUDE, pos_c(-v))]
                        for i, _ in cible: bus.limiter_force(i, 100)
                        texte = aller_ensemble(bus, cible, synchro=(m[0] == 'n')); print(f'   {nom}...', texte)
                        if texte.startswith('ARRÊT'): etat(); print('   La suite est annulée. Regarde ce qui coince.'); break
                except ErreurServo as err:
                    print('   refusé :', err, '— la suite est annulée'); break
                etat()
    except KeyboardInterrupt: print()
    except ErreurServo as e: print('Problème :', e)
    finally:
        try:
            if tenus:
                print('\nLa force va être coupée : le bras va TOMBER s\'il n\'est pas tenu.')
                input('TIENS le bras (haut du bras ET avant-bras), ou pose-le, puis Entrée... ')
                for i in tenus + [ID_PINCE] + ([1] if ID_COUDE == 3 and bus.present(1) else []) + ([ID_POIGNET] if bus.present(ID_POIGNET) else []): bus.relacher(i)
                print('Force coupée. Pose le bras doucement. Au revoir.')
        except (Exception, KeyboardInterrupt):
            print('\n⚠️  Les servos RETIENNENT peut-être encore le bras. TIENS LE BRAS, puis coupe le 12 V.')
        bus.fermer()

if __name__ == '__main__':
    main()
