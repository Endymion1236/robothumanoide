"""Premier essai motorisé de l'épaule (servo n° 2), en sécurité.

L'épaule PORTE le bras : ce programme ne coupe jamais la force sans te demander de tenir le bras, et si une
sécurité arrête un mouvement, le servo RETIENT le bras sur place (force réduite) au lieu de le lâcher.

Au premier lancement, il règle trois choses, sans aucun mouvement du moteur :
  1. le zéro : tu tiens le haut du bras à l'HORIZONTALE, le servo prend cette position comme milieu (2048) ;
  2. le sens : tu lèves le bras à la main, le programme voit dans quel sens les chiffres montent ;
  3. les butées : 30° sous l'horizontale et 90° au-dessus (bras vertical), écrites dans le servo.
Ensuite : b, h, 3, 6, v = aller à −20°, 0°, 30°, 60°, 90° · + et − = 10° plus haut ou plus bas ·
m = mesure de l'effort à chaque hauteur (pour choisir le trou du ressort) · i = infos · q = quitter.

Premier essai conseillé : SANS le ressort et SANS l'avant-bras (haut du bras seul). Voir epaule/LISEZ-MOI.md.
Si l'avant-bras est monté, son servo doit être alimenté et donné avec --coude N : il est tenu raide pendant l'essai."""
import argparse, json, sys, time
from pathlib import Path
from servos import Bus, ErreurServo, degres, pas

MILIEU = 2048
BAS, HAUT = -30, 90            # course de l'épaule, en degrés par rapport à l'horizontale (epaule/generer_epaule.py)
SENS = Path(__file__).with_name('sens_epaule.json')
POSES = {'b': ('un peu sous l\'horizontale (−20°)', -20), 'h': ('à l\'horizontale (0°)', 0), '3': ('à 30°', 30), '6': ('à 60°', 60), 'v': ('à la verticale (90°)', 90)}

def butees(haut): return (MILIEU + pas(BAS), MILIEU + pas(HAUT)) if haut > 0 else (MILIEU - pas(HAUT), MILIEU - pas(BAS))
def angle(position, haut): return degres(position - MILIEU) * haut
def position(angle_, haut): return MILIEU + haut * pas(angle_)

def afficher_etat(e, haut=None):
    ou = f"{angle(e['position'], haut):+.0f}° par rapport à l'horizontale" if haut else 'angle inconnu (étalonnage à faire)'
    print(f"   position {e['position']} ({ou}) · butées {e['butee_min']}–{e['butee_max']} · {e['tension']:.1f} V · {e['temperature']} °C"
          f" · charge {e['charge']:+.0f} % · {e['courant_mA']} mA · force {'oui' if e['force'] else 'non'}")

def etalonner(bus, ident):
    """Zéro à l'horizontale, sens, butées. Aucun mouvement du moteur : tout se fait à la main, force coupée."""
    print('\n--- Étalonnage de l\'épaule (le moteur ne bouge pas) ---')
    print('TIENS le bras d\'une main : la force va être coupée.')
    if not input('Tu le tiens ? (o/n) ').strip().lower().startswith('o'):
        raise ErreurServo('étalonnage abandonné')
    bus.relacher(ident)
    print('Mets le HAUT DU BRAS (la fourche orange, de l\'épaule au coude) bien à l\'HORIZONTALE :')
    print('   les deux bords de la fourche à la même hauteur au-dessus de la table, à mesurer à la règle aux deux bouts.')
    if not input('Il est à l\'horizontale ? (o/n) ').strip().lower().startswith('o'):
        raise ErreurServo('étalonnage abandonné')
    print('   le servo lit maintenant', bus.etalonner_milieu(ident), '(il faut 2048, à 2 près)')
    while True:
        input('Maintenant LÈVE le bras d\'environ 30° à la main, garde-le là, et appuie sur Entrée... ')
        ecart = bus.etat(ident)['position'] - MILIEU
        if abs(ecart) >= pas(12):
            break
        print(f'   il n\'a presque pas bougé ({degres(ecart):+.0f}°). Lève-le franchement.')
    haut = 1 if ecart > 0 else -1
    SENS.write_text(json.dumps({'haut': haut}), encoding='utf-8')
    print(f"   compris : quand le bras monte, la position {'augmente' if haut > 0 else 'diminue'} (tu l\'as levé de {degres(abs(ecart)):.0f}°).")
    b = butees(haut)
    bus.regler_butees(ident, *b)
    print(f'   butées écrites dans le servo : {b[0]}–{b[1]} (de {BAS}° à +{HAUT}°).')
    e = bus.etat(ident)
    if not b[0] <= e['position'] <= b[1]:
        raise ErreurServo('le bras est hors de ses butées : ramène-le entre −30° et 90° et relance')
    bus.limiter_force(ident, 100); bus.retenir(ident)
    print('   le servo tient le bras : tu peux le lâcher DOUCEMENT (s\'il descend, reprends-le et tape q).')
    return haut

def lacher(bus, ident):
    """Coupe la force, seulement quand le bras est tenu."""
    print('\nLa force va être coupée : le bras va TOMBER s\'il n\'est pas tenu.')
    input('Tiens le bras (ou pose-le sur une cale), puis appuie sur Entrée... ')
    bus.relacher(ident)
    print('Force coupée. Pose le bras doucement.')

def mesurer(bus, ident, haut):
    """Effort du servo pour TENIR le bras à chaque hauteur : c'est ce que le ressort doit faire baisser."""
    print('   mesure de l\'effort (bras immobile 1,5 s à chaque hauteur). Positif = le servo retient le bras qui veut descendre.')
    lignes = []
    for a in (-20, 0, 20, 40, 60, 80):
        bus.limiter_force(ident, 100)
        r = bus.aller(ident, position(a, haut), delai_max=10, si_arret='retenir')
        if r.startswith('ARRÊT'):
            print('  ', r); return
        time.sleep(1.5)
        m = [bus.etat(ident) for _ in range(5)]
        charge = sum(x['charge'] for x in m) / 5 * haut; courant = sum(x['courant_mA'] for x in m) / 5
        lignes.append((a, charge, courant, m[-1]['temperature']))
        print(f'      {a:+4d}° : charge {charge:+5.0f} % · {courant:4.0f} mA · {m[-1]["temperature"]} °C')
    pire = max(lignes, key=lambda l: abs(l[1]))
    print(f'   effort le plus fort : {pire[1]:+.0f} % à {pire[0]:+d}°. Note ce tableau avec le trou du ressort utilisé : on compare et on garde le meilleur trou.')
    if abs(pire[1]) > 35:
        print('   Au-dessus de 35 % environ, le servo chauffe s\'il reste longtemps dans cette position.')

def main():
    ap = argparse.ArgumentParser(description='Essai de l\'épaule')
    ap.add_argument('--port', help='port COM (trouvé tout seul sinon)')
    ap.add_argument('--id', type=int, default=2, help='numéro du servo d\'épaule (2 par défaut)')
    ap.add_argument('--coude', type=int, help='numéro du servo du coude, s\'il est monté : il est tenu raide pendant l\'essai')
    a = ap.parse_args()
    try:
        bus = Bus(a.port)
    except ErreurServo as e:
        sys.exit(str(e))
    ident, tenu = a.id, False
    try:
        if not bus.present(ident):
            sys.exit(f'Servo n° {ident} introuvable. Servos qui répondent : {bus.chercher() or "aucun"}. '
                     'Le servo d\'épaule doit porter le n° 2 (à régler dans FD), ou donne son numéro : --id N')
        if a.coude is not None:
            if a.coude == ident or not bus.present(a.coude):
                sys.exit(f'Servo du coude n° {a.coude} introuvable (ou même numéro que l\'épaule).')
            bus.retenir(a.coude); print(f'Coude (servo n° {a.coude}) tenu raide dans sa position actuelle.')
        e = bus.etat(ident); print(f'Servo d\'épaule n° {ident} :')
        haut = json.loads(SENS.read_text(encoding='utf-8'))['haut'] if SENS.exists() else None
        afficher_etat(e, haut)
        if e['temperature'] >= 50:
            sys.exit('Servo déjà chaud : laisse-le refroidir avant l\'essai.')
        if haut is None or (e['butee_min'], e['butee_max']) != butees(haut):
            print('\nPremier lancement (ou butées différentes) : il faut étalonner l\'épaule.')
            haut = etalonner(bus, ident)
        else:
            if not e['butee_min'] <= e['position'] <= e['butee_max']:
                sys.exit('Le bras est HORS de ses butées. Coupe le 12 V, ramène-le entre −30° et 90° à la main, relance.')
            bus.limiter_force(ident, 100); bus.retenir(ident)
            print('Le servo tient le bras là où il est.')
        tenu = True
        print('\nCommandes :', ' · '.join(f'{k} = {v[0]}' for k, v in POSES.items()))
        print('            + = 10° plus haut · - = 10° plus bas · m = mesurer l\'effort · i = infos · e = refaire l\'étalonnage · q = quitter')
        print('Plusieurs commandes d\'un coup : séparées par des espaces, par exemple « h 3 6 h ».')
        while True:
            mots = [m for m in input('> ').replace(',', ' ').split() if m.lower() != 'et']
            inconnus = [m for m in mots if m not in POSES and m not in ('+', '-', 'm', 'i', 'e', 'q')]
            if inconnus:
                print('   commande inconnue :', ' '.join(inconnus), '(rien n\'a bougé)'); continue
            if 'q' in mots:
                break
            for choix in mots:
                e = bus.etat(ident)
                if choix == 'i':
                    afficher_etat(e, haut); continue
                if choix == 'e':
                    haut = etalonner(bus, ident); break
                if choix == 'm':
                    mesurer(bus, ident, haut); afficher_etat(bus.etat(ident), haut); continue
                if choix in '+-':
                    vise = max(BAS, min(HAUT, round(angle(e['position'], haut) / 10) * 10 + (10 if choix == '+' else -10)))
                    nom = f'à {vise:+d}°'
                else:
                    nom, vise = POSES[choix]
                print(f'   vers {nom}...')
                try:
                    bus.limiter_force(ident, 100)
                    texte = bus.aller(ident, position(vise, haut), delai_max=10, si_arret='retenir')
                except ErreurServo as err:
                    print('   refusé :', err, '— la suite de la série est annulée'); break
                print('  ', texte); afficher_etat(bus.etat(ident), haut)
                if texte.startswith('ARRÊT'):
                    print('   La suite est annulée. Regarde ce qui coince. Pour libérer le bras : q (en le tenant).'); break
    except KeyboardInterrupt:
        print()
    except ErreurServo as e:
        print('Problème :', e)
    finally:
        try:
            if tenu:
                bus.retenir(ident, 60)          # il tient encore le bras, avec une force modérée
                lacher(bus, ident)
            if a.coude is not None:
                input('Tiens aussi l\'avant-bras, puis Entrée : son servo va être libéré... '); bus.relacher(a.coude)
            print('Au revoir.')
        except (Exception, KeyboardInterrupt):
            print('\n⚠️  Le servo RETIENT peut-être encore le bras. TIENS LE BRAS, puis coupe le 12 V.')
        bus.fermer()

if __name__ == '__main__':
    main()
