"""Étalonner la largeur lue par la pince, avec deux objets d'essai : le GROS rond (40 mm) et le PETIT rond (28 mm).
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
        points = []
        for nom, mm in (('le GROS rond', 40.0), ('le PETIT rond', 28.0)):
            bus.limiter_force(ident, P.FORCE_MOUVEMENT); bus.tenir(ident); print('   ', bus.aller(ident, ouvert, charge_max=P.CHARGE_BLOCAGE))
            r = input(f'\nTiens {nom} ({mm:.0f} mm) DEBOUT entre les mâchoires, au milieu, puis Entrée (ou une autre largeur en mm, puis Entrée) : ').strip().replace(',', '.')
            if r:
                try: mm = float(r)
                except ValueError: pass
            texte, pos, tenu = bus.serrer(ident, ferme, P.FORCE_DOUCE)
            print('   Serrer :', texte)
            if not tenu: print('   Rien de serré : recommence en tenant l\'objet bien au milieu.'); return 1
            print(f'   position {pos} : le dessin disait {P.ecart_mm(pos, ouvert):.0f} mm, l\'objet en fait {mm:.0f}.')
            points.append((pos, mm))
        bus.aller(ident, ouvert, charge_max=P.CHARGE_BLOCAGE)
        if abs(points[0][0] - points[1][0]) < 8: print('\nLes deux positions sont presque les mêmes : un objet a glissé ? Rien enregistré.'); return 1
        L.FICHIER.write_text(json.dumps({'points': points}, indent=1), encoding='utf-8'); et = L.charger()
        print(f'\nEnregistré. Maintenant : fermée ≈ {L.ecart(ferme, ouvert, et):.0f} mm, ouverte ≈ {L.ecart(ouvert, ouvert, et):.0f} mm.')
        print('Le tri s\'en servira pour mesurer les objets et pour ouvrir la pince juste ce qu\'il faut.')
        return 0
    finally:
        bus.fermer()

if __name__ == '__main__': sys.exit(main())
