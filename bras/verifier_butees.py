"""Vérifie les butées de tous les servos branchés, sans rien faire bouger. Lancer : verifier_butees.bat (FD fermé, 12 V allumé).

Pour chaque servo qui répond : son numéro, son rôle, ses butées, celles qu'il devrait avoir, sa position.
Le programme ne change rien tout seul : il propose de régler les butées manquantes et attend « o ».
L'épaule fait exception : ses butées dépendent de son étalonnage, on les règle avec tester_epaule.bat."""
import json, sys
from servos import Bus, ErreurServo, degres, numero_coude, numero_socle
import test_epaule as E, test_pince as P, piloter_bras as B

MILIEU = 2048
MARGE = 35              # pas (3°) : un servo arrêté contre sa butée lit souvent 2 ou 3 pas au-delà (épaule à 3074 pour 3072, le 21/11/2026)
QUART = (1024, 3072)        # un quart de tour de chaque côté (écrit ici : ce programme marche même avec un ancien piloter_bras.py)
def attendues(trouves):
    """Numéro → (rôle, butées attendues ou None si on ne peut pas le savoir, programme d'étalonnage)."""
    coude, socle = numero_coude(trouves), numero_socle(trouves)
    haut = json.loads(E.SENS.read_text(encoding='utf-8'))['haut'] if E.SENS.exists() else None
    r = {2: ('épaule', E.butees(haut) if haut else None, 'tester_epaule.bat'), 4: ('pince', P.BUTEES_PINCE, 'tester_pince.bat'),
         5: ('poignet, rotation', QUART, 'tester_poignet.bat'), 6: ('poignet, flexion', QUART, 'tester_flexion.bat')}
    r[coude] = ('coude', B.BUTEES_COUDE, 'tester_coude.bat')
    if socle: r[socle] = ('socle', B.BUTEES_SOCLE, 'tester_socle.bat')
    return r

def main(bus=None, demander=input):
    try: bus = bus or Bus(sys.argv[sys.argv.index('--port') + 1] if '--port' in sys.argv else None)
    except ErreurServo as e: print(e); return 1
    try:
        trouves = bus.chercher(); print('Servos qui répondent :', trouves or 'aucun')
        if not trouves: print('Vérifie le 12 V, le câble USB, et que FD est fermé.'); return 1
        roles = attendues(trouves); a_regler = []
        print(f"\n{'n°':>3}  {'rôle':<20} {'butées lues':<13} {'attendues':<13} {'position':<16} verdict")
        for i in trouves:
            e = bus.etat(i); lues = (e['butee_min'], e['butee_max']); role, att, prog = roles.get(i, ('inconnu', None, None))
            dedans = lues[0] - MARGE <= e['position'] <= lues[1] + MARGE
            if role == 'inconnu': verdict = 'numéro non prévu : servo neuf pas encore numéroté ?'
            elif att is None: verdict = f'pas encore étalonné : lance {prog}'
            elif lues == tuple(att): verdict = 'BON' if dedans else 'butées bonnes, mais le servo est EN DEHORS : le remettre à la main, 12 V coupé'
            elif lues in ((0, 4095), (0, 0)): verdict = 'PAS RÉGLÉES (valeurs d\'usine)'; a_regler.append((i, role, att, prog))
            else: verdict = 'DIFFÉRENTES de celles attendues'; a_regler.append((i, role, att, prog))
            print(f"{i:>3}  {role:<20} {f'{lues[0]}–{lues[1]}':<13} {(f'{att[0]}–{att[1]}' if att else '?'):<13} {e['position']} ({degres(e['position'] - MILIEU):+.0f}°)".ljust(72) + verdict)
        doubles = [i for i in trouves if i == 1 and numero_socle(trouves) is None and len(trouves) > 1]
        if doubles: print('\nLe n° 1 est compté comme COUDE (pas de n° 3) : si le socle est monté, le coude doit être au n° 3.')
        if not a_regler: print('\nRien à régler ici.'); return 0
        for i, role, att, prog in a_regler:
            if role == 'épaule': print(f'\nÉpaule (n° {i}) : ses butées se règlent avec {prog} (étalonnage), pas ici.'); continue
            e = bus.etat(i)
            if not att[0] - MARGE <= e['position'] <= att[1] + MARGE:
                print(f"\n{role} (n° {i}) : il est à {e['position']}, en dehors de {att[0]}–{att[1]}. Remets-le vers son milieu à la main (12 V coupé), puis relance."); continue
            if demander(f'\nRégler les butées du servo n° {i} ({role}) à {att[0]}–{att[1]} ? (o/n) ').strip().lower().startswith('o'):
                bus.regler_butees(i, *att); e = bus.etat(i); print(f"   fait : {e['butee_min']}–{e['butee_max']}. Pense à lancer {prog} pour l'étalonnage si ce n'est pas fait.")
            else: print('   laissé tel quel.')
        return 0
    except ErreurServo as e: print('Problème :', e); return 1
    finally: bus.fermer()

if __name__ == '__main__': sys.exit(main())
