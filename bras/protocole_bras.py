"""Protocole d'essai des articulations du bras : coude, épaule, socle, pince. Mêmes mouvements à chaque fois, tout est mesuré
et rangé dans un rapport (dossier rapports/), pour comparer d'un jour à l'autre et envoyer le fichier.

Lancer : protocole_bras.bat (FD fermé, 12 V allumé, fenêtre de contrôle fermée). Options : --rapide (essai court),
--sans-pince, --sans-socle, --tenue N (secondes de maintien bras tendu, 30 par défaut).
Il faut avoir fait les étalonnages (tester_epaule, tester_coude, tester_pince, tester_socle, piloter_bras).
Sécurités : celles de piloter_bras (butées, chaleur, blocage). Un mouvement arrêté RETIENT le bras, il ne le lâche pas.
Ctrl+C : le bras est retenu sur place et le rapport déjà rempli est gardé.

Ce qui est mesuré pour chaque mouvement : écart à l'arrivée (°), effort le plus fort pendant le mouvement (%), effort pour
tenir la pose (%), température, tension. Jugement : BON / À VOIR, d'après les seuils ci-dessous (à ajuster avec l'expérience)."""
import sys, time, json, queue, statistics
from datetime import datetime
from pathlib import Path
from servos import Bus, ErreurServo, degres, pas
import test_epaule as E, test_pince as P, piloter_bras as B
from controle_bras import Controleur, MILIEU

SEUILS = {'ecart': {'coude': 3.0, 'socle': 3.0, 'épaule': 6.0},      # ° d'écart à l'arrivée (l'épaule fléchit sous le poids)
          'retour': 1.5,                                             # ° entre deux retours au même endroit
          'effort_mouvement': 60, 'effort_tenue': 40,                # % de la force du servo
          'temperature': 55, 'echauffement': 8,                      # °C ; °C gagnés pendant la tenue
          'tension_mini': 11.0}                                      # V : en dessous, l'alimentation fléchit

class Essai:
    def __init__(self, bus=None, port=None, demander=input, dire=print):
        self.c = Controleur.__new__(Controleur); c = self.c
        c.bus = bus or Bus(port); c.journal = queue.Queue(); c.reglages = {'vitesse': 300, 'acceleration': 20, 'serrage_doux': P.FORCE_DOUCE, 'serrage_fort': P.FORCE_FERME, 'maintien': P.FORCE_MAINTIEN}
        c._preparer()
        while not c.journal.empty(): c.journal.get()
        self.bus, self.demander, self.dire_ = c.bus, demander, dire
        self.lignes, self.avis, self.stat = [], [], {}
        lire = self.bus.etat
        def etat(i):                                               # toutes les lectures passent ici : on garde le pire
            e = lire(i); s = self.stat.setdefault(i, {'effort': 0.0, 'tension': 99.0})
            s['effort'] = max(s['effort'], abs(e['charge'])); s['tension'] = min(s['tension'], e['tension']); return e
        self.bus.etat = etat
        self.noms = {c.epaule: 'épaule', c.coude: 'coude', c.pince: 'pince'}
        if c.socle: self.noms[c.socle] = 'socle'

    # ---- écriture ----
    def dire(self, t=''): self.dire_(t); self.lignes.append(t)
    def juger(self, ok, texte):
        if not ok: self.avis.append(texte)
        return 'BON' if ok else 'À VOIR'

    # ---- conversions ----
    def cible(self, i, a):
        c = self.c
        return E.position(a, c.haut) if i == c.epaule else MILIEU + (c.sc if i == c.coude else 1) * pas(a)
    def angle(self, i, p):
        c = self.c
        return E.angle(p, c.haut) if i == c.epaule else degres(p - MILIEU) * (c.sc if i == c.coude else 1)

    # ---- un mouvement mesuré ----
    def aller(self, i, a, pause=1.0):
        """Envoie l'articulation i à l'angle a. Renvoie l'écart à l'arrivée (°), ou None si le mouvement a été arrêté."""
        nom = self.noms[i]; c = self.c; self.stat[i] = {'effort': 0.0, 'tension': 99.0}
        if i in (c.epaule, c.coude):                               # même refus que la fenêtre de contrôle : pas de geste vers la table
            ae, ac = c._angles()
            try: c._verifier(a if i == c.epaule else ae, a if i == c.coude else ac)
            except ErreurServo as err: self.dire(f'  {nom} → {a:+.0f}° : non essayé ({err})'); return 0.0
        self.bus.limiter_force(i, 100)
        texte = B.aller_ensemble(self.bus, [(i, self.cible(i, a))])
        if texte.startswith('ARRÊT'):
            self.dire(f'  {nom} → {a:+.0f}° : {texte}'); self.avis.append(f'{nom} : mouvement vers {a:+.0f}° arrêté'); return None
        pic = self.stat[i]['effort']; time.sleep(pause); e = self.bus.etat(i)
        ecart = self.angle(i, e['position']) - a
        v = self.juger(abs(ecart) <= SEUILS['ecart'][nom] and pic <= SEUILS['effort_mouvement'] and abs(e['charge']) <= SEUILS['effort_tenue']
                       and e['temperature'] <= SEUILS['temperature'] and self.stat[i]['tension'] >= SEUILS['tension_mini'],
                       f'{nom} à {a:+.0f}° : écart {ecart:+.1f}°, effort {pic:.0f} % en mouvement, {abs(e["charge"]):.0f} % en tenue, {e["temperature"]} °C, {self.stat[i]["tension"]:.1f} V')
        self.dire(f'  {nom} → {a:+4.0f}° : {texte:16s} écart {ecart:+5.1f}° · effort {pic:3.0f} % puis {abs(e["charge"]):3.0f} % en tenue · {e["temperature"]} °C · {self.stat[i]["tension"]:.1f} V mini · {v}')
        return ecart

    def serie(self, i, angles):
        for a in angles:
            if self.aller(i, a) is None: return False
        return True

    def repetabilite(self, i, a, b, fois):
        """Va-et-vient entre a et b : le servo revient-il toujours au même endroit ?"""
        retours = []
        for _ in range(fois):
            if self.aller(i, b, pause=0.3) is None or self.aller(i, a, pause=0.6) is None: return
            retours.append(self.angle(i, self.bus.etat(i)['position']))
        etendue = max(retours) - min(retours)
        v = self.juger(etendue <= SEUILS['retour'], f'{self.noms[i]} : retours à {a:+.0f}° étalés sur {etendue:.1f}°')
        self.dire(f'  Répétabilité ({fois} allers-retours {a:+.0f}° ↔ {b:+.0f}°) : retours étalés sur {etendue:.1f}° (moyenne {statistics.mean(retours):+.1f}°) · {v}')

    def tenue(self, i, secondes):
        """Garde la pose et regarde l'effort et l'échauffement."""
        e0 = self.bus.etat(i); efforts = []; fin = time.time() + secondes
        while time.time() < fin:
            e = self.bus.etat(i); efforts.append(abs(e['charge']))
            if self.bus.trop_chaud(i, e): self.dire(f'  Tenue interrompue : {e["temperature"]} °C'); self.avis.append(f'{self.noms[i]} trop chaud en tenue'); break
            time.sleep(0.5)
        e1 = self.bus.etat(i); gain = e1['temperature'] - e0['temperature']
        v = self.juger(max(efforts) <= SEUILS['effort_tenue'] and gain <= SEUILS['echauffement'], f'{self.noms[i]} : tenue {secondes:.0f} s, effort {max(efforts):.0f} %, +{gain} °C')
        self.dire(f'  Tenue {secondes:.0f} s : effort moyen {statistics.mean(efforts):.0f} %, maxi {max(efforts):.0f} % · {e0["temperature"]} → {e1["temperature"]} °C · {v}')

    def question(self, texte):
        r = self.demander(texte + ' (o/n) : ').strip().lower()[:1]; self.lignes.append(f'  {texte} → {"oui" if r == "o" else "non"}'); return r == 'o'

    # ---- le protocole ----
    def lancer(self, rapide=False, pince=True, socle=True, tenue=30.0):
        c = self.c; n = 2 if rapide else 5
        self.dire(f'PROTOCOLE D\'ESSAI DU BRAS — {datetime.now():%d/%m/%Y %H:%M}{" (essai court)" if rapide else ""}')
        self.dire('0. État au départ')
        for i, nom in self.noms.items():
            e = self.bus.etat(i); self.dire(f'  {nom} (n° {i}) : {self.angle(i, e["position"]):+.0f}° · {e["temperature"]} °C · {e["tension"]:.1f} V')
        self.demander('Dégage la table autour du bras, pince vide. Entrée pour mettre le bras au repos (à la verticale)... ')
        if not (self.serie(c.coude, [0]) and self.serie(c.epaule, [90])): return self.fin()
        self.dire('1. Coude (épaule à la verticale)')
        if self.serie(c.coude, [45, 0, -45, 0, 90, -90, 0]): self.repetabilite(c.coude, 0, 45, n)
        self.dire('2. Épaule (bras tendu, coude à 0°)')
        if self.serie(c.epaule, [60, 30, 0]):
            self.dire('  Bras tendu à l\'horizontale : la position la plus dure pour l\'épaule.'); self.tenue(c.epaule, tenue)
            self.serie(c.epaule, [30, 60]); self.repetabilite(c.epaule, 60, 30, n)
        self.serie(c.epaule, [90])
        if c.socle and socle:
            self.dire('3. Socle (bras à la verticale)')
            self.demander('Colle un repère (ruban) sur la table, en face du bras. Entrée... ')
            if self.serie(c.socle, [45, 0, -45, 0, 90, -90, 0]):
                self.repetabilite(c.socle, 0, 60, n)
                if not self.question('Le bras est-il revenu exactement en face du repère ?'): self.avis.append('socle : le plateau a glissé sur le palonnier (bras plus en face du repère)')
                self.dire('  Socle bras tendu (épaule à 30°) :')
                if self.serie(c.epaule, [30]): self.serie(c.socle, [60, -60, 0]); self.serie(c.epaule, [90])
        elif socle: self.dire('3. Socle : pas branché, étape sautée')
        if pince:
            self.dire('4. Pince (à vide)')
            for action, nom in (('o', 'ouvrir'), ('s', 'serrer doux'), ('o', 'ouvrir'), ('S', 'serrer fort'), ('o', 'ouvrir')):
                try: c._pince(action)
                except ErreurServo as err: self.dire(f'  {nom} : refusé ({err})'); self.avis.append(f'pince : {nom} refusé'); break
                while not c.journal.empty(): self.dire('  ' + c.journal.get())
            e = self.bus.etat(c.pince); self.dire(f'  pince : {e["temperature"]} °C · {e["tension"]:.1f} V')
        return self.fin()

    def fin(self):
        self.dire('BILAN')
        for i, nom in self.noms.items():
            try: e = self.bus.etat(i); self.dire(f'  {nom} : {e["temperature"]} °C')
            except ErreurServo as err: self.dire(f'  {nom} : ne répond plus ({err})'); self.avis.append(f'{nom} ne répond plus')
        if self.avis:
            self.dire(f'  {len(self.avis)} point(s) À VOIR :')
            for a in self.avis: self.dire('   - ' + a)
        else: self.dire('  Tout est BON.')
        return self.ecrire()

    def ecrire(self):
        d = Path(__file__).with_name('rapports'); d.mkdir(exist_ok=True)
        f = d / f'protocole_{datetime.now():%Y%m%d_%H%M%S}.txt'; f.write_text('\n'.join(self.lignes) + '\n', encoding='utf-8')
        self.dire_(f'\nRapport enregistré : {f}\nEnvoie-moi ce fichier (ou copie son contenu).'); return f

def main():
    a = sys.argv[1:]; tenue = float(a[a.index('--tenue') + 1]) if '--tenue' in a else 30.0
    try: essai = Essai()
    except ErreurServo as err: print('Impossible de commencer :', err); return 1
    try: essai.lancer(rapide='--rapide' in a, pince='--sans-pince' not in a, socle='--sans-socle' not in a, tenue=tenue)
    except KeyboardInterrupt:
        for i in essai.noms:
            if i != essai.c.pince:
                try: essai.bus.retenir(i)
                except Exception: pass
        essai.dire('INTERROMPU au clavier : le bras est retenu sur place.'); essai.ecrire()
    except ErreurServo as err:
        essai.dire(f'ARRÊT sur erreur : {err}'); essai.avis.append(str(err)); essai.ecrire(); return 1
    return 0

if __name__ == '__main__': sys.exit(main())
