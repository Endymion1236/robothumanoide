"""Les réglages de la pince et des pions, dans un fichier texte que Nicolas modifie au Bloc-notes : bras/mes_reglages.txt
(double-clic pour l'ouvrir). Lu par trier.py et jouer_morpion.py quand ils sont lancés avec --reglages (trier_pions.bat,
morpion_pions.bat). Le fichier est créé au premier lancement et n'est pas dans le dépôt : une mise à jour ne l'écrase pas.
Avant le 28/11/2026 c'était un fichier .bat ouvert par REGLAGES.bat : l'antivirus de Nicolas (Avast) l'a mis en quarantaine
(fausse alerte « IDP.Generic » sur un .bat qui en copie un autre et lance le Bloc-notes). Un .txt lu par Python n'alerte rien."""
from pathlib import Path

FICHIER = Path(__file__).with_name('mes_reglages.txt')
ANCIEN = Path(__file__).with_name('mes_reglages.bat')
# nom dans le fichier → (option du programme, valeur de départ, explication)
REGLAGES = [
    ('HAUTEUR', 'hauteur', 40.0, ['Hauteur des pions, en mm (60 pour les objets d\'essai, 40 pour les pions raccourcis).']),
    ('MACHOIRE_FIXE', 'machoire_fixe', 32.0, ['Distance, en mm, entre la mâchoire FIXE (celle de droite, tapis compris) et le milieu de l\'avant-bras.',
                                             'À la prise : la mâchoire de DROITE passe trop près du pion -> baisse de 3. Celle de GAUCHE trop près -> monte de 3.']),
    ('DECALE', 'decale', 6.0, ['Après avoir lâché un pion, la pince s\'écarte de ce nombre de mm vers la droite avant de remonter.',
                               'Le pion accroche encore à droite en remontant -> monte à 10. Il est bousculé -> baisse à 3 ou 0.']),
    ('APPUI', 'appui', 12.0, ['Avant de lâcher un pion, la pince descend encore de ce nombre de mm au plus pour l\'appuyer sur la table.',
                              'Le pion est posé trop près ou trop loin dans sa case, ou il est écrasé -> essaie 6, puis 0 (aucun appui).']),
    ('DECALE_PRISE', 'decale_prise', 0.0, ['Retouche de la visée de prise, en mm vers la droite (négatif = vers la gauche). Laisse 0 en temps normal.']),
]

def _lire(chemin):
    vals = {}
    for ligne in chemin.read_text(encoding='utf-8', errors='replace').splitlines():
        ligne = ligne.strip()
        if ligne.lower().startswith('set '): ligne = ligne[4:]                 # ancien fichier .bat : « set NOM=valeur »
        if not ligne or ligne[0] in '#;' or ligne.lower().startswith(('rem', '@')) or '=' not in ligne: continue
        nom, _, val = ligne.partition('=')
        try: vals[nom.strip().upper()] = float(val.strip().replace(',', '.'))
        except ValueError: pass
    return vals

def _ecrire(vals):
    lignes = ['# RÉGLAGES DE LA PINCE ET DES PIONS (tri et morpion)', '# Change seulement le NOMBRE après le signe =. Enregistre (Ctrl+S), ferme, puis relance.', '']
    for nom, _, defaut, aide in REGLAGES:
        v = vals.get(nom, defaut)
        lignes += [f'# {a}' for a in aide] + [f'{nom}={v:g}', '']
    FICHIER.write_text('\n'.join(lignes), encoding='utf-8')

def charger():
    """Renvoie ({option: valeur}, texte à afficher). Crée le fichier s'il manque (en reprenant l'ancien .bat s'il existe) et le
    complète quand un nouveau réglage est apparu, sans toucher aux valeurs de Nicolas."""
    vals = _lire(FICHIER) if FICHIER.exists() else (_lire(ANCIEN) if ANCIEN.exists() else {})
    if not FICHIER.exists() or any(nom not in vals for nom, *_ in REGLAGES): _ecrire(vals)
    options = {opt: vals.get(nom, defaut) for nom, opt, defaut, _ in REGLAGES}
    texte = 'Réglages (mes_reglages.txt) : ' + ', '.join(f'{nom} = {vals.get(nom, defaut):g}' for nom, _, defaut, _ in REGLAGES)
    return options, texte
