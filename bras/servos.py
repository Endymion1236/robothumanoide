"""Moelle épinière du robot : parler aux servos STS3215 par la carte Waveshare (cavaliers sur B, USB).

Bibliothèque Feetech/Waveshare « scservo_sdk » (copiée depuis driver-servo/STServo_Python.zip).
Sécurité : jamais de position hors des butées lues DANS le servo, vitesse limitée, surveillance de la
température, de la charge et du blocage pendant chaque mouvement (force coupée au moindre souci)."""
import time
import serial.tools.list_ports
from scservo_sdk import PortHandler, sms_sts, COMM_SUCCESS
from scservo_sdk.sms_sts import (SMS_STS_MIN_ANGLE_LIMIT_L, SMS_STS_MAX_ANGLE_LIMIT_L, SMS_STS_TORQUE_ENABLE,
                                 SMS_STS_PRESENT_LOAD_L, SMS_STS_PRESENT_VOLTAGE, SMS_STS_PRESENT_TEMPERATURE,
                                 SMS_STS_PRESENT_CURRENT_L, SMS_STS_MOVING)

PAS_PAR_TOUR = 4096                       # 4096 positions = 360°
def degres(pas): return pas * 360 / PAS_PAR_TOUR
def pas(degres_): return round(degres_ * PAS_PAR_TOUR / 360)

TEMP_MAX = 55                             # °C : au-delà, on coupe la force
CHARGE_MAX = 70                           # % de la force maximale, pendant plus de 0,5 s : servo bloqué
VITESSE_DOUCE, ACCEL_DOUCE = 300, 20      # comme les essais dans FD
LIMITE_COUPLE = 48                        # registre « Torque Limit » (mémoire vive : 0 à 1000 = 0 à 100 %)
FORCE_RETENUE = 40                        # % : force gardée pour RETENIR un bras sur place après un arrêt (épaule)

class ErreurServo(Exception):
    pass

def trouver_port():
    """Port COM de la carte Waveshare (puce CH343), sinon le premier port USB série."""
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if 'CH34' in (p.description or '') or p.vid == 0x1A86:
            return p.device
    usb = [p for p in ports if 'USB' in (p.description or '').upper()]
    if usb:
        return usb[0].device
    raise ErreurServo('Carte introuvable : vérifier le câble USB, le 12 V, et que FD est fermé.')

class Bus:
    def __init__(self, port=None, debit=1_000_000, paquets=None):
        if paquets is not None:           # pour les tests sans carte
            self.port, self.p = None, paquets
            return
        self.port = PortHandler(port or trouver_port())
        if not self.port.openPort():
            raise ErreurServo(f'Impossible d\'ouvrir {self.port.port_name} (FD est-il encore ouvert ?)')
        if not self.port.setBaudRate(debit):
            raise ErreurServo('Débit refusé par la carte')
        self.p = sms_sts(self.port)

    def fermer(self):
        if self.port:
            self.port.closePort()

    def _ok(self, res, err, quoi):
        if res != COMM_SUCCESS:
            raise ErreurServo(f'{quoi} : pas de réponse ({self.p.getTxRxResult(res)})')
        return True

    def lire1(self, ident, adresse, quoi):
        v, res, err = self.p.read1ByteTxRx(ident, adresse); self._ok(res, err, quoi); return v

    def lire2(self, ident, adresse, quoi):
        v, res, err = self.p.read2ByteTxRx(ident, adresse); self._ok(res, err, quoi); return v

    def ecrire1(self, ident, adresse, valeur, quoi):
        res, err = self.p.write1ByteTxRx(ident, adresse, valeur); self._ok(res, err, quoi)

    def ecrire2(self, ident, adresse, valeur, quoi):
        res, err = self.p.write2ByteTxRx(ident, adresse, valeur); self._ok(res, err, quoi)

    def present(self, ident):
        _, res, _ = self.p.ping(ident)
        return res == COMM_SUCCESS

    def chercher(self, ids=range(0, 21)):
        return [i for i in ids if self.present(i)]

    def etat(self, ident):
        pos, res, err = self.p.ReadPos(ident); self._ok(res, err, 'position')
        return {
            'position': pos,
            'butee_min': self.lire2(ident, SMS_STS_MIN_ANGLE_LIMIT_L, 'butée min'),
            'butee_max': self.lire2(ident, SMS_STS_MAX_ANGLE_LIMIT_L, 'butée max'),
            'temperature': self.lire1(ident, SMS_STS_PRESENT_TEMPERATURE, 'température'),
            'tension': self.lire1(ident, SMS_STS_PRESENT_VOLTAGE, 'tension') / 10,
            'charge': self.p.scs_tohost(self.lire2(ident, SMS_STS_PRESENT_LOAD_L, 'charge'), 10) / 10,   # en %
            'courant_mA': round(self.lire2(ident, SMS_STS_PRESENT_CURRENT_L, 'courant') * 6.5),
            'force': bool(self.lire1(ident, SMS_STS_TORQUE_ENABLE, 'force')),
        }

    def butees_reglees(self, e):
        return not (e['butee_min'] == 0 and e['butee_max'] in (0, 4095))

    def regler_butees(self, ident, mini, maxi):
        """Écrit les butées dans la mémoire permanente du servo (gardées même éteint)."""
        if not 0 <= mini < maxi <= 4095:
            raise ErreurServo('butées incohérentes')
        self._ok(*self.p.unLockEprom(ident), 'déverrouillage')
        try:
            self.ecrire2(ident, SMS_STS_MIN_ANGLE_LIMIT_L, mini, 'butée min')
            self.ecrire2(ident, SMS_STS_MAX_ANGLE_LIMIT_L, maxi, 'butée max')
        finally:
            self._ok(*self.p.LockEprom(ident), 'verrouillage')

    def etalonner_milieu(self, ident):
        """Le servo prend sa position ACTUELLE comme milieu (2048) : écrire 128 dans « Torque Enable »
        (table mémoire Feetech STS3215). Le décalage est gardé dans sa mémoire permanente."""
        self._ok(*self.p.unLockEprom(ident), 'déverrouillage')
        try:
            self.ecrire1(ident, SMS_STS_TORQUE_ENABLE, 128, 'étalonnage du milieu')
            time.sleep(0.2)
        finally:
            self._ok(*self.p.LockEprom(ident), 'verrouillage')
        self.relacher(ident)
        return self.etat(ident)['position']

    def relacher(self, ident):
        """Coupe la force : le servo devient libre (on peut le tourner à la main)."""
        self.ecrire1(ident, SMS_STS_TORQUE_ENABLE, 0, 'couper la force')

    def tenir(self, ident):
        self.ecrire1(ident, SMS_STS_TORQUE_ENABLE, 1, 'mettre la force')

    def retenir(self, ident, force=None):
        """Tient le servo LÀ OÙ IL EST, sans le lâcher. Avec `force` (en %), limite aussi sa force.
        Pour une articulation qui porte du poids (épaule) : couper la force ferait tomber le bras."""
        pos = self.etat(ident)['position']
        if force is not None:
            self.limiter_force(ident, force)
        res, err = self.p.WritePosEx(ident, pos, VITESSE_DOUCE, ACCEL_DOUCE); self._ok(res, err, 'ordre de retenue')
        return pos

    def _arreter(self, ident, si_arret, cause, question=''):
        """Ce qu'on fait quand un mouvement est arrêté par une sécurité : couper la force, ou retenir sur place."""
        if si_arret == 'retenir':
            self.retenir(ident, FORCE_RETENUE)
            return f"ARRÊT : {cause}. Le servo RETIENT le bras sur place (force réduite à {FORCE_RETENUE} %).{question}"
        self.relacher(ident)
        return f"ARRÊT : {cause}, force coupée.{question}"

    def trop_chaud(self, ident, e):
        """Vrai seulement si la température dépasse TEMP_MAX à 3 lectures de suite (0,1 s). Une lecture isolée
        peut être fausse : le 15/11/2026, 75 °C lus une fois pendant un serrage, 35 °C juste avant et après
        (impossible en une seconde) ; la pince s'était arrêtée pour rien. Une vraie chauffe, elle, dure."""
        if e['temperature'] < TEMP_MAX:
            return False
        for _ in range(2):
            time.sleep(0.05)
            if self.lire1(ident, SMS_STS_PRESENT_TEMPERATURE, 'température') < TEMP_MAX:
                return False
        return True

    def aller(self, ident, cible, vitesse=VITESSE_DOUCE, accel=ACCEL_DOUCE, delai_max=8.0, afficher=None, charge_max=CHARGE_MAX, si_arret='relacher', tolerance=15):
        """Va doucement à la position cible en surveillant le servo. Renvoie un compte rendu (texte).
        Refuse toute cible hors des butées du servo ; coupe la force en cas de chaleur, d'effort ou de blocage.
        charge_max : effort (en %) au-delà duquel le servo est considéré comme bloqué. À donner PLUS BAS que la
        limite de force du servo : avec une force limitée à 50 %, la charge n'atteint jamais 70 % (essai du
        14/11/2026 : pince coincée, le servo a poussé jusqu'à faire sauter les dents des engrenages).
        Deuxième filet : s'il n'avance plus du tout pendant 0,7 s loin de la cible, la force est coupée aussi.
        tolerance : écart (en pas) accepté à l'arrivée. 15 pour un axe qui ne porte rien ; plus pour l'épaule, où le
        poids du bras fait fléchir le servo sous la position demandée (essai du 18/11/2026 : arrêté à 18 pas, 1,6°, de la
        cible avec 15 % de charge, et pris à tort pour un blocage).
        si_arret : 'relacher' (coude, pince : la force est coupée) ou 'retenir' (épaule : le servo garde le bras
        sur place avec une force réduite, sinon le bras tomberait)."""
        e = self.etat(ident)
        if not self.butees_reglees(e):
            raise ErreurServo('butées non réglées dans le servo : mouvement refusé')
        if not e['butee_min'] <= cible <= e['butee_max']:
            raise ErreurServo(f"cible {cible} hors des butées {e['butee_min']}–{e['butee_max']} : refusé")
        if self.trop_chaud(ident, e):
            raise ErreurServo(f"servo trop chaud ({e['temperature']} °C) : laisser refroidir")
        res, err = self.p.WritePosEx(ident, cible, vitesse, accel); self._ok(res, err, 'ordre de position')
        debut, effort_depuis, avant, immobile_depuis = time.time(), None, e['position'], None
        while True:
            time.sleep(0.1)
            e = self.etat(ident)
            if afficher:
                afficher(e)
            if self.trop_chaud(ident, e):
                return self._arreter(ident, si_arret, f"trop chaud ({e['temperature']} °C)")
            if abs(e['charge']) >= charge_max:
                effort_depuis = effort_depuis or time.time()
                if time.time() - effort_depuis > 0.5:
                    return self._arreter(ident, si_arret, f"le servo force ({e['charge']:.0f} %)", ' Quelque chose le bloque ?')
            else:
                effort_depuis = None
            if abs(e['position'] - avant) <= 2 and abs(e['position'] - cible) > tolerance:
                immobile_depuis = immobile_depuis or time.time()
                if time.time() - immobile_depuis > 0.7:
                    return self._arreter(ident, si_arret, f"le servo n'avance plus (position {e['position']}, charge {e['charge']:.0f} %)", ' Quelque chose le bloque ?')
            else:
                immobile_depuis = None
            avant = e['position']
            if abs(e['position'] - cible) <= tolerance and not self.lire1(ident, SMS_STS_MOVING, 'en mouvement'):
                ecart = e['position'] - cible
                note = f" (à {abs(degres(ecart)):.1f}° de la position demandée : le poids fait fléchir le servo)" if abs(ecart) > 15 else ''
                return f"arrivé en {time.time() - debut:.1f} s{note}"
            if time.time() - debut > delai_max:
                return self._arreter(ident, si_arret, f"n'arrive pas en {delai_max:.0f} s (bloqué ?)")

    def limiter_force(self, ident, pourcent):
        """Force maximale du servo, en % (oubliée quand on coupe le 12 V)."""
        self.ecrire2(ident, LIMITE_COUPLE, max(0, min(100, round(pourcent))) * 10, 'limite de force')

    def serrer(self, ident, cible, force=25, delai_max=6.0, afficher=None, maintien=None):
        """Avance vers `cible` avec une force limitée (en %) et s'arrête de lui-même sur un objet.
        Renvoie (compte rendu, position, objet_tenu). L'objet reste serré avec cette force."""
        e = self.etat(ident)
        if not self.butees_reglees(e):
            raise ErreurServo('butées non réglées dans le servo : mouvement refusé')
        if not e['butee_min'] <= cible <= e['butee_max']:
            raise ErreurServo(f"cible {cible} hors des butées {e['butee_min']}–{e['butee_max']} : refusé")
        if self.trop_chaud(ident, e):
            raise ErreurServo(f"servo trop chaud ({e['temperature']} °C) : laisser refroidir")
        self.limiter_force(ident, force)
        res, err = self.p.WritePosEx(ident, cible, VITESSE_DOUCE, ACCEL_DOUCE); self._ok(res, err, 'ordre de position')
        debut, avant, immobile_depuis = time.time(), e['position'], None
        while True:
            time.sleep(0.1)
            e = self.etat(ident)
            if afficher:
                afficher(e)
            if self.trop_chaud(ident, e):
                self.relacher(ident); return f"ARRÊT : trop chaud ({e['temperature']} °C), force coupée", e['position'], False
            if abs(e['position'] - cible) <= 15:
                return f"fermée jusqu'au bout en {time.time() - debut:.1f} s : rien entre les doigts", e['position'], False
            if abs(e['position'] - avant) <= 2:
                immobile_depuis = immobile_depuis or time.time()
                if time.time() - immobile_depuis > 0.4 and abs(e['charge']) >= force * 0.5:
                    texte = f"objet tenu (force {abs(e['charge']):.0f} % sur {force} % permis)"
                    if maintien is not None and maintien < force:
                        # une fois l'objet saisi, on ne garde que la force de maintien : le servo, qui pousse sans tourner,
                        # chauffe beaucoup moins (42 °C en tenant un verre à 20 %, essai du 18/11/2026)
                        self.limiter_force(ident, maintien); texte += f', puis tenu à {maintien} %'
                    return texte, e['position'], True
            else:
                immobile_depuis = None
            avant = e['position']
            if time.time() - debut > delai_max:
                self.relacher(ident); return f"ARRÊT : ni arrivée ni objet en {delai_max:.0f} s, force coupée", e['position'], False
