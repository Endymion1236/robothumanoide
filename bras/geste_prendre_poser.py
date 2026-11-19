"""Premier geste « prendre et poser » : coude (n° 1) + pince (n° 4) sur le même câble.

1. coude au centre, pince ouverte ;
2. tu présentes un gobelet entre les mâchoires et tu appuies sur Entrée : la pince le serre
   (force limitée : s'arrête toute seule sur l'objet) ;
3. l'avant-bras tourne de 90° (à gauche ou à droite) en tenant le gobelet ;
4. la pince le lâche, l'avant-bras revient au centre.

À faire avant : `tester_coude.bat` (butées du coude) et `tester_pince.bat` (butées, étalonnage du
milieu, sens d'ouverture). Toutes les sécurités de servos.py restent : butées, chaleur, blocage.
Sur le support de table, le coude est couché : la pince saisit DE CÔTÉ ; garder une main sous le
gobelet pour le recevoir quand elle le lâche. En quittant, la force des deux servos est coupée."""
import argparse, json, sys
from servos import Bus, ErreurServo, degres, pas
import test_pince as P

MILIEU = 2048
ID_COUDE, ID_PINCE = 1, 4
BUTEES_COUDE = (908, 3188)
ANGLE_POSE = 90                       # degrés de rotation de l'avant-bras pour aller poser

def ligne(bus, nom, ident, ouvert=None):
    e = bus.etat(ident)
    extra = f" · mâchoires ≈ {P.ecart_mm(e['position'], ouvert):.0f} mm" if ouvert else f" ({degres(e['position'] - MILIEU):+.0f}°)"
    print(f"   {nom:5} : position {e['position']}{extra} · {e['temperature']} °C · charge {e['charge']:+.0f} %")

def etape(texte):
    print(f'\n▶ {texte}')

def bouge(bus, ident, cible, **kw):
    """Un mouvement surveillé ; lève ErreurServo si une sécurité l'a arrêté."""
    rapport = bus.aller(ident, cible, **kw)
    print('  ', rapport)
    if rapport.startswith('ARRÊT'):
        raise ErreurServo(rapport)

def ouvrir_pince(bus, ouvert):
    bus.tenir(ID_PINCE); bus.limiter_force(ID_PINCE, P.FORCE_MOUVEMENT)
    bouge(bus, ID_PINCE, ouvert, charge_max=P.CHARGE_BLOCAGE)

def geste(bus, ouvert, cote):
    ferme = sum(P.BUTEES_PINCE) - ouvert
    pose = MILIEU + cote * pas(ANGLE_POSE)
    etape('Coude au centre, pince ouverte')
    bus.tenir(ID_COUDE); bouge(bus, ID_COUDE, MILIEU)
    ouvrir_pince(bus, ouvert)
    ligne(bus, 'coude', ID_COUDE); ligne(bus, 'pince', ID_PINCE, ouvert)

    etape('Présente le gobelet entre les mâchoires, au creux de l\'arrondi')
    if input('   Entrée pour serrer (a pour annuler) : ').strip().lower().startswith('a'):
        print('   annulé'); return
    texte, pos, tenu = bus.serrer(ID_PINCE, ferme, P.FORCE_FERME, maintien=P.FORCE_MAINTIEN)
    print('  ', texte)
    if not tenu:
        print('   Rien de tenu : j\'ouvre la pince et j\'arrête ce geste.')
        ouvrir_pince(bus, ouvert); return
    print(f'   gobelet tenu, largeur ≈ {P.ecart_mm(pos, ouvert):.0f} mm à l\'endroit saisi')

    cote_txt = "d'un côté" if cote > 0 else "de l'autre côté"
    etape(f"L'avant-bras tourne de {ANGLE_POSE}° {cote_txt} en tenant le gobelet")
    try:
        bouge(bus, ID_COUDE, pose)
    except ErreurServo:
        print('   Le coude s\'est arrêté. La pince TIENT TOUJOURS le gobelet.')
        input('   Mets la main sous le gobelet, puis Entrée pour que la pince le lâche... ')
        ouvrir_pince(bus, ouvert); raise
    ligne(bus, 'coude', ID_COUDE); ligne(bus, 'pince', ID_PINCE, ouvert)

    etape('La pince lâche le gobelet')
    input('   Mets la main (ou une boîte) sous le gobelet, puis Entrée... ')
    ouvrir_pince(bus, ouvert)

    etape('Retour au centre')
    bouge(bus, ID_COUDE, MILIEU)
    bus.limiter_force(ID_PINCE, P.FORCE_MOUVEMENT); bouge(bus, ID_PINCE, MILIEU, charge_max=P.CHARGE_BLOCAGE)
    ligne(bus, 'coude', ID_COUDE); ligne(bus, 'pince', ID_PINCE, ouvert)
    print('\n✅ Geste terminé.')

def verifier(bus):
    """Refuse de bouger si un réglage manque, et dit quel programme lancer."""
    trouves = bus.chercher()
    print('Servos trouvés :', trouves or 'aucun')
    for ident, nom, prog in ((ID_COUDE, 'coude', 'tester_coude'), (ID_PINCE, 'pince', 'tester_pince')):
        if ident not in trouves:
            sys.exit(f'Servo de la {nom} (n° {ident}) introuvable : vérifier le branchement, ou lancer {prog}.bat.')
    e = bus.etat(ID_COUDE)
    if (e['butee_min'], e['butee_max']) != BUTEES_COUDE or not BUTEES_COUDE[0] <= e['position'] <= BUTEES_COUDE[1]:
        sys.exit(f"Coude : butées {e['butee_min']}–{e['butee_max']}, position {e['position']}. Lancer d'abord tester_coude.bat.")
    e = bus.etat(ID_PINCE)
    if (e['butee_min'], e['butee_max']) != P.BUTEES_PINCE or not P.BUTEES_PINCE[0] <= e['position'] <= P.BUTEES_PINCE[1]:
        sys.exit(f"Pince : butées {e['butee_min']}–{e['butee_max']}, position {e['position']}. Lancer d'abord tester_pince.bat (étalonnage).")
    if not P.SENS.exists():
        sys.exit('Sens d\'ouverture de la pince inconnu : lancer d\'abord tester_pince.bat une fois.')
    return json.loads(P.SENS.read_text())['ouvert']

def main():
    ap = argparse.ArgumentParser(description='Geste prendre et poser (coude + pince)')
    ap.add_argument('--port', help='port COM (trouvé tout seul sinon)')
    a = ap.parse_args()
    try:
        bus = Bus(a.port)
    except ErreurServo as e:
        sys.exit(str(e))
    try:
        ouvert = verifier(bus)
        print('\nCommandes : g = prendre et poser d\'un côté · d = de l\'autre côté · q = quitter')
        while True:
            choix = input('\n> ').strip()
            if choix == 'q':
                break
            if choix not in ('g', 'd'):
                print('   commande inconnue'); continue
            try:
                geste(bus, ouvert, 1 if choix == 'g' else -1)
            except ErreurServo as err:
                print('   Geste interrompu par une sécurité :', err)
    except KeyboardInterrupt:
        pass
    except ErreurServo as e:
        print('Problème :', e)
    finally:
        for ident in (ID_COUDE, ID_PINCE):
            try:
                bus.relacher(ident)
            except Exception:
                pass
        print('Force coupée sur le coude et la pince. Au revoir.')
        bus.fermer()

if __name__ == '__main__':
    main()
