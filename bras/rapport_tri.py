"""Rapport d'un tri : un dossier par essai dans bras/rapports/, avec les photos de la table et un texte lisible
(demande de Nicolas, 26/11/2026). Rien n'est envoyé ailleurs : les dossiers restent sur son PC.

Contenu d'un dossier tri_AAAAMMJJ_HHMMSS/ :
  rapport.html         LE RAPPORT : il s'ouvre tout seul à la fin du tri, photos comprises, avec le contrôle automatique de chaque
                       objet sur les photos (enlevé ? posé ? debout ?) ; rapports/index.html les résume tous
  rapport.txt          le résumé, objet par objet, puis le journal complet du programme
  resultats.csv        une ligne par objet (s'ouvre dans un tableur)
  00_debut.png         la table au début, telle que la caméra la voit ; 00_debut_vu.png avec ce que le programme a reconnu
  objet_01_avant.png   la table juste avant la prise de l'objet n° 1 (l'objet choisi entouré en rouge) ; objet_01_apres.png après
  fin.png, fin_vu.png  la table à la fin"""
import csv, html, json, time, webbrowser
from pathlib import Path
import cv2

DOSSIER = Path(__file__).resolve().parent / 'rapports'
CHAMPS = ['n', 'heure', 'X vu', 'Y vu', 'largeur vue', 'visée X', 'visée Y', 'pince à la prise (°)', 'ouverture (mm)', 'résultat',
          'largeur mesurée (mm)', 'catégorie', 'posé en X', 'posé en Y', 'pince à la pose (°)', 'lâché plus haut (mm)', 'durée (s)',
          'contrôle photo', 'remarque']

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
        t += ['', 'JOURNAL COMPLET DU PROGRAMME'] + ['  ' + l for l in self.lignes]
        (self.dossier / 'rapport.txt').write_text('\n'.join(t), encoding='utf-8')
        bilan = {'date': time.strftime('%d/%m/%Y %H:%M'), 'objets': len(self.essais), 'tries': tries,
                 'debout': sum(1 for e in self.essais if str(e.get('contrôle photo', '')).startswith('debout')),
                 'duree': round(time.time() - self.debut), 'conclusion': conclusion, 'mode': self.reglages.get('mode', '')}
        (self.dossier / 'resultats.json').write_text(json.dumps({'bilan': bilan, 'essais': self.essais, 'reglages': self.reglages}, ensure_ascii=False, indent=1), encoding='utf-8')
        self.page(bilan); index()
        return self.dossier

    def page(self, bilan):
        """rapport.html : tout le tri sur une page, photos comprises (elles sont à côté, dans le même dossier)."""
        e_ = html.escape
        def img(nom): return f'<img src="{nom}.png">' if (self.dossier / f'{nom}.png').exists() else '<div class="vide">pas de photo</div>'
        couleur = lambda r: '#2e7d32' if r == 'trié' else '#c62828' if r and (r.startswith('raté') or r == 'interrompu') else '#ef6c00'
        h = [f'<!DOCTYPE html><html lang="fr"><meta charset="utf-8"><title>Tri du {bilan["date"]}</title><style>'
             'body{font-family:sans-serif;margin:20px;max-width:1300px}img{width:100%;border-radius:6px}.deux{display:grid;grid-template-columns:1fr 1fr;gap:10px}'
             '.objet{border:1px solid #ccc;border-radius:8px;padding:12px;margin:16px 0}.res{font-weight:bold;font-size:1.2em}td,th{padding:4px 10px;border-bottom:1px solid #ddd;text-align:left}'
             '.vide{background:#eee;padding:40px;text-align:center;color:#888}pre{background:#f6f6f6;padding:10px;font-size:12px;white-space:pre-wrap}</style>',
             f'<h1>Câlin trie — {bilan["date"]}</h1>',
             f'<p class="res">{bilan["tries"]} objet(s) trié(s) sur {bilan["objets"]} · {bilan["debout"]} reposé(s) debout (contrôle photo) · {bilan["duree"]} s</p>',
             f'<p>{e_(bilan["conclusion"])}</p><table>' + ''.join(f'<tr><th>{e_(str(k))}</th><td>{e_(str(v))}</td></tr>' for k, v in self.reglages.items()) + '</table>',
             '<h2>La table au début et à la fin</h2><div class="deux">' + img('00_debut_vu') + img('fin_vu') + '</div>',
             '<h2>Objet par objet</h2><table><tr>' + ''.join(f'<th>{c}</th>' for c in ('n°', 'vu en', 'largeur vue', 'pince prise', 'mesurée', 'catégorie', 'posé en', 'résultat', 'contrôle photo', 'durée')) + '</tr>']
        for e in self.essais:
            pose = f"X {e['posé en X']:+d} Y {e['posé en Y']}" if 'posé en X' in e else ''
            h.append(f"<tr><td>{e['n']}</td><td>X {e['X vu']:+d} Y {e['Y vu']}</td><td>{e['largeur vue']} mm</td><td>{e.get('pince à la prise (°)', '')}°</td>"
                     f"<td>{e.get('largeur mesurée (mm)', '')} mm</td><td>{e_(str(e.get('catégorie', '')))}</td><td>{pose}</td>"
                     f"<td style='color:{couleur(e.get('résultat'))}'><b>{e_(str(e.get('résultat')))}</b></td><td>{e_(str(e.get('contrôle photo', '')))}</td><td>{e['durée (s)']} s</td></tr>")
        h.append('</table>')
        for e in self.essais:
            n = e['n']
            h.append(f"<div class='objet'><h3>Objet n° {n} — <span style='color:{couleur(e.get('résultat'))}'>{e_(str(e.get('résultat')))}</span></h3>"
                     f"<p>Vu en X {e['X vu']:+d}, Y {e['Y vu']} ({e['largeur vue']} mm de large) · visé en X {e.get('visée X', '?')}, Y {e.get('visée Y', '?')} · "
                     f"pince à {e.get('pince à la prise (°)', '?')}°, ouverte à {e.get('ouverture (mm)', '?')} mm · serrée à {e.get('largeur mesurée (mm)', '?')} mm"
                     + (f" · posé en X {e['posé en X']:+d}, Y {e['posé en Y']}, pince à {e.get('pince à la pose (°)', '?')}°" if 'posé en X' in e else '')
                     + (f"<br><b>Contrôle photo : {e_(str(e['contrôle photo']))}</b>" if e.get('contrôle photo') else '')
                     + (f"<br>Remarque : {e_(str(e['remarque']))}" if e.get('remarque') else '')
                     + f"</p><div class='deux'><div><b>Avant</b> (objet choisi en rouge){img(f'objet_{n:02d}_avant_vu')}</div><div><b>Après</b>{img(f'objet_{n:02d}_apres_vu')}</div></div></div>")
        h.append('<h2>Journal du programme</h2><pre>' + e_('\n'.join(self.lignes)) + '</pre></html>')
        (self.dossier / 'rapport.html').write_text(''.join(h), encoding='utf-8')
        try: webbrowser.open((self.dossier / 'rapport.html').resolve().as_uri())
        except Exception: pass

def index():
    """rapports/index.html : tous les essais de tri, du plus récent au plus ancien, avec un lien vers chacun."""
    lignes = []
    for d in sorted(DOSSIER.glob('tri_*'), reverse=True):
        try: b = json.loads((d / 'resultats.json').read_text(encoding='utf-8'))['bilan']
        except Exception: continue
        lignes.append(f"<tr><td><a href='{d.name}/rapport.html'>{b['date']}</a></td><td>{html.escape(b['mode'])}</td><td>{b['objets']}</td><td>{b['tries']}</td>"
                      f"<td>{b['debout']}</td><td>{b['duree']} s</td><td>{html.escape(b['conclusion'])}</td></tr>")
    (DOSSIER / 'index.html').write_text('<!DOCTYPE html><html lang="fr"><meta charset="utf-8"><title>Essais de tri</title><style>body{font-family:sans-serif;margin:20px}'
        'td,th{padding:5px 10px;border-bottom:1px solid #ddd;text-align:left}</style><h1>Tous les essais de tri</h1><table><tr><th>date</th><th>mode</th>'
        '<th>objets</th><th>triés</th><th>debout</th><th>durée</th><th>conclusion</th></tr>' + ''.join(lignes) + '</table></html>', encoding='utf-8')
