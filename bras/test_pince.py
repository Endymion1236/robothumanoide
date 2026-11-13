"""Premier essai motorisé de la pince (servo n° 4, butées 1663–2433), en sécurité.

Au premier lancement : étalonnage du milieu (pince réglée à la main à mi-ouverture, le servo prend
cette position comme 2048), puis le programme demande dans quel sens la pince s'ouvre et le retient
(fichier sens_pince.json, à côté). Ensuite : milieu, ouvrir, fermer, serrer doucement.
« Serrer » avance avec une force LIMITÉE et s'arrête tout seul sur l'objet : un gobelet en carton
n'est pas écrasé. En quittant, la force est coupée (la pince devient libre)."""
import argparse, json, math, sys
from pathlib import Path
from servos import Bus, ErreurServo, degres

MILIEU = 2048
BUTEES_PINCE = (1663, 2433)
ID_PINCE = 4
FORCE_MOUVEMENT = 50          # % : la pince n'a jamais besoin de plus
FORCE_DOUCE, FORCE_FERME = 20, 35
SENS = Path(__file__).with_name('sens_pince.json')

# géométrie de la pince V2 (pince/generer_pince.py) : écart au creux des mâchoires selon l'angle du bras
AY, L_BRAS, E_DOIGT = 15.0, 50.0, 5.0
TH_FERME = math.degrees(math.asin((14 / 2 + E_DOIGT - AY) / L_BRAS))
TH_OUVERT = math.degrees(math.asin((110 / 2 + E_DOIGT - AY) / L_BRAS))
TH_MILIEU = (TH_FERME + TH_OUVERT) / 2

def ecart_mm(position, ouvert):
    """Écart estimé entre les mâchoires (mm) ; `ouvert` = la butée du côté ouvert."""
    signe = 1 if ouvert > MILIEU else -1
    th = TH_MILIEU + signe * degres(position - MILIEU)
    return 2 * (AY + L_BRAS * math.sin(math.radians(th)) - E_DOIGT)

def afficher_etat(e, ouvert=None):
    largeur = f" · mâchoires ≈ {ecart_mm(e['position'], ouvert):.0f} mm" if ouvert else ''
    print(f"   position {e['position']}{largeur} · butées {e['butee_min']}–{e['butee_max']} · {e['tension']:.1f} V"
          f" · {e['temperature']} °C · charge {e['charge']:+.0f} % · force {'oui' if e['force'] else 'non'}")

def etalonner(bus, ident):
    """Réglage du milieu à la main : l'engrenage A est vissé là où ses trous tombent sur le palonnier,
    puis on règle la pince à mi-ouverture et le servo prend cette position comme milieu (2048)."""
    bus.relacher(ident)
    print('\nÉtalonnage du milieu. La force est coupée : tu peux tourner la pince à la main (ça résiste un peu).')
    print('Règle-la à MI-OUVERTURE, au pied à coulisse :')
    print('  - doigts montés : 71 mm entre les mâchoires, au creux de l\'arrondi ;')
    print('  - doigts pas encore montés : 81 mm entre les 2 trous au bout des bras des engrenages.')
    print('Les deux bras doivent être bien symétriques.')
    if not input('Réglée ? Taper o puis Entrée (autre chose pour annuler) : ').strip().lower().startswith('o'):
        print('   étalonnage annulé'); return False
    pos = bus.etalonner_milieu(ident)
    if abs(pos - MILIEU) > 10:
        print(f'   ⚠️  le servo lit {pos} au lieu de {MILIEU} : étalonnage refusé par le servo ?'); return False
    print(f'   fait : cette position est maintenant le milieu ({pos}). Les butées 1663–2433 tombent juste.')
    return True

def trouver_sens(bus, ident):
    if SENS.exists():
        return json.loads(SENS.read_text())['ouvert']
    print('\nPremier lancement : je dois apprendre dans quel sens la pince s\'ouvre.')
    print('La pince va aller au milieu, puis bouger un peu. Rien ne doit être entre les doigts.')
    input('Entrée pour continuer (Ctrl + C pour arrêter)... ')
    bus.limiter_force(ident, FORCE_MOUVEMENT); bus.tenir(ident)
    print('  ', bus.aller(ident, MILIEU))
    print('  ', bus.aller(ident, MILIEU + 150))
    while True:
        r = input('Les mâchoires se sont-elles ÉCARTÉES (o) ou RAPPROCHÉES (f) ? ').strip().lower()
        if r in ('o', 'f'):
            break
    ouvert = BUTEES_PINCE[1] if r == 'o' else BUTEES_PINCE[0]
    SENS.write_text(json.dumps({'ouvert': ouvert}))
    print(f'   retenu : la pince est ouverte côté {ouvert}, fermée côté {sum(BUTEES_PINCE) - ouvert}.')
    print('  ', bus.aller(ident, MILIEU))
    return ouvert

def main():
    ap = argparse.ArgumentParser(description='Essai de la pince')
    ap.add_argument('--port', help='port COM (trouvé tout seul sinon)')
    ap.add_argument('--id', type=int, help='numéro du servo (cherché tout seul sinon)')
    a = ap.parse_args()
    try:
        bus = Bus(a.port)
    except ErreurServo as e:
        sys.exit(str(e))
    ident = None
    try:
        ident = a.id
        if ident is None:
            trouves = bus.chercher()
            print('Servos trouvés :', trouves or 'aucun')
            if ID_PINCE in trouves:
                ident = ID_PINCE
            elif len(trouves) == 1:
                ident = trouves[0]
                print(f'⚠️  Le servo porte le n° {ident}, pas {ID_PINCE}. À corriger dans FD (ligne 5 · ID), mais l\'essai peut se faire.')
            else:
                sys.exit(f'Servo n° {ID_PINCE} introuvable. Brancher la pince seule (ou préciser --id N).')
        e = bus.etat(ident); print(f'Servo n° {ident} :'); afficher_etat(e)
        if (e['butee_min'], e['butee_max']) != BUTEES_PINCE:
            print(f"\nLes butées sont {e['butee_min']}–{e['butee_max']}. Pour la pince, il faut {BUTEES_PINCE[0]}–{BUTEES_PINCE[1]}.")
            if input('Les régler maintenant ? (o/n) ').strip().lower().startswith('o'):
                bus.regler_butees(ident, *BUTEES_PINCE); e = bus.etat(ident); afficher_etat(e)
            if (e['butee_min'], e['butee_max']) != BUTEES_PINCE:
                sys.exit('Butées de la pince non réglées : aucun mouvement. Arrêt.')
        if not BUTEES_PINCE[0] <= e['position'] <= BUTEES_PINCE[1]:
            print(f"\nLe servo est à {e['position']}, hors de ses butées : normal tant que le milieu n'est pas étalonné.")
            if not etalonner(bus, ident):
                sys.exit('Pas d\'étalonnage : aucun mouvement. Arrêt.')
        elif not SENS.exists():
            print('\nPremier lancement : on étalonne d\'abord le milieu (une seule fois).')
            if not etalonner(bus, ident):
                sys.exit('Pas d\'étalonnage : aucun mouvement. Arrêt.')
        ouvert = trouver_sens(bus, ident)
        ferme = sum(BUTEES_PINCE) - ouvert
        menu = {'c': ('milieu', MILIEU), 'o': ('ouvrir en grand', ouvert)}
        print('\nCommandes : c = milieu · o = ouvrir en grand · s = serrer doucement · S = serrer plus fort'
              ' · f = fermer à vide · l = lâcher (libre) · i = infos · e = refaire l\'étalonnage · q = quitter')
        print('Plusieurs commandes d\'un coup : séparées par des espaces, par exemple « o s ».')
        quitter = False
        while not quitter:
            mots = [m for m in input('> ').replace(',', ' ').split() if m.lower() != 'et']
            inconnus = [m for m in mots if m not in ('c', 'o', 's', 'S', 'f', 'l', 'i', 'e', 'q')]
            if inconnus:
                print('   commande inconnue :', ' '.join(inconnus), '(rien n\'a bougé)'); continue
            for choix in mots:
                if choix == 'q':
                    quitter = True; break
                if choix == 'l':
                    bus.relacher(ident); print('   force coupée : la pince est libre'); continue
                if choix == 'i':
                    afficher_etat(bus.etat(ident), ouvert); continue
                if choix == 'e':
                    etalonner(bus, ident); afficher_etat(bus.etat(ident), ouvert); break
                try:
                    bus.tenir(ident)
                    if choix in menu:
                        nom, cible = menu[choix]
                        print(f'   {nom}...')
                        bus.limiter_force(ident, FORCE_MOUVEMENT)
                        print('  ', bus.aller(ident, cible))
                    else:
                        force = {'s': FORCE_DOUCE, 'S': FORCE_FERME, 'f': FORCE_FERME}[choix]
                        print(f"   {'fermer' if choix == 'f' else 'serrer'} (force limitée à {force} %)...")
                        texte, pos, tenu = bus.serrer(ident, ferme, force)
                        print('  ', texte)
                        if tenu:
                            print(f'   largeur de l\'objet ≈ {ecart_mm(pos, ouvert):.0f} mm · « o » ou « l » pour le lâcher.'
                                  ' Ne pas le laisser serré plusieurs minutes.')
                except ErreurServo as err:
                    print('   refusé :', err, '— la suite de la série est annulée')
                    afficher_etat(bus.etat(ident), ouvert); break
                afficher_etat(bus.etat(ident), ouvert)
    except KeyboardInterrupt:
        pass
    except ErreurServo as e:
        print('Problème :', e)
    finally:
        try:
            if ident is not None:
                bus.relacher(ident); print('Force coupée. Au revoir.')
        except Exception:
            pass
        bus.fermer()

if __name__ == '__main__':
    main()
