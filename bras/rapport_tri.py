"""Rapport d'un tri : un dossier par essai dans bras/rapports/, avec les photos de la table et un texte lisible
(demande de Nicolas, 26/11/2026). Rien n'est envoyé ailleurs : les dossiers restent sur son PC.

Contenu d'un dossier tri_AAAAMMJJ_HHMMSS/ :
  rapport.txt          le résumé, objet par objet, puis le journal complet du programme
  resultats.csv        une ligne par objet (s'ouvre dans un tableur)
  00_debut.png         la table au début, telle que la caméra la voit ; 00_debut_vu.png avec ce que le programme a reconnu
  objet_01_avant.png   la table juste avant la prise de l'objet n° 1 (l'objet choisi entouré en rouge) ; objet_01_apres.png après
  fin.png, fin_vu.png  la table à la fin"""
import csv, time
from pathlib import Path
import cv2

DOSSIER = Path(__file__).resolve().parent / 'rapports'
CHAMPS = ['n', 'heure', 'X vu', 'Y vu', 'largeur vue', 'visée X', 'visée Y', 'pince à la prise (°)', 'ouverture (mm)', 'résultat',
          'largeur mesurée (mm)', 'catégorie', 'posé en X', 'posé en Y', 'pince à la pose (°)', 'lâché plus haut (mm)', 'durée (s)', 'remarque']

class Rapport:
    def __init__(self, reglages):
        self.debut = time.time()
        self.dossier = DOSSIER / time.strftime('tri_%Y%m%d_%H%M%S'); self.dossier.mkdir(parents=True, exist_ok=True)
        self.reglages, self.essais, self.lignes, self.essai = reglages, [], [], None

    def journal(self, texte):
        self.lignes.append(f'{time.strftime("%H:%M:%S")}  {texte}')

    def photo(self, nom, brute, vue=None):
        if brute is None: return
        cv2.imwrite(str(self.dossier / f'{nom}.png'), brute)
        if vue is not None: cv2.imwrite(str(self.dossier / f'{nom}_vu.png'), vue)

    def nouvel_essai(self, o):
        self.fin_essai()
        self.essai = {'n': len(self.essais) + 1, 'heure': time.strftime('%H:%M:%S'), 'X vu': round(o['X']), 'Y vu': round(o['Y']),
                      'largeur vue': round(o['largeur']), 't0': time.time()}
        return self.essai['n']

    def note(self, **champs):
        if self.essai is None: return
        for k, v in champs.items():
            self.essai[k.replace('_', ' ')] = round(v) if isinstance(v, float) else v

    def fin_essai(self):
        if self.essai is None: return
        self.essai['durée (s)'] = round(time.time() - self.essai.pop('t0'))
        self.essai.setdefault('résultat', 'interrompu')
        self.essais.append(self.essai); self.essai = None

    def fermer(self, conclusion):
        self.fin_essai()
        with open(self.dossier / 'resultats.csv', 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=CHAMPS, delimiter=';', extrasaction='ignore'); w.writeheader()
            for e in self.essais: w.writerow(e)
        tries = sum(1 for e in self.essais if e.get('résultat') == 'trié')
        t = [f'RAPPORT DE TRI — {time.strftime("%d/%m/%Y %H:%M")}', '',
             f'Objets traités : {len(self.essais)} · triés : {tries} · durée : {round(time.time() - self.debut)} s', conclusion, '', 'RÉGLAGES']
        t += [f'  {k} : {v}' for k, v in self.reglages.items()]
        t += ['', 'OBJET PAR OBJET']
        for e in self.essais:
            t.append(f"  n° {e['n']} ({e['heure']}) vu en X {e['X vu']:+d}, Y {e['Y vu']}, {e['largeur vue']} mm de large → {e.get('résultat')}")
            if 'visée X' in e: t.append(f"      visé en X {e['visée X']:+d}, Y {e['visée Y']} ; pince à {e.get('pince à la prise (°)', '?')}° ; ouverte à {e.get('ouverture (mm)', '?')} mm")
            if 'largeur mesurée (mm)' in e: t.append(f"      pince serrée à {e['largeur mesurée (mm)']} mm → {e.get('catégorie', '?')}")
            if 'posé en X' in e: t.append(f"      posé en X {e['posé en X']:+d}, Y {e['posé en Y']}, pince à {e.get('pince à la pose (°)', '?')}°"
                                         + (f", lâché {e['lâché plus haut (mm)']} mm plus haut" if e.get('lâché plus haut (mm)') else ''))
            if e.get('remarque'): t.append(f"      remarque : {e['remarque']}")
            t.append(f"      durée : {e['durée (s)']} s")
        t += ['', 'À REMPLIR PAR NICOLAS (ce que tu as vu) :', '  objets reposés bien droits ? ', '  objets touchés ou renversés ? ', '  autre : ',
              '', 'JOURNAL COMPLET DU PROGRAMME'] + ['  ' + l for l in self.lignes]
        (self.dossier / 'rapport.txt').write_text('\n'.join(t), encoding='utf-8')
        return self.dossier
