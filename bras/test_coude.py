"""Premier essai motorisé du coude, pas à pas et en sécurité.

1. Trouve la carte et le servo, affiche son état (position, butées, tension, température).
2. Si ses butées ne sont pas réglées, propose de les régler (908 et 3188 = ± 100° autour du milieu)
   et REFUSE tout mouvement tant que ce n'est pas fait.
3. Menu : centre, ± 30°, ± 90°, libre, infos. Chaque mouvement est lent et surveillé.
En quittant, la force est coupée (le coude devient libre)."""
import argparse, sys
from servos import Bus, ErreurServo, degres, pas

MILIEU = 2048
BUTEES_COUDE = (908, 3188)     # ± 100° : la fourche touche les colonnes du bras V1 à ± 109°

def afficher_etat(e):
    print(f"   position {e['position']} ({degres(e['position'] - MILIEU):+.0f}°) · butées {e['butee_min']}–{e['butee_max']}"
          f" · {e['tension']:.1f} V · {e['temperature']} °C · charge {e['charge']:+.0f} % · {e['courant_mA']} mA"
          f" · force {'oui' if e['force'] else 'non'}")

def main():
    ap = argparse.ArgumentParser(description='Essai du coude')
    ap.add_argument('--port', help='port COM (trouvé tout seul sinon)')
    ap.add_argument('--id', type=int, help='numéro du servo (cherché tout seul sinon)')
    a = ap.parse_args()
    try:
        bus = Bus(a.port)
    except ErreurServo as e:
        sys.exit(str(e))
    try:
        ident = a.id
        if ident is None:
            trouves = bus.chercher()
            print('Servos trouvés :', trouves or 'aucun')
            if len(trouves) != 1:
                sys.exit('Brancher UN seul servo (ou préciser --id N).')
            ident = trouves[0]
        e = bus.etat(ident); print(f'Servo n° {ident} :'); afficher_etat(e)
        if not bus.butees_reglees(e) or (e['butee_min'], e['butee_max']) != BUTEES_COUDE:
            print(f"\nLes butées du servo sont {e['butee_min']}–{e['butee_max']}. Pour le coude, il faut {BUTEES_COUDE[0]}–{BUTEES_COUDE[1]}.")
            if input('Les régler maintenant ? (o/n) ').strip().lower().startswith('o'):
                bus.regler_butees(ident, *BUTEES_COUDE); e = bus.etat(ident); afficher_etat(e)
        if not bus.butees_reglees(e):
            sys.exit('Butées non réglées : aucun mouvement possible. Arrêt.')
        if not e['butee_min'] <= e['position'] <= e['butee_max']:
            print('\n⚠️  Le coude est HORS de ses butées. Couper le 12 V, le ramener à la main vers le milieu, relancer.')
            sys.exit()
        menu = {'c': ('centre (avant-bras dans l\'axe)', MILIEU), 'g': ('30° d\'un côté', MILIEU + pas(30)),
                'd': ('30° de l\'autre côté', MILIEU - pas(30)), 'G': ('90° d\'un côté', MILIEU + pas(90)),
                'D': ('90° de l\'autre côté', MILIEU - pas(90))}
        print('\nCommandes :', ' · '.join(f'{k} = {v[0]}' for k, v in menu.items()), '· l = libre · i = infos · q = quitter')
        while True:
            choix = input('> ').strip()
            if choix == 'q':
                break
            if choix == 'l':
                bus.relacher(ident); print('   force coupée : le coude est libre'); continue
            if choix == 'i':
                afficher_etat(bus.etat(ident)); continue
            if choix not in menu:
                print('   commande inconnue'); continue
            nom, cible = menu[choix]
            print(f'   vers {nom} (position {cible})...')
            try:
                bus.tenir(ident)
                print('  ', bus.aller(ident, cible))
            except ErreurServo as err:
                print('   refusé :', err)
            afficher_etat(bus.etat(ident))
    except KeyboardInterrupt:
        pass
    except ErreurServo as e:
        print('Problème :', e)
    finally:
        try:
            bus.relacher(ident); print('Force coupée. Au revoir.')
        except Exception:
            pass
        bus.fermer()

if __name__ == '__main__':
    main()
