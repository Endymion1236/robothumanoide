"""Parler aux petits servos des doigts (Feetech SCS0009) par la DEUXIÈME carte Waveshare, alimentée en 6 V.

Ces servos parlent le protocole « SCS » (pas celui des STS3215 du bras) : positions de 0 à 1023 pour 300°, octets dans l'autre
ordre. La bibliothèque est la même (scservo_sdk, copiée dans le dossier bras), avec sa partie « scscl ».

Sécurités :
  - on ne parle qu'à une carte dont les servos disent recevoir MOINS de 8 V : la carte du bras (12 V) est écartée d'office ;
  - un servo qui annonce plus de 8 V est relâché tout de suite (ces servos ne supportent que 4 à 7,4 V) ;
  - vitesse limitée, position bornée à la course apprise du doigt ;
  - pendant un mouvement, si le servo force trop longtemps (doigt bloqué, fil coincé), il s'arrête et tient sa place.
Un doigt ne porte aucun poids : le relâcher ne fait rien tomber."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'bras'))
from scservo_sdk import PortHandler, scscl, COMM_SUCCESS
from scservo_sdk.scscl import (SCSCL_TORQUE_ENABLE, SCSCL_PRESENT_LOAD_L, SCSCL_PRESENT_VOLTAGE, SCSCL_PRESENT_TEMPERATURE,
                               SCSCL_PRESENT_POSITION_L, scs_id as SCSCL_ID)

PAS_MAX = 1023                            # 0 à 1023 = 300°
def degres(p): return p * 300 / 1024
def pas(d): return round(d * 1024 / 300)
TENSION_MAX, TENSION_MIN = 8.0, 4.5       # V
TEMP_MAX = 60                             # °C
CHARGE_ARRET = 600                        # sur 1000 : au-delà pendant 0,4 s, le servo est bloqué → il s'arrête et tient
VITESSE = 250                             # douce
NUMEROS_DOIGTS = {'pouce': 21, 'index': 22, 'majeur': 23, 'annulaire': 24, 'auriculaire': 25}

class ErreurDoigt(Exception): pass

def ports_candidats():
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    ch = [p.device for p in ports if 'CH34' in (p.description or '') or p.vid == 0x1A86]
    return ch or [p.device for p in ports if 'USB' in (p.description or '').upper()]

class Main:
    """La carte de la main. `paquets` : un faux servo pour les essais sans matériel."""
    def __init__(self, port=None, paquets=None, a_chercher=range(1, 31)):
        self.port = None
        if paquets is not None:
            self.p = paquets; self.ids = self._chercher(a_chercher); return
        essais = [port] if port else ports_candidats()
        if not essais: raise ErreurDoigt('Aucune carte trouvée : vérifie le câble USB de la deuxième carte Waveshare.')
        refus = []
        for dev in essais:
            ph = PortHandler(dev)
            if not ph.openPort() or not ph.setBaudRate(1_000_000):
                refus.append(f'{dev} : impossible à ouvrir (FD ou un autre programme est-il ouvert ?)'); continue
            self.port, self.p = ph, scscl(ph)
            ids = self._chercher(a_chercher)
            tensions = {i: self.tension(i) for i in ids}
            if ids and all(t < TENSION_MAX for t in tensions.values()):
                self.ids = ids; self.port_nom = dev; return
            ph.closePort(); self.port = None
            refus.append(f'{dev} : ' + ('aucun servo' if not ids else f'servos {ids} à {max(tensions.values()):.1f} V : c\'est la carte du BRAS (12 V), on n\'y touche pas'))
        raise ErreurDoigt('Pas de carte de la main en 6 V :\n   ' + '\n   '.join(refus))

    def fermer(self):
        if self.port: self.port.closePort()

    def _chercher(self, a_chercher):
        return [i for i in a_chercher if self.p.ping(i)[1] == COMM_SUCCESS]

    def _ok(self, res, quoi):
        if res != COMM_SUCCESS: raise ErreurDoigt(f'{quoi} : pas de réponse ({self.p.getTxRxResult(res)})')
    def lire1(self, i, adr, quoi): v, res, _ = self.p.read1ByteTxRx(i, adr); self._ok(res, quoi); return v
    def lire2(self, i, adr, quoi): v, res, _ = self.p.read2ByteTxRx(i, adr); self._ok(res, quoi); return v

    def tension(self, i): return self.lire1(i, SCSCL_PRESENT_VOLTAGE, f'tension du servo {i}') / 10
    def position(self, i): return self.lire2(i, SCSCL_PRESENT_POSITION_L, f'position du servo {i}')
    def charge(self, i):
        brut = self.lire2(i, SCSCL_PRESENT_LOAD_L, f'charge du servo {i}')
        return -(brut & 1023) if brut & 1024 else brut & 1023
    def etat(self, i):
        return {'position': self.position(i), 'charge': self.charge(i), 'tension': self.tension(i),
                'temperature': self.lire1(i, SCSCL_PRESENT_TEMPERATURE, f'température du servo {i}')}

    def verifier(self, i):
        """À faire avant chaque mouvement : bonne tension, pas trop chaud. Relâche et refuse sinon."""
        t = self.tension(i)
        if t > TENSION_MAX:
            self.relacher(i); raise ErreurDoigt(f'le servo {i} reçoit {t:.1f} V : TROP (4 à 7,4 V). Coupe tout et vérifie l\'alimentation de la carte.')
        if t < TENSION_MIN: raise ErreurDoigt(f'le servo {i} ne reçoit que {t:.1f} V : alimentation de la carte éteinte ou trop faible')
        if self.lire1(i, SCSCL_PRESENT_TEMPERATURE, 'température') > TEMP_MAX:
            self.relacher(i); raise ErreurDoigt(f'le servo {i} est trop chaud : laisse-le refroidir')

    def relacher(self, i):
        res, _ = self.p.write1ByteTxRx(i, SCSCL_TORQUE_ENABLE, 0); self._ok(res, f'relâcher le servo {i}')
    def tenir(self, i):
        res, _ = self.p.write1ByteTxRx(i, SCSCL_TORQUE_ENABLE, 1); self._ok(res, f'tenir le servo {i}')

    def aller(self, i, cible, vitesse=VITESSE, delai=4.0, arret_charge=CHARGE_ARRET):
        """Va vers `cible` (pas). Renvoie (position atteinte, 'arrivé' | 'bloqué'). Bloqué = force au-delà de arret_charge
        pendant 0,4 s, ou plus aucun mouvement alors que la cible est loin : le servo s'arrête et TIENT sa place."""
        self.verifier(i)
        cible = max(0, min(PAS_MAX, int(round(cible))))
        res, _ = self.p.WritePos(i, cible, 0, vitesse); self._ok(res, f'ordre au servo {i}')
        debut = time.time(); trop, immobile, avant = None, None, self.position(i)
        while time.time() - debut < delai:
            time.sleep(0.05)
            pos, ch = self.position(i), self.charge(i)
            if abs(pos - cible) <= 4: return pos, 'arrivé'
            trop = (trop or time.time()) if abs(ch) > arret_charge else None
            immobile = (immobile or time.time()) if abs(pos - avant) <= 1 else None
            avant = pos
            if (trop and time.time() - trop > 0.4) or (immobile and time.time() - immobile > 0.5):
                res, _ = self.p.WritePos(i, pos, 0, vitesse); self._ok(res, 'arrêt')
                return pos, 'bloqué'
        return self.position(i), 'trop long'

    def changer_numero(self, ancien, nouveau):
        if self.p.ping(nouveau)[1] == COMM_SUCCESS: raise ErreurDoigt(f'le numéro {nouveau} est déjà pris sur cette carte')
        res, _ = self.p.unLockEprom(ancien); self._ok(res, 'déverrouiller')
        res, _ = self.p.write1ByteTxRx(ancien, SCSCL_ID, nouveau); self._ok(res, 'changer le numéro')
        time.sleep(0.05)
        res, _ = self.p.LockEprom(nouveau); self._ok(res, 'reverrouiller')
        if self.p.ping(nouveau)[1] != COMM_SUCCESS: raise ErreurDoigt('le servo ne répond pas sous son nouveau numéro')
        self.ids = [nouveau if x == ancien else x for x in self.ids]
