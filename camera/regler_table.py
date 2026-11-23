"""Enregistre où sont collés les 4 marqueurs (table.json). À refaire seulement si on déplace les marqueurs ou le bras.
Toutes les mesures se prennent à la règle, en millimètres, de CENTRE de marqueur à centre de marqueur."""
import json
import table as T

def nombre(q):
    while True:
        try: return float(input(q).replace(',', '.'))
        except ValueError: print('   un nombre en millimètres, par exemple 400')

print(__doc__)
print('Place-toi DERRIÈRE le bras. Les marqueurs : 0 près à gauche, 1 près à droite, 2 au fond à droite, 3 au fond à gauche.')
r = {'largeur': nombre('Largeur : distance entre les centres des marqueurs 0 et 1 (mm) : '),
     'profondeur': nombre('Profondeur : distance entre les centres des marqueurs 0 et 3 (mm) : ')}
print('\nPosition du marqueur 0 par rapport à l\'AXE du socle (le centre du plateau tournant) :')
g = nombre('  de combien le centre du marqueur 0 est-il À GAUCHE de l\'axe du socle (mm ; s\'il est à droite, mets un nombre négatif) : ')
r['x0'] = -g; r['y0'] = nombre('  de combien est-il EN AVANT de l\'axe du socle (mm) : ')
T.FICHIER.write_text(json.dumps(r, indent=1), encoding='utf-8')
print('\nEnregistré. Les 4 centres, dans le repère du bras (X à droite, Y en avant) :')
for i, (x, y) in T.coins_table(r).items(): print(f'   marqueur {i} : X = {x:+.0f} mm, Y = {y:+.0f} mm')
