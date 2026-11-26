"""Étalonner la largeur lue par la pince, avec les objets d'essai : le GROS rond (40 mm), le PETIT rond (28 mm), puis, si on veut,
la BARRE tenue en long (64 mm) et l'écart mesuré au réglet pince grande ouverte (pour que les grandes ouvertures soient justes).
Lancer : etalonner_largeur.bat (FD fermé, 12 V allumé). Le bras ne bouge pas : seule la pince s'ouvre et se ferme.
Tiens l'objet debout entre les mâchoires, à mi-hauteur des tapis ; la pince serre doucement (force de tri), on lit sa position."""
import json, sys
from servos import Bus, ErreurServo
import test_pince as P, largeur_pince as L

def main():
    try: bus = Bus()
    except ErreurServo as e: print('Impossible de commencer :', e); return 1
    try:
        if not P.SENS.exists(): print('La pince n\'est pas étalonnée : lance d\'abord tester_pince.bat.'); return 1
        ident = P.ID_PINCE; ouvert = json.loads(P.SENS.read_text())['ouvert']; ferme = sum(P.BUTEES_PINCE) - ouvert
        print('Avant : le calcul du dessin annonce', f'{P.ecart_mm(ferme, ouvert):.0f} mm fermée, {P.ecart_mm(ouvert, ouvert):.0f} mm ouverte.')
        points, butee = [], []
        for nom, mm in (('le GROS rond', 40.0), ('le PETIT rond', 28.0), ('la BARRE debout, prise EN LONG,', 64.0)):
            bus.limiter_force(ident, P.FORCE_MOUVEMENT); bus.tenir(ident); print('   ', bus.aller(ident, ouvert, charge_max=P.CHARGE_BLOCAGE))
            facultatif = len(points) >= 2
            r = input(f'\nTiens {nom} ({mm:.0f} mm) DEBOUT entre les mâchoires, au milieu, puis Entrée (ou une autre largeur en mm, puis Entrée)'
                      + (' — ou n pour passer' if facultatif else '') + ' : ').strip().replace(',', '.')
            if facultatif and r.lower().startswith('n'): break
            if r:
                try: mm = float(r)
                except ValueError: pass
            texte, pos, tenu = bus.serrer(ident, ferme, P.FORCE_DOUCE)
            print('   Serrer :', texte)
            if not tenu:
                # La pince est allée jusqu'à sa butée « fermée » : soit rien entre les mâchoires, soit la butée est atteinte EN serrant
                # l'objet (essai de Nicolas, 26/11/2026 : « pourtant c'est serré sur l'objet »). On demande plutôt que de deviner.
                r = input('   La pince est allée jusqu\'à sa butée. Les mâchoires serrent-elles quand même l\'objet ? (o/n) ').strip().lower()
                if not r.startswith('o'): print('   Recommence en tenant l\'objet bien au milieu.'); return 1
                print(f'   ⚠️  La butée « fermée » ({ferme}) est atteinte en serrant {mm:.0f} mm : la pince ne pourra pas serrer plus petit.')
                butee.append(mm)
            print(f'   position {pos} : le dessin disait {P.ecart_mm(pos, ouvert):.0f} mm, l\'objet en fait {mm:.0f}.')
            points.append((pos, mm))
        bus.aller(ident, ouvert, charge_max=P.CHARGE_BLOCAGE)
        r = input('\nPince GRANDE OUVERTE : mesure au réglet l\'écart entre les deux tapis, au milieu, et tape-le en mm (ou Entrée pour passer) : ').strip().replace(',', '.')
        try:
            if r: points.append((ouvert, float(r)))
        except ValueError: print('   Pas compris : je ne garde pas cette mesure.')
        if abs(points[0][0] - points[1][0]) < 8:
            if butee:
                print('\nLes deux objets ont été serrés à la MÊME position, celle de la butée « fermée » : la pince n\'arrive pas à se fermer plus.')
                print('Rien enregistré. Mesure, pince FERMÉE à vide (touche s de tester_pince), l\'écart entre les deux tapis, et dis-le-moi.')
            else: print('\nLes deux positions sont presque les mêmes : un objet a glissé ? Rien enregistré.')
            return 1
        # garde-fou : plus la pince est ouverte, plus l'écart est grand. Une mesure qui ne suit pas cet ordre (objet qui a glissé,
        # largeur mal tapée) donnerait des ouvertures absurdes au tri : rien n'est enregistré.
        tries = [l for _, l in sorted(points, key=lambda q: abs(q[0] - ouvert))]
        if any(b >= a for a, b in zip(tries, tries[1:])):
            print('\nCes mesures ne vont pas dans le bon ordre (plus la pince est ouverte, plus l\'écart doit être grand) :')
            for q, l in sorted(points, key=lambda q: abs(q[0] - ouvert)): print(f'   position {q} : {l:.0f} mm')
            print('Rien enregistré : un objet a sans doute glissé. Recommence.'); return 1
        L.FICHIER.write_text(json.dumps({'points': points}, indent=1), encoding='utf-8'); et = L.charger()
        print(f'\nEnregistré ({len(points)} mesures). Maintenant : fermée ≈ {L.ecart(ferme, ouvert, et):.0f} mm, ouverte ≈ {L.ecart(ouvert, ouvert, et):.0f} mm.')
        for mm in (40, 60, 80): print(f'   Pour ouvrir à {mm} mm, le tri mettra la pince en position {L.position_pour(mm, ouvert, ferme, et)}.')
        print('Le tri s\'en servira pour mesurer les objets et pour ouvrir la pince juste ce qu\'il faut.')
        return 0
    finally:
        bus.fermer()

if __name__ == '__main__': sys.exit(main())
