"""Premier essai motorisé du poignet : rotation de la pince sur elle-même (servo n° 5, butées 1024–3072 = un quart de
tour de chaque côté). Montage : poignet/sortie/plan_montage_poignet.pdf.

Commandes : c = pince droite · g / d = 45° d'un côté / de l'autre · G / D = 90° · e = refaire l'étalonnage ·
i = infos · q = quitter (plusieurs à la suite : « c g c d c »).
Ce programme ne parle QU'AU servo n° 5 : l'épaule et le coude ne sont pas tenus, pose le bras à plat avant de lancer.
Force limitée à 50 % : si un câble retient la pince, le servo s'arrête au lieu de tirer dessus.
En quittant, la force du poignet est coupée (il ne porte rien : sans danger)."""
import argparse, sys
from pathlib import Path
from servos import Bus, ErreurServo, degres, pas

ID, MILIEU, BUTEES, FORCE = 5, 2048, (1024, 3072), 50
FAIT = Path(__file__).with_name('poignet_etalonne.json')
# + = le haut de la pince part À GAUCHE, vu de derrière le bras (constaté par Nicolas le 21/11/2026)
MENU = {'c': ('pince droite', 0), 'g': ('45° à gauche (vu de derrière)', 45), 'd': ('45° à droite (vu de derrière)', -45), 'G': ('90° à gauche', 90), 'D': ('90° à droite', -90)}

def etalonner(bus, i=ID):
    """La pince « droite » se règle à la main : le palonnier se visse par quarts de tour, il ne tombe pas forcément droit
    quand le servo est à 2048. On met la pince droite à la main, et le servo prend cette position comme milieu."""
    bus.relacher(i)
    print('\nÉtalonnage du poignet. La force est coupée : tourne la pince À LA MAIN jusqu\'à ce qu\'elle soit DROITE,')
    print('sa plaque du dessous bien à plat (parallèle à la table quand l\'avant-bras est à plat), les mâchoires de chaque côté.')
    if not input('La pince est droite ? Taper o puis Entrée (autre chose pour annuler) : ').strip().lower().startswith('o'): return False
    pos = bus.etalonner_milieu(i)
    if abs(pos - MILIEU) > 10: print(f'   ⚠️  le servo lit {pos} au lieu de {MILIEU}'); return False
    bus.regler_butees(i, *BUTEES); FAIT.write_text('{"fait": true}')
    print('   fait : cette position est « pince droite » (2048), butées 1024–3072 = un quart de tour de chaque côté.')
    return True

def etat(bus, i=ID):
    e = bus.etat(i)
    print(f"   position {e['position']} ({degres(e['position'] - MILIEU):+.0f}°) · butées {e['butee_min']}–{e['butee_max']} · {e['tension']:.1f} V · {e['temperature']} °C · charge {e['charge']:+.0f} %")

def main():
    ap = argparse.ArgumentParser(description='Essai de la rotation du poignet'); ap.add_argument('--port'); a = ap.parse_args()
    try: bus = Bus(a.port)
    except ErreurServo as e: sys.exit(str(e))
    i = ID
    try:
        trouves = bus.chercher(); print('Servos trouvés :', trouves or 'aucun')
        if i not in trouves: sys.exit(f'Servo n° {i} (poignet) introuvable. Vérifie son câble, le 12 V, que FD est fermé, et qu\'il porte bien le n° 5.')
        e = bus.etat(i); etat(bus, i)
        if (e['butee_min'], e['butee_max']) != BUTEES:
            print(f"Butées {e['butee_min']}–{e['butee_max']} : pour le poignet il faut {BUTEES[0]}–{BUTEES[1]}.")
            if not input('Les régler maintenant ? (o/n) ').strip().lower().startswith('o'): sys.exit('Butées non réglées : aucun mouvement.')
            bus.regler_butees(i, *BUTEES); etat(bus, i)
        if not FAIT.exists() or not BUTEES[0] <= bus.etat(i)['position'] <= BUTEES[1]:
            if not etalonner(bus, i): sys.exit('Pas d\'étalonnage : aucun mouvement.')
        if not BUTEES[0] <= bus.etat(i)['position'] <= BUTEES[1]: sys.exit('La pince est hors de ses butées : remets-la droite à la main (12 V coupé), puis relance.')
        print('\nAvant de commencer : le câble entre le poignet et la pince fait-il bien une BOUCLE souple ? Garde un œil dessus.')
        print('Commandes :', ' · '.join(f'{k} = {v[0]}' for k, v in MENU.items()), '· e = refaire l\'étalonnage · i = infos · q = quitter')
        print('Commence par g puis c, puis d puis c, avant d\'essayer G et D.')
        while True:
            mots = input('> ').replace(',', ' ').split()
            faux = [m for m in mots if m not in MENU and m not in ('i', 'q', 'e')]
            if faux: print('   commande inconnue :', ' '.join(faux), '(rien n\'a bougé)'); continue
            if 'q' in mots: break
            for m in mots:
                if m == 'e': etalonner(bus, i); break
                if m != 'i':
                    nom, v = MENU[m]; print(f'   vers {nom}...')
                    try:
                        bus.limiter_force(i, FORCE); bus.tenir(i); texte = bus.aller(i, MILIEU + pas(v), delai_max=12, tolerance=40); print('  ', texte)
                    except ErreurServo as err: print('   refusé :', err); break
                    if texte.startswith('ARRÊT'): etat(bus, i); break
                etat(bus, i)
    except KeyboardInterrupt: print()
    except ErreurServo as e: print('Problème :', e)
    finally:
        try: bus.relacher(i); print('Force du poignet coupée. Au revoir.')
        except Exception: pass
        bus.fermer()

if __name__ == '__main__':
    main()
