"""Régler un BAC de tri : où il est sur la table, sa taille, la hauteur de son bord. Gardé dans bacs.json (sur le PC).
Lancer : regler_bac.bat. Pour trouver la position du centre du bac : camera\\voir_table.bat, clic au milieu du bac (lire X et Y).
Le calcul vérifie, sans bouger le bras, que le bras peut lâcher un objet au-dessus du bac quelle que soit sa façon de l'avoir pris."""
import json, sys
import piloter_bras as B, geometrie as G, trier as TR

def nombre(question, mini, maxi):
    while True:
        r = input(question).strip().replace(',', '.')
        try:
            v = float(r)
            if mini <= v <= maxi: return v
        except ValueError: pass
        print(f'   un nombre entre {mini} et {maxi}, s\'il te plaît')

def main():
    B.regler_longueurs({1, 2, 3, 4, 5, 6})                      # bras complet (poignet monté)
    bacs = TR.charger_bacs()
    print('Bacs déjà réglés :', {z: (b['X'], b['Y']) for z, b in bacs.items()} or 'aucun')
    for zone, cote in (('petit', 'GAUCHE'), ('gros', 'DROITE')):
        r = input(f'\nUn bac pour les {zone.upper()}S (à {cote}, vu de derrière le bras) ? o = oui, n = non (zone sur la table), Entrée = garder : ').strip().lower()
        if not r: continue
        if r.startswith('n'): bacs.pop(zone, None); continue
        X = nombre('   X du CENTRE du bac (mm, négatif = à gauche ; lu dans voir_table) : ', -400, 400)
        Y = nombre('   Y du CENTRE du bac (mm, en avant du socle) : ', 100, 600)
        larg = nombre('   largeur INTÉRIEURE du bac, de gauche à droite (mm) : ', 40, 400)
        prof = nombre('   profondeur INTÉRIEURE du bac, d\'avant en arrière (mm) : ', 40, 400)
        bord = nombre('   hauteur du BORD au-dessus de la table (mm) : ', 0, 200)
        b = {'X': X, 'Y': Y, 'largeur': larg, 'profondeur': prof, 'bord': bord}
        rates = [abs(i) for i in G.INCLINAISONS if not TR.pose_dans_bac(b, i)]
        if rates:
            print(f'   ⚠️  Le bras ne peut pas lâcher au-dessus de ce bac un objet pris pince à {rates}°.')
            print('      Rapproche le bac (entre 30 et 40 cm du socle) ou prends un bac plus bas. Bac NON enregistré.'); continue
        bacs[zone] = b; print('   Bac enregistré : le bras peut y lâcher un objet, quelle que soit sa prise.')
    TR.FICHIER_BACS.write_text(json.dumps(bacs, indent=1), encoding='utf-8')
    print('\nEnregistré. Mets les bacs en place, PUIS refais la photo du fond (touche F dans trier) : sinon le bac serait vu comme un objet.')

if __name__ == '__main__': sys.exit(main())
