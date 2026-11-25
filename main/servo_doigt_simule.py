"""Faux servo SCS0009 pour essayer tester_doigt.py SANS matériel. Il imite un doigt : deux butées (doigt tendu, doigt plié)
au-delà desquelles le servo force sans avancer."""
import time
from scservo_sdk import COMM_SUCCESS

class DoigtSimule:
    def __init__(self, ident=1, position=512, butees_doigt=(140, 900), tension=6.0, temperature=30):
        self.ident, self.pos, self.cible, self.vitesse = ident, float(position), float(position), 250.0
        self.bmin, self.bmax = butees_doigt                      # butées du DOIGT (None = pas de fil : le servo va partout)
        self.tension, self.temperature, self.force, self.verrou, self.t = tension, temperature, 1, 1, time.time()
        self.bloque, self.ordres = False, []
    def _avancer(self):
        t = time.time(); dt, self.t = t - self.t, t; self.bloque = False
        if not self.force or abs(self.cible - self.pos) < 0.5: return
        sens = 1 if self.cible > self.pos else -1
        n = self.pos + sens * min(self.vitesse * dt * 2, abs(self.cible - self.pos))
        if self.bmin is not None and n < self.bmin: n, self.bloque = float(self.bmin), True
        if self.bmax is not None and n > self.bmax: n, self.bloque = float(self.bmax), True
        self.pos = n
    def ping(self, i): return (9, COMM_SUCCESS, 0) if i == self.ident else (0, -1, 0)
    def getTxRxResult(self, r): return 'pas de réponse (simulé)'
    def unLockEprom(self, i): self.verrou = 0; return COMM_SUCCESS, 0
    def LockEprom(self, i): self.verrou = 1; return (COMM_SUCCESS, 0) if i == self.ident else (-1, 0)
    def WritePos(self, i, p, temps, vitesse):
        self._avancer(); self.cible, self.vitesse = float(p), float(vitesse); self.ordres.append(('aller', p)); return COMM_SUCCESS, 0
    def read1ByteTxRx(self, i, adr):
        self._avancer(); return {62: int(self.tension * 10), 63: self.temperature, 40: self.force}[adr], COMM_SUCCESS, 0
    def read2ByteTxRx(self, i, adr):
        self._avancer()
        if adr == 56: return round(self.pos), COMM_SUCCESS, 0
        if adr == 60:
            brut = (800 if self.bloque else (60 if self.force and abs(self.cible - self.pos) > 0.5 else 10))
            return brut | (1024 if self.cible < self.pos else 0), COMM_SUCCESS, 0
        raise KeyError(adr)
    def write1ByteTxRx(self, i, adr, v):
        self._avancer()
        if adr == 40: self.force = v; self.cible = self.pos
        elif adr == 5:
            if self.verrou: return COMM_SUCCESS, 0
            self.ident = v
        return COMM_SUCCESS, 0
