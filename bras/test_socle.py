"""Premier essai motorisé du socle tournant (servo n° 1, butées 1024–3072 = un quart de tour de chaque côté).

Le socle porte le n° 1 : le COUDE doit donc déjà être passé au n° 3 (plan de montage du socle, étape 8), ou le
servo du socle être seul sur la carte. Commandes : c = en face · g / d = 30° d'un côté / de l'autre ·
G / D = 90° · i = infos · q = quitter (plusieurs à la suite : « c g d c »).
Le socle ne porte pas le bras, il le fait tourner : en quittant, sa force est coupée sans danger."""
import argparse, sys
from pathlib import Path
from servos import Bus, ErreurServo, degres, pas, numero_socle

MILIEU, BUTEES = 2048, (1024, 3072)
FAIT = Path(__file__).with_name('socle_etalonne.json')

def etalonner(bus, i):
    """Le « en face » se règle à la main : les 4 trous du palonnier ne tombent pas forcément là où le plateau est parallèle
    à la base quand le servo est à 2048 (le palonnier se monte par crans de 14°). On aligne le plateau à la main, et le
    servo prend cette position comme milieu."""
    bus.relacher(i)
    print('\nÉtalonnage du socle. La force est coupée : tourne le plateau À LA MAIN jusqu\'à ce que ses côtés soient')
    print('PARALLÈLES à ceux de la base, le bras pointant vers l\'avant (là où tu veux qu\'il soit « en face »).')
    if not input('C\'est aligné ? Taper o puis Entrée (autre chose pour annuler) : ').strip().lower().startswith('o'): return False
    pos = bus.etalonner_milieu(i)
    if abs(pos - MILIEU) > 10: print(f'   ⚠️  le servo lit {pos} au lieu de {MILIEU}'); return False
    bus.regler_butees(i, *BUTEES); FAIT.write_text('{"fait": true}')
    print('   fait : cette position est « en face » (2048), butées 1024–3072 = un quart de tour de chaque côté.')
    return True

def etat(bus, i):
    e = bus.etat(i)
    print(f"   position {e['position']} ({degres(e['position'] - MILIEU):+.0f}°) · butées {e['butee_min']}–{e['butee_max']} · {e['tension']:.1f} V · {e['temperature']} °C · charge {e['charge']:+.0f} %")

def main():
    ap = argparse.ArgumentParser(description='Essai du socle tournant'); ap.add_argument('--port'); a = ap.parse_args()
    try: bus = Bus(a.port)
    except ErreurServo as e: sys.exit(str(e))
    i = 1
    try:
        trouves = bus.chercher(); print('Servos trouvés :', trouves or 'aucun')
        if 1 not in trouves: sys.exit('Servo n° 1 (socle) introuvable.')
        if numero_socle(trouves) is None and len(trouves) > 1:
            sys.exit('Le n° 1 est encore le COUDE (pas de servo n° 3) : passe d\'abord le coude au n° 3 dans FD, puis branche le socle.')
        if len(trouves) == 1 and not input('Un seul servo, le n° 1 : est-ce bien celui du SOCLE ? (o/n) ').strip().lower().startswith('o'): sys.exit('Arrêt.')
        e = bus.etat(i); etat(bus, i)
        if (e['butee_min'], e['butee_max']) != BUTEES:
            print(f"Butées {e['butee_min']}–{e['butee_max']} : pour le socle il faut {BUTEES[0]}–{BUTEES[1]}.")
            if not input('Les régler maintenant ? (o/n) ').strip().lower().startswith('o'): sys.exit('Butées non réglées : aucun mouvement.')
            bus.regler_butees(i, *BUTEES); etat(bus, i)
        if not FAIT.exists() or not BUTEES[0] <= bus.etat(i)['position'] <= BUTEES[1]:
            if not etalonner(bus, i): sys.exit('Pas d\'étalonnage : aucun mouvement.')
        if not BUTEES[0] <= bus.etat(i)['position'] <= BUTEES[1]: sys.exit('Le plateau est hors de ses butées : ramène-le en face à la main (12 V coupé), puis relance.')
        menu = {'c': ('en face', 0), 'g': ('30° à gauche', -30), 'd': ('30° à droite', 30), 'G': ('90° à gauche', -90), 'D': ('90° à droite', 90)}   # + = à droite, vu en face du bras (constaté par Nicolas le 20/11/2026)
        print('\nCommandes :', ' · '.join(f'{k} = {v[0]}' for k, v in menu.items()), '· e = refaire l\'étalonnage · i = infos · q = quitter')
        while True:
            mots = input('> ').replace(',', ' ').split()
            faux = [m for m in mots if m not in menu and m not in ('i', 'q', 'e')]
            if faux: print('   commande inconnue :', ' '.join(faux), '(rien n\'a bougé)'); continue
            if 'q' in mots: break
            for m in mots:
                if m == 'e': etalonner(bus, i); break
                if m != 'i':
                    nom, v = menu[m]; print(f'   vers {nom}...')
                    try:
                        bus.limiter_force(i, 100); bus.tenir(i); texte = bus.aller(i, MILIEU + pas(v), delai_max=12, tolerance=40); print('  ', texte)
                    except ErreurServo as err: print('   refusé :', err); break
                    if texte.startswith('ARRÊT'): etat(bus, i); break
                etat(bus, i)
    except KeyboardInterrupt: print()
    except ErreurServo as e: print('Problème :', e)
    finally:
        try: bus.relacher(i); print('Force du socle coupée. Au revoir.')
        except Exception: pass
        bus.fermer()

if __name__ == '__main__':
    main()
