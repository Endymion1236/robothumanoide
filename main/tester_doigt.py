"""Essai du doigt motorisé (banc d'essai, servo SCS0009 sur la deuxième carte Waveshare, en 6 V).

Lancer : tester_doigt.bat (FD fermé ; carte de la main branchée en USB et alimentée en 6 V, ou 5 V pour un premier essai).
Commandes :
  i        état du servo : position, charge, tension, température
  n 22     donner un autre numéro au servo (les doigts : pouce 21, index 22, majeur 23, annulaire 24, auriculaire 25)
  v        petit mouvement d'essai, SANS fil monté : ± 20° autour de la position actuelle
  m        mettre le servo au milieu de sa course (pour monter les fils, doigt à moitié plié)
  c        apprendre la course du doigt, fils montés : le servo tourne doucement d'un côté jusqu'à sentir la butée du doigt,
           puis de l'autre ; tu dis de quel côté le doigt est plié
  t / p    doigt tendu / plié          a 50   aller à 50 % (0 = tendu, 100 = plié)       + / -   10 % de plus ou de moins
  r        relâcher (le doigt ne porte rien : il ne tombe pas)                                q   quitter
La course apprise est gardée dans doigts.json (sur ton PC)."""
import json, sys, time
from pathlib import Path
import doigt_servo as S
from doigt_servo import ErreurDoigt, pas, degres

REGLAGES = Path(__file__).with_name('doigts.json')
RECUL = 3.0                                # degrés : on s'arrête un peu avant chaque butée trouvée
CHARGE_CONTACT = 350                       # sur 1000 : en apprenant la course, au-delà c'est la butée du doigt
COURSE_ATTENDUE = 221.0                    # degrés, par le calcul (generer_banc_doigt.py) ; jamais plus de 260 accepté

def lire_reglages():
    try: return {int(k): v for k, v in json.loads(REGLAGES.read_text(encoding='utf-8')).items()}
    except Exception: return {}
def ecrire_reglages(r): REGLAGES.write_text(json.dumps(r, indent=1), encoding='utf-8')

class Essai:
    def __init__(self, main, demander=input, dire=print):
        self.m, self.demander, self.dire = main, demander, dire
        self.reglages = lire_reglages(); self.id = None

    def choisir(self):
        ids = self.m.ids
        if not ids: raise ErreurDoigt('aucun servo ne répond sur la carte de la main')
        if len(ids) == 1: self.id = ids[0]
        else:
            rep = self.demander(f'Servos trouvés : {ids}. Lequel essayer ? ').strip()
            self.id = int(rep) if rep.isdigit() and int(rep) in ids else ids[0]
        e = self.m.etat(self.id)
        self.dire(f'Servo n° {self.id} : position {e["position"]} ({degres(e["position"]):.0f}°), {e["tension"]:.1f} V, {e["temperature"]} °C.')
        self.m.verifier(self.id)
        if self.id not in self.reglages: self.dire('Course du doigt pas encore apprise : monte les fils (voir le plan), puis « c ».')

    def course(self):
        r = self.reglages.get(self.id)
        if not r: raise ErreurDoigt('course pas encore apprise : commande « c »')
        return r['tendu'], r['plie']

    def aller_pct(self, pct):
        t, p = self.course(); pct = max(0.0, min(100.0, pct))
        pos, etat = self.m.aller(self.id, t + (p - t) * pct / 100)
        fait = max(0.0, 100 * (pos - t) / (p - t))
        self.dire(f'   {pct:.0f} % demandé → {fait:.0f} % ({etat})' + ('  : le doigt est bloqué, il tient sa place' if etat == 'bloqué' else ''))
        self.pct = fait

    def petit_essai(self):
        p0 = self.m.position(self.id)
        for d in (20, -20, 0):
            pos, etat = self.m.aller(self.id, p0 + pas(d)); self.dire(f'   {d:+d}° → position {pos} ({etat})')

    def milieu(self):
        pos, etat = self.m.aller(self.id, 512); self.dire(f'   milieu : position {pos} ({etat}). Monte les fils doigt à MOITIÉ plié (environ 45° par charnière).')

    def apprendre(self):
        """Tourne par petits pas d'un côté jusqu'à la butée du doigt (la force monte ou le servo n'avance plus), puis de l'autre."""
        if not self.demander('   Les deux fils sont montés et tendus, le doigt dans le vide ? (o/n) ').strip().lower().startswith('o'): return
        p0 = self.m.position(self.id); bouts = []
        for sens in (1, -1):
            pos, trouve = p0, False
            while True:
                cible = pos + sens * pas(6)
                if not 0 <= cible <= S.PAS_MAX:
                    self.dire('   Bout de course du servo atteint sans trouver la butée du doigt : un fil est sans doute détendu.'); break
                if abs(degres(cible - p0)) > 200:
                    self.dire('   Plus de 200° sans butée : je m\'arrête (fil détendu ou glissé ?).'); break
                pos, etat = self.m.aller(self.id, cible, vitesse=120, arret_charge=CHARGE_CONTACT)
                if etat != 'arrivé': trouve = True; break
            self.m.aller(self.id, p0)
            if not trouve: raise ErreurDoigt('butée du doigt pas trouvée de ce côté : le servo est revenu au départ. Retends les fils, puis recommence « c ».')
            bouts.append(pos); self.dire(f'   Butée trouvée à la position {pos} ({degres(pos - p0):+.0f}° depuis le départ).')
        a, b = bouts
        etendue = degres(abs(a - b))
        if etendue < 60: raise ErreurDoigt(f'course de seulement {etendue:.0f}° : les fils sont-ils accrochés à la poulie ?')
        if etendue > 260: raise ErreurDoigt(f'course de {etendue:.0f}° : trop, un fil a dû glisser')
        self.m.aller(self.id, a)
        rep = self.demander('   Regarde le doigt maintenant : est-il PLIÉ (p) ou TENDU (t) ? ').strip().lower()
        plie, tendu = (a, b) if rep.startswith('p') else (b, a)
        s = 1 if plie > tendu else -1
        tendu, plie = tendu + s * pas(RECUL), plie - s * pas(RECUL)
        self.reglages[self.id] = {'tendu': int(tendu), 'plie': int(plie)}; ecrire_reglages(self.reglages)
        self.dire(f'   Course apprise : tendu {tendu}, plié {plie}, soit {degres(abs(plie - tendu)):.0f}° (le calcul en prévoyait {COURSE_ATTENDUE:.0f}).')
        self.aller_pct(0)

    def info(self):
        e = self.m.etat(self.id); txt = f'   position {e["position"]} ({degres(e["position"]):.0f}°)'
        if self.id in self.reglages:
            t, p = self.course(); txt += f' = {max(0.0, 100 * (e["position"] - t) / (p - t)):.0f} % plié'
        self.dire(txt + f', charge {e["charge"] / 10:.0f} %, {e["tension"]:.1f} V, {e["temperature"]} °C')

    def boucle(self):
        self.choisir(); self.pct = 0.0
        self.dire('Commandes : i · n 22 · v · m · c · t · p · a 50 · + · - · r · q')
        while True:
            mots = self.demander('> ').strip().lower().replace(',', '.').split()
            if not mots: continue
            try:
                c = mots[0]
                if c == 'q': break
                elif c == 'i': self.info()
                elif c == 'n' and len(mots) == 2:
                    ancien = self.id; self.m.changer_numero(ancien, int(mots[1])); self.id = int(mots[1])
                    if ancien in self.reglages: self.reglages[self.id] = self.reglages.pop(ancien); ecrire_reglages(self.reglages)
                    self.dire(f'   Le servo porte maintenant le n° {self.id}. Note-le sur une étiquette.')
                elif c == 'v': self.petit_essai()
                elif c == 'm': self.milieu()
                elif c == 'c': self.apprendre()
                elif c == 't': self.aller_pct(0)
                elif c == 'p': self.aller_pct(100)
                elif c == 'a' and len(mots) == 2: self.aller_pct(float(mots[1]))
                elif c in ('+', '-'): self.aller_pct(self.pct + (10 if c == '+' else -10))
                elif c == 'r': self.m.relacher(self.id); self.dire('   Relâché.')
                else: self.dire('   commande inconnue (rien n\'a bougé)')
            except ValueError: self.dire('   il faut un nombre, par exemple : a 50')
            except ErreurDoigt as e: self.dire(f'   Refusé : {e}')

def main():
    port = sys.argv[sys.argv.index('--port') + 1] if '--port' in sys.argv else None
    try: m = S.Main(port)
    except ErreurDoigt as e: print('Impossible de commencer :', e); return 1
    print(f'Carte de la main sur {m.port_nom}, servos {m.ids}.')
    e = Essai(m)
    try: e.boucle()
    except ErreurDoigt as err: print('Arrêt :', err)
    except KeyboardInterrupt: print('\nInterrompu.')
    try:
        if e.id is not None: m.relacher(e.id)
    except ErreurDoigt: pass
    m.fermer(); print('Au revoir.'); return 0

if __name__ == '__main__': sys.exit(main())
