"""Faux servo STS3215 pour essayer les programmes SANS matériel (aucun risque).

Il imite ce que servos.py demande au vrai servo : positions, butées, force, charge, température, et un
obstacle sur la course (le servo bute dessus et force). Utilisation :
    from servo_simule import ServoSimule ; from servos import Bus
    bus = Bus(paquets=ServoSimule(obstacle=2300))"""
import time
from scservo_sdk import COMM_SUCCESS

class ServoSimule:
    def __init__(self, position=2048, butees=(0, 4095), obstacle=None, temperature=30, ident=1):
        self.ident, self.pos, self.cible, self.vitesse = ident, float(position), float(position), 300.0
        self.butee_min, self.butee_max = butees
        self.obstacle = obstacle            # position que le servo ne peut pas dépasser (objet, pièce coincée) ; None = rien
        self.temperature, self.force, self.limite, self.verrou = temperature, 0, 1000, 1
        self.bloque, self._cote, self.t = False, 0, time.time()
        self.ordres = []                    # journal de ce qu'on lui a demandé, pour les tests

    def _avancer(self):
        t = time.time(); dt, self.t = t - self.t, t
        self.bloque = False
        if not self.force or abs(self.cible - self.pos) < 0.5:
            return
        sens = 1 if self.cible > self.pos else -1
        nouvelle = self.pos + sens * min(self.vitesse * dt, abs(self.cible - self.pos))
        if self.obstacle is not None and (self.pos - self.obstacle) * (nouvelle - self.obstacle) <= 0 and self.pos != self.obstacle:
            nouvelle = float(self.obstacle); self.bloque = True
        elif self.obstacle is not None and self.pos == self.obstacle and (self.cible - self.obstacle) * sens > 0 and self._cote == sens:
            nouvelle = self.pos; self.bloque = True
        if self.bloque: self._cote = sens
        self.pos = nouvelle

    # ---- ce que servos.py appelle ----
    def ping(self, ident): return (777, COMM_SUCCESS, 0) if ident == self.ident else (0, -1, 0)
    def getTxRxResult(self, res): return 'pas de réponse (simulé)'
    def scs_tohost(self, a, b): return -(a & ~(1 << b)) if a & (1 << b) else a
    def unLockEprom(self, ident): self.verrou = 0; return COMM_SUCCESS, 0
    def LockEprom(self, ident): self.verrou = 1; return COMM_SUCCESS, 0
    def ReadPos(self, ident): self._avancer(); return round(self.pos), COMM_SUCCESS, 0
    def WritePosEx(self, ident, position, vitesse, acc):
        self._avancer(); self.cible, self.vitesse, self.force = float(position), float(vitesse), 1
        self.ordres.append(('aller', position)); return COMM_SUCCESS, 0

    def read1ByteTxRx(self, ident, adresse):
        self._avancer()
        v = {63: self.temperature, 62: 123, 40: self.force, 66: int(self.force and abs(self.cible - self.pos) >= 0.5 and not self.bloque)}[adresse]
        return v, COMM_SUCCESS, 0

    def read2ByteTxRx(self, ident, adresse):
        self._avancer()
        if adresse == 60:                    # charge : la limite de force quand il bute, presque rien sinon
            if self.bloque:
                brut = self.limite | ((1 << 10) if self.cible < self.pos else 0)
            else:
                brut = 20 if self.force else 0
            return brut, COMM_SUCCESS, 0
        return {9: self.butee_min, 11: self.butee_max, 69: 60 if self.bloque else 5, 48: self.limite}[adresse], COMM_SUCCESS, 0

    def write1ByteTxRx(self, ident, adresse, valeur):
        self._avancer()
        if adresse == 40:
            if valeur == 128: self.pos = self.cible = 2048.0; self.ordres.append(('milieu',))
            else:
                self.force = int(bool(valeur)); self.ordres.append(('force', self.force))
                if self.force: self.cible = self.pos
        return COMM_SUCCESS, 0

    def write2ByteTxRx(self, ident, adresse, valeur):
        self._avancer()
        if adresse in (9, 11) and self.verrou: return COMM_SUCCESS, 0      # mémoire verrouillée : écriture ignorée
        if adresse == 9: self.butee_min = valeur
        elif adresse == 11: self.butee_max = valeur
        elif adresse == 48: self.limite = valeur
        return COMM_SUCCESS, 0
