"""Premier essai motorisé de la FLEXION du poignet (servo n° 6, butées 1024–3072 = un quart de tour vers le haut et vers
le bas). Montage : poignet/sortie/plan_montage_flexion.pdf.

Ce poignet PORTE la pince : comme l'épaule, il est RETENU par les sécurités, jamais lâché. La force n'est coupée que
pendant l'étalonnage et en quittant, et le programme demande alors de soutenir la pince avec la main.
Commandes : c = poignet droit · h / b = 30° vers le haut / le bas · H / B = 60° · e = refaire l'étalonnage ·
i = infos · q = quitter (plusieurs à la suite : « c h c b c »).
Ce programme ne parle QU'AU servo n° 6 : pose l'avant-bras à plat sur un support avant de lancer."""
import argparse, json, sys
from pathlib import Path
from servos import Bus, ErreurServo, degres, pas

ID, MILIEU, BUTEES = 6, 2048, (1024, 3072)
SENS = Path(__file__).with_name('sens_flexion.json')
MENU = {'c': ('poignet droit', 0), 'h': ('30° vers le haut', 30), 'b': ('30° vers le bas', -30), 'H': ('60° vers le haut', 60), 'B': ('60° vers le bas', -60)}
oui = lambda q: input(q).strip().lower().startswith('o')

def etalonner(bus, i=ID):
    """Le milieu et le sens « haut » se règlent à la main, force coupée, la pince soutenue."""
    print('\nÉtalonnage de la flexion. SOUTIENS LA PINCE AVEC LA MAIN : la force va être coupée.')
    if not oui('Tu tiens la pince ? Taper o puis Entrée (autre chose pour annuler) : '): return None
    bus.relacher(i)
    print('Mets la pince bien DROITE, dans le prolongement de l\'avant-bras.')
    if not oui('Elle est droite ? (o pour valider) : '): bus.retenir(i); return None
    pos = bus.etalonner_milieu(i)
    if abs(pos - MILIEU) > 10: print(f'   ⚠️  le servo lit {pos} au lieu de {MILIEU}'); bus.retenir(i); return None
    bus.regler_butees(i, *BUTEES); bus.relacher(i)
    input('Maintenant LÈVE la pince vers le HAUT, d\'environ un huitième de tour (45°), garde-la là et tape Entrée : ')
    ecart = bus.etat(i)['position'] - MILIEU
    if abs(ecart) < pas(15): print('   la pince n\'a presque pas bougé : étalonnage à refaire.'); bus.retenir(i); return None
    haut = 1 if ecart > 0 else -1
    input('Bien. Remets la pince DROITE, garde-la là et tape Entrée : ')
    bus.limiter_force(i, 100); bus.retenir(i)
    SENS.write_text(json.dumps({'haut': haut}), encoding='utf-8')
    print(f'   fait : milieu réglé, « vers le haut » = positions {"croissantes" if haut > 0 else "décroissantes"}. Le poignet est tenu, tu peux lâcher la pince.')
    return haut

def etat(bus, haut, i=ID):
    e = bus.etat(i)
    print(f"   position {e['position']} ({degres(e['position'] - MILIEU) * haut:+.0f}° ; + = vers le haut) · butées {e['butee_min']}–{e['butee_max']} · {e['tension']:.1f} V · {e['temperature']} °C · charge {e['charge']:+.0f} %")

def main():
    ap = argparse.ArgumentParser(description='Essai de la flexion du poignet'); ap.add_argument('--port'); a = ap.parse_args()
    try: bus = Bus(a.port)
    except ErreurServo as e: sys.exit(str(e))
    i, tenu = ID, False
    try:
        trouves = bus.chercher(); print('Servos trouvés :', trouves or 'aucun')
        if i not in trouves: sys.exit(f'Servo n° {i} (flexion du poignet) introuvable. Vérifie son câble, le 12 V, que FD est fermé, et qu\'il porte bien le n° 6.')
        e = bus.etat(i)
        if (e['butee_min'], e['butee_max']) != BUTEES:
            print(f"Butées {e['butee_min']}–{e['butee_max']} : pour la flexion il faut {BUTEES[0]}–{BUTEES[1]}.")
            if not oui('Les régler maintenant ? (o/n) '): sys.exit('Butées non réglées : aucun mouvement.')
            bus.regler_butees(i, *BUTEES)
        haut = json.loads(SENS.read_text(encoding='utf-8'))['haut'] if SENS.exists() else None
        if haut is None or not BUTEES[0] <= bus.etat(i)['position'] <= BUTEES[1]:
            haut = etalonner(bus, i)
            if haut is None: sys.exit('Pas d\'étalonnage : aucun mouvement.')
        bus.limiter_force(i, 100); bus.retenir(i); tenu = True; etat(bus, haut, i)
        print('\nLe poignet est TENU là où il est.')
        print('Commandes :', ' · '.join(f'{k} = {v[0]}' for k, v in MENU.items()), '· e = refaire l\'étalonnage · i = infos · q = quitter')
        print('Commence par h puis c, puis b puis c, avant d\'essayer H et B.')
        while True:
            mots = input('> ').replace(',', ' ').split()
            faux = [m for m in mots if m not in MENU and m not in ('i', 'q', 'e')]
            if faux: print('   commande inconnue :', ' '.join(faux), '(rien n\'a bougé)'); continue
            if 'q' in mots: break
            for m in mots:
                if m == 'e':
                    h = etalonner(bus, i); haut = h or haut; break
                if m != 'i':
                    nom, v = MENU[m]; print(f'   vers {nom}...')
                    try: texte = bus.aller(i, MILIEU + haut * pas(v), delai_max=12, tolerance=70, si_arret='retenir'); print('  ', texte)
                    except ErreurServo as err: print('   refusé :', err); break
                    if texte.startswith('ARRÊT'): etat(bus, haut, i); break
                etat(bus, haut, i)
        print('\nPour quitter, la force va être coupée : SOUTIENS LA PINCE AVEC LA MAIN.')
        if oui('Tu tiens la pince ? (o = couper la force ; autre chose = la laisser tenue) : '): bus.relacher(i); tenu = False; print('Force coupée. Au revoir.')
        else: print('Le poignet reste tenu (il chauffe un peu) : coupe le 12 V en soutenant la pince. Au revoir.')
    except KeyboardInterrupt: print('\nInterrompu : le poignet reste TENU. Soutiens la pince avant de couper le 12 V.')
    except ErreurServo as e: print('Problème :', e)
    finally: bus.fermer()

if __name__ == '__main__':
    main()
