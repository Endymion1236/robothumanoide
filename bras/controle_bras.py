"""Fenêtre de commande du bras : socle, épaule, coude, pince, avec réglages (vitesse, accélération, forces).

Lancer : controle_bras.bat (FD fermé, 12 V allumé). Il faut avoir fait une fois tester_epaule, tester_coude,
tester_pince et piloter_bras (étalonnages et sens) : sinon la fenêtre dit lequel lancer.
Les sécurités sont celles de piloter_bras : butées, chaleur, blocage (les servos RETIENNENT le bras), refus d'un geste
qui enverrait la pince dans la table. Le bouton ARRÊT fige le bras là où il est, sans le lâcher.
Les réglages sont gardés dans reglages_bras.json."""
import json, queue, threading, time
from pathlib import Path
from servos import Bus, ErreurServo, degres, pas, numero_coude, numero_socle
import test_epaule as E, test_pince as P, piloter_bras as B

MILIEU = 2048
FICHIER = Path(__file__).with_name('reglages_bras.json')
DEFAUT = {'vitesse': 300, 'acceleration': 20, 'serrage_doux': P.FORCE_DOUCE, 'serrage_fort': P.FORCE_FERME, 'maintien': P.FORCE_MAINTIEN}
LIMITES = {'vitesse': (80, 800), 'acceleration': (5, 60), 'serrage_doux': (10, 40), 'serrage_fort': (20, 50), 'maintien': (8, 40)}
NOMS = {'vitesse': 'Vitesse des mouvements', 'acceleration': 'Accélération (douceur des départs)', 'serrage_doux': 'Serrage doux (%)',
        'serrage_fort': 'Serrage fort (%)', 'maintien': 'Force gardée une fois l\'objet tenu (%)'}

def charger():
    r = dict(DEFAUT)
    try: r.update({k: v for k, v in json.loads(FICHIER.read_text(encoding='utf-8')).items() if k in DEFAUT})
    except Exception: pass
    return {k: max(LIMITES[k][0], min(LIMITES[k][1], int(v))) for k, v in r.items()}

class Controleur:
    """Tout ce qui parle aux servos, dans un seul fil d'exécution. La fenêtre ne fait que poster des demandes."""
    def __init__(self, port=None, bus=None):
        self.bus = bus or Bus(port); self.q = queue.Queue(); self.journal = queue.Queue(); self.arret = threading.Event()
        self.etat, self.occupe, self.reglages = {}, False, charger(); self.refus = None
        self._preparer(); self._lire()
        threading.Thread(target=self._boucle, daemon=True).start()

    def dire(self, texte): self.journal.put(texte)

    def _preparer(self):
        bus = self.bus; trouves = bus.chercher()
        self.coude, self.socle, self.epaule, self.pince = numero_coude(trouves), numero_socle(trouves), 2, 4
        for i, nom in ((self.epaule, 'épaule'), (self.coude, 'coude'), (self.pince, 'pince')):
            if i not in trouves: raise ErreurServo(f'Servo n° {i} ({nom}) introuvable. Servos qui répondent : {trouves or "aucun"}. Vérifie les câbles et le 12 V, et ferme FD.')
        if not E.SENS.exists(): raise ErreurServo('Épaule pas encore étalonnée : lance d\'abord tester_epaule.bat --coude ' + str(self.coude))
        if not B.SENS_COUDE.exists(): raise ErreurServo('Sens du coude inconnu : lance d\'abord piloter_bras.bat une fois.')
        if not P.SENS.exists(): raise ErreurServo('Pince pas réglée : lance d\'abord tester_pince.bat')
        self.haut = json.loads(E.SENS.read_text(encoding='utf-8'))['haut']; self.sc = json.loads(B.SENS_COUDE.read_text(encoding='utf-8'))['haut']
        self.ouvert = json.loads(P.SENS.read_text())['ouvert']; self.ferme = sum(P.BUTEES_PINCE) - self.ouvert
        ee, ec, ep = bus.etat(self.epaule), bus.etat(self.coude), bus.etat(self.pince)
        if (ee['butee_min'], ee['butee_max']) != E.butees(self.haut): raise ErreurServo('Butées de l\'épaule différentes : relance tester_epaule.bat (étalonnage).')
        if (ec['butee_min'], ec['butee_max']) != B.BUTEES_COUDE: raise ErreurServo('Butées du coude pas réglées : lance tester_coude.bat')
        if (ep['butee_min'], ep['butee_max']) != P.BUTEES_PINCE: raise ErreurServo('Butées de la pince pas réglées : lance tester_pince.bat')
        if self.socle:
            es = bus.etat(self.socle)
            if (es['butee_min'], es['butee_max']) != B.BUTEES_SOCLE: raise ErreurServo('Socle pas étalonné : lance tester_socle.bat')
        self.hauteur = 179.0 if self.socle else 101.0
        self.poignet = B.ID_POIGNET if B.regler_longueurs(trouves) else None      # avec le poignet, le bras est compté plus long
        self.flexion, self.sf = (B.ID_FLEXION if B.FLEXION else None), 1
        if self.flexion:
            import test_flexion as TF
            ef = bus.etat(self.flexion)
            if (ef['butee_min'], ef['butee_max']) != B.BUTEES_FLEXION or not TF.SENS.exists(): raise ErreurServo('Flexion du poignet pas étalonnée : lance tester_flexion.bat')
            self.sf = json.loads(TF.SENS.read_text(encoding='utf-8'))['haut']; bus.limiter_force(self.flexion, 100); bus.retenir(self.flexion)
        if self.poignet:
            ew = bus.etat(self.poignet)
            if (ew['butee_min'], ew['butee_max']) != B.BUTEES_POIGNET or not Path(__file__).with_name('poignet_etalonne.json').exists(): raise ErreurServo('Poignet pas étalonné : lance tester_poignet.bat')
            bus.limiter_force(self.poignet, 50); bus.retenir(self.poignet)
        for i in [self.epaule, self.coude] + ([self.socle] if self.socle else []):
            bus.limiter_force(i, 100); bus.retenir(i)
        self.dire(f"Servos : {trouves}. Coude n° {self.coude}, socle {'n° 1' if self.socle else 'pas monté'}, rotation du poignet {'n° 5' if self.poignet else 'pas montée'}, flexion {'n° 6' if self.flexion else 'pas montée'} (longueur du bras comptée : {B.L_BRAS + B.L_AVANT:.0f} mm). Le bras est tenu là où il est.")

    # ---- lecture ----
    def _angles(self):
        return E.angle(self.bus.etat(self.epaule)['position'], self.haut), degres(self.bus.etat(self.coude)['position'] - MILIEU) * self.sc

    def _etat(self, ident, nom):
        """Lit un servo ; en cas de silence, dit LEQUEL ne répond pas (20/11/2026 : le message ne le disait pas)."""
        try: return self.bus.etat(ident)
        except ErreurServo as err: raise ErreurServo(f'le servo n° {ident} ({nom}) ne répond plus — {err}')

    def _flex(self):
        return degres(self.bus.etat(self.flexion)['position'] - MILIEU) * self.sf if self.flexion else 0.0

    def _roulis(self):
        return degres(self.bus.etat(self.poignet)['position'] - MILIEU) if self.poignet else 0.0

    def _lire(self):
        e1, e2, e3 = self._etat(self.epaule, 'épaule'), self._etat(self.coude, 'coude'), self._etat(self.pince, 'pince')
        ae, ac = E.angle(e1['position'], self.haut), degres(e2['position'] - MILIEU) * self.sc
        d = {'epaule': (ae, e1['charge'], e1['temperature']), 'coude': (ac, e2['charge'], e2['temperature']),
             'pince': (P.ecart_mm(e3['position'], self.ouvert), e3['charge'], e3['temperature']),
             'avant_bras': ae + ac, 'bas_pince': B.bas_de_pince(self.hauteur, ae, ac, self._flex(), self._roulis()), 'tension': e1['tension']}
        if self.socle:
            e0 = self._etat(self.socle, 'socle'); d['socle'] = (degres(e0['position'] - MILIEU), e0['charge'], e0['temperature'])
        if self.flexion:
            e6 = self._etat(self.flexion, 'flexion du poignet'); d['flexion'] = (degres(e6['position'] - MILIEU) * self.sf, e6['charge'], e6['temperature'])
            import geometrie as G; d['pince_plan'] = G.position_plan(ae, ac, d['flexion'][0], self.hauteur)
        if self.poignet:
            e5 = self._etat(self.poignet, 'poignet'); d['poignet'] = (degres(e5['position'] - MILIEU), e5['charge'], e5['temperature'])
        self.etat = d

    # ---- demandes (appelées par la fenêtre) ----
    def demander(self, *cmd): self.arret.clear(); self.q.put(cmd)
    def stop(self): self.arret.set(); self.dire('ARRÊT demandé.')

    def _boucle(self):
        while True:
            try: cmd = self.q.get(timeout=0.35)
            except queue.Empty:
                try: self._lire(); self._muet = None
                except ErreurServo as err:
                    if str(err) != getattr(self, '_muet', None): self.dire(f'Lecture impossible : {err}')   # une seule fois, pas toutes les 0,35 s
                    self._muet = str(err)
                continue
            if cmd[0] == 'fin':
                for i in [self.epaule, self.coude, self.pince] + ([self.socle] if self.socle else []) + ([self.poignet] if self.poignet else []) + ([self.flexion] if self.flexion else []):
                    try: self.bus.relacher(i)
                    except Exception: pass
                self.bus.fermer(); self.etat = {'fini': True}; return
            self.occupe = True
            try: getattr(self, '_' + cmd[0])(*cmd[1:])
            except ErreurServo as err: self.dire(f'Refusé : {err}'); self.refus = str(err)      # la fenêtre l'affiche en rouge et remet les curseurs à leur vraie place
            except Exception as err: self.dire(f'Erreur : {err!r}')
            self.occupe = False
            try: self._lire()
            except ErreurServo: pass

    def _verifier(self, ae, ac, f=None):
        if not E.BAS - 3 <= ae <= E.HAUT + 3: raise ErreurServo(f'épaule à {ae:+.0f}° : hors de −30° à +90°')
        if abs(ac) > B.COUDE_MAX + 3: raise ErreurServo(f'coude à {ac:+.0f}° : hors de ±{B.COUDE_MAX}°')
        z = B.bas_de_pince(self.hauteur, ae, ac, self._flex() if f is None else f, self._roulis())
        if z < 3: raise ErreurServo(f'la pince irait dans la table (bas des mâchoires à {z:.0f} mm)')

    def _bouger(self, cibles, nom, synchro=False):
        for i, _ in cibles: self.bus.limiter_force(i, 100)
        r = self.reglages
        texte = B.aller_ensemble(self.bus, cibles, synchro=synchro, vitesse=r['vitesse'], accel=r['acceleration'], arret=self.arret.is_set)
        self.dire(f'{nom} : {texte}'); return not texte.startswith('ARRÊT')

    def _aller(self, epaule=None, coude=None, socle=None, plat=False, niveau=False):
        ae, ac = self._angles(); niveau = niveau and self.flexion     # niveau : la flexion du poignet garde la pince à l'horizontale
        borne = lambda x: max(-B.FLEXION_MAX, min(B.FLEXION_MAX, x))
        if plat:                                           # avant-bras gardé à l'horizontale : le coude suit l'épaule
            v = ae if epaule is None else epaule; self._verifier(v, -v, 0.0 if niveau else None)
            if niveau and abs(self._flex()) > 3 and not self._bouger([(self.flexion, MILIEU)], 'Poignet remis droit'): return
            if abs(ae + ac) > 3 and not self._bouger([(self.coude, MILIEU + self.sc * pas(-ae))], 'Avant-bras à l\'horizontale'): return
            self._bouger([(self.epaule, E.position(v, self.haut)), (self.coude, MILIEU + self.sc * pas(-v))], f'Épaule à {v:+.0f}°, avant-bras à plat', synchro=True)
        elif epaule is not None or coude is not None:
            ve, vc = (ae if epaule is None else epaule), (ac if coude is None else coude); fc = borne(-(ve + vc)) if niveau else None
            self._verifier(ve, vc, fc); cibles, noms = [], []
            if epaule is not None: cibles.append((self.epaule, E.position(ve, self.haut))); noms.append(f'épaule à {ve:+.0f}°')
            if coude is not None: cibles.append((self.coude, MILIEU + self.sc * pas(vc))); noms.append(f'coude à {vc:+.0f}°')
            if niveau: cibles.append((self.flexion, MILIEU + self.sf * pas(fc))); noms.append(f'pince gardée à plat (poignet à {fc:+.0f}°)')
            self._bouger(cibles, ', '.join(noms).capitalize())
        if socle is not None:
            if not self.socle: raise ErreurServo('pas de socle tournant branché')
            if abs(socle) > B.SOCLE_MAX: raise ErreurServo('socle hors de ±90°')
            self._bouger([(self.socle, MILIEU + pas(socle))], f'Socle à {socle:+.0f}°')

    def _flechir(self, angle):
        if not self.flexion: raise ErreurServo('pas de flexion du poignet branchée (servo n° 6)')
        if abs(angle) > B.FLEXION_MAX: raise ErreurServo('flexion hors de ±90°')
        ae, ac = self._angles(); self._verifier(ae, ac, angle)
        self._bouger([(self.flexion, MILIEU + self.sf * pas(angle))], f'Poignet plié à {angle:+.0f}°')

    # positions de départ selon l'inclinaison de la pince : (mm devant l'épaule, hauteur du milieu des mâchoires, mm).
    # Plus la pince pointe vers le bas, plus elle travaille PRÈS du socle : à plat 36–45 cm, à 45° 34–42 cm, à 70° 26–34 cm, à 90° 19–26 cm.
    DEPART = {0: (400.0, 130.0), -45: (380.0, 120.0), -70: (300.0, 110.0), -90: (220.0, 70.0)}
    NOMS_INCL = {0: 'à plat', -45: 'en biais (45°)', -70: 'presque vers le bas (70°)', -90: 'vers le bas'}

    def _deplacer(self, avance, monte, inclinaison, depart=False):
        """Déplace la PINCE de quelques millimètres (vers l'avant, vers le haut) en gardant son inclinaison : c'est le programme qui
        calcule l'épaule, le coude et le poignet. inclinaison : 0 = pince à plat, −90 = pince pointée vers le bas.
        depart=True : amène d'abord la pince à une position de départ commode, dans cette inclinaison."""
        if not self.flexion: raise ErreurServo('il faut la flexion du poignet (servo n° 6) pour déplacer la pince ainsi')
        import geometrie as G
        nom = self.NOMS_INCL.get(inclinaison, f'inclinée de {inclinaison}°')
        ae, ac = self._angles(); f = self._flex(); s, z, t = G.position_plan(ae, ac, f, self.hauteur)
        if depart: s, z, avance, monte = *self.DEPART[inclinaison], 0, 0
        elif abs(t - inclinaison) > 8: raise ErreurServo(f'la pince n\'est pas encore {nom} : clique d\'abord sur le rond « Pince {nom} »')
        glisse = ''
        try: cible = G.angles_plan(s + avance, z + monte, inclinaison, self.hauteur)
        except G.HorsDePortee as err:
            # Le point demandé est hors de portée : on prend le plus proche en glissant sur l'autre axe (monter en avançant un peu, par
            # exemple), et on le dit. Le 23/11/2026, « Monter » était refusé net à 389 mm de l'épaule : le coude était en butée.
            if depart: raise ErreurServo(f'la pince ne peut pas aller là : {err}')
            try: cible, d = G.au_plus_pres(s + avance, z + monte, inclinaison, self.hauteur, 'avance' if monte else 'hauteur')
            except G.HorsDePortee: raise ErreurServo(f'la pince ne peut pas aller là : {err}')
            if monte: avance += d; glisse = f" (pour y arriver, la pince a aussi {'avancé' if d > 0 else 'reculé'} de {abs(d)} mm)"
            else: monte += d; glisse = f" (pour y arriver, la pince est aussi {'montée' if d > 0 else 'descendue'} de {abs(d)} mm)"
        arrivee = [cible['epaule'], cible['coude'], cible['flexion']]; self._verifier(*arrivee)
        if not G.trajet_sur([ae, ac, f], arrivee, self.hauteur):
            # trajet direct trop près de la table (changement d'inclinaison, pince basse) : on passe par une position haute, pince à plat
            haut = [70.0, -70.0, 0.0]
            if not (depart and G.trajet_sur([ae, ac, f], haut, self.hauteur) and G.trajet_sur(haut, arrivee, self.hauteur)):
                raise ErreurServo('sur ce trajet la pince passerait trop près de la table : clique d\'abord sur « Repos »')
            if not self._bouger([(self.epaule, E.position(haut[0], self.haut)), (self.coude, MILIEU + self.sc * pas(haut[1])), (self.flexion, MILIEU + self.sf * pas(haut[2]))], 'Pince relevée avant de changer d\'inclinaison'): return
        quoi = f"Pince {nom} : {s + avance:.0f} mm devant l'épaule, à {z + monte:.0f} mm de la table{glisse}"
        self._bouger([(self.epaule, E.position(arrivee[0], self.haut)), (self.coude, MILIEU + self.sc * pas(arrivee[1])), (self.flexion, MILIEU + self.sf * pas(arrivee[2]))], quoi)

    def _poignet(self, angle):
        if not self.poignet: raise ErreurServo('pas de poignet branché (servo n° 5)')
        if abs(angle) > B.POIGNET_MAX: raise ErreurServo('poignet hors de ±90°')
        self.bus.limiter_force(self.poignet, 50)                     # force réduite : un câble qui retient la pince arrête le mouvement
        r = self.reglages; texte = B.aller_ensemble(self.bus, [(self.poignet, MILIEU + pas(angle))], vitesse=r['vitesse'], accel=r['acceleration'], arret=self.arret.is_set)
        self.dire(f'Pince tournée de {angle:+.0f}° : {texte}')

    def _repos(self): self._bouger([(self.epaule, E.position(E.REPOS, self.haut)), (self.coude, MILIEU)], f'Repos (bras à {E.REPOS}°, presque à la verticale)')

    def _pince(self, action):
        b, r = self.bus, self.reglages; b.tenir(self.pince)
        if action == 'o':
            b.limiter_force(self.pince, P.FORCE_MOUVEMENT); self.dire('Ouvrir : ' + b.aller(self.pince, self.ouvert, charge_max=P.CHARGE_BLOCAGE))
        else:
            force = r['serrage_doux'] if action == 's' else r['serrage_fort']
            texte, pos, tenu = b.serrer(self.pince, self.ferme, force, maintien=min(r['maintien'], force))
            self.dire('Serrer : ' + texte + (f' · largeur ≈ {P.ecart_mm(pos, self.ouvert):.0f} mm' if tenu else ''))

    def _poser(self):
        ae, ac = self._angles()
        if abs(ae + ac) > 3 and not self._bouger([(self.coude, MILIEU + self.sc * pas(-ae))], 'Avant-bras à l\'horizontale'): return
        self.dire('Poser : descente lente jusqu\'à sentir la table...')
        v, lus = round(self._angles()[0]), []
        while True:
            v -= 1
            if self.arret.is_set(): self.dire('Poser : arrêté.'); return
            if v < E.BAS or B.bas_de_pince(self.hauteur, v, -v, self._flex()) < 5: self.dire('Poser : arrivé en bas sans sentir la table, je n\'ouvre pas.'); return
            texte = B.aller_ensemble(self.bus, [(self.epaule, E.position(v, self.haut)), (self.coude, MILIEU + self.sc * pas(-v))], synchro=True, arret=self.arret.is_set)
            if texte.startswith('ARRÊT'): self.dire('Poser : ' + texte); return
            time.sleep(0.25)
            ce = sum(self.bus.etat(self.epaule)['charge'] for _ in range(3)) / 3; cc = sum(self.bus.etat(self.coude)['charge'] for _ in range(3)) / 3
            lus.append((ce, cc))
            if len(lus) > 3:
                re_, rc = sum(x[0] for x in lus[:3]) / 3, sum(x[1] for x in lus[:3]) / 3
                if abs(ce - re_) >= B.SEUIL_CONTACT or abs(cc - rc) >= B.SEUIL_CONTACT: break
        self.dire(f'Poser : contact senti à {v:+d}°.')
        B.aller_ensemble(self.bus, [(self.epaule, E.position(v + 1, self.haut)), (self.coude, MILIEU + self.sc * pas(-v - 1))], synchro=True)
        self._pince('o'); h = min(E.HAUT, v + 20)
        self._bouger([(self.epaule, E.position(h, self.haut)), (self.coude, MILIEU + self.sc * pas(-h))], 'Remonter', synchro=True)

    def regler(self, cle, valeur):
        self.reglages[cle] = max(LIMITES[cle][0], min(LIMITES[cle][1], int(float(valeur))))
        try: FICHIER.write_text(json.dumps(self.reglages, indent=1), encoding='utf-8')
        except Exception: pass

def fenetre(ctrl):
    import tkinter as tk
    from tkinter import ttk, messagebox
    f = tk.Tk(); f.title('Bras de Câlin — commande'); f.geometry('760x760')
    gros = ('Segoe UI', 11); titre = ('Segoe UI', 12, 'bold')
    cadre = ttk.LabelFrame(f, text=' Articulations (lâche le curseur pour envoyer) '); cadre.pack(fill='x', padx=10, pady=6)
    curseurs, etats = {}, {}
    plat = tk.BooleanVar(value=False); niveau = tk.BooleanVar(value=False)
    def envoyer(nom):
        v = curseurs[nom].get()
        if nom == 'epaule': ctrl.demander('aller', v, None, None, plat.get(), niveau.get())
        elif nom == 'coude': ctrl.demander('aller', None, v, None, False, niveau.get())
        elif nom == 'flexion': ctrl.demander('flechir', v)
        elif nom == 'poignet': ctrl.demander('poignet', v)
        else: ctrl.demander('aller', None, None, v, False)
    lignes = [('socle', 'Socle (− gauche · + droite, vu de derrière)', -90, 90), ('epaule', 'Épaule (lever)', -30, 90), ('coude', 'Coude (plier)', -90, 90), ('flexion', 'Poignet (plier : + vers le haut)', -90, 90), ('poignet', 'Poignet (− droite · + gauche, vu de derrière)', -90, 90)]
    for k, (nom, texte, mini, maxi) in enumerate(lignes):
        ttk.Label(cadre, text=texte, font=titre, width=15).grid(row=k, column=0, padx=6, pady=8, sticky='w')
        c = tk.Scale(cadre, from_=mini, to=maxi, orient='horizontal', length=330, resolution=1, font=gros); c.grid(row=k, column=1)
        c.bind('<ButtonRelease-1>', lambda ev, n=nom: envoyer(n)); c.bind('<KeyRelease>', lambda ev, n=nom: envoyer(n)); curseurs[nom] = c
        etats[nom] = ttk.Label(cadre, text='', font=gros, width=30); etats[nom].grid(row=k, column=2, padx=8, sticky='w')
        if (nom == 'socle' and not ctrl.socle) or (nom == 'poignet' and not ctrl.poignet) or (nom == 'flexion' and not ctrl.flexion): c.configure(state='disabled'); etats[nom].configure(text='pas monté')
    ttk.Checkbutton(cadre, text='Garder l\'avant-bras à l\'horizontale quand l\'épaule bouge (pour porter un verre)', variable=plat).grid(row=5, column=0, columnspan=3, sticky='w', padx=6, pady=4)
    c2 = ttk.Checkbutton(cadre, text='Garder la PINCE à l\'horizontale avec le poignet, quand l\'épaule ou le coude bougent', variable=niveau); c2.grid(row=6, column=0, columnspan=3, sticky='w', padx=6, pady=2)
    if not ctrl.flexion: c2.configure(state='disabled')
    resume = ttk.Label(cadre, text='', font=gros); resume.grid(row=7, column=0, columnspan=3, sticky='w', padx=6, pady=4)
    alerte = ttk.Label(cadre, text='', font=titre, foreground='#b00', wraplength=900); alerte.grid(row=8, column=0, columnspan=3, sticky='w', padx=6, pady=2)

    cd = ttk.LabelFrame(f, text=' Déplacer la pince (le programme règle tout seul l\'épaule, le coude et le poignet) '); cd.pack(fill='x', padx=10, pady=6)
    incl = tk.IntVar(value=1); pas_mm = tk.IntVar(value=20)          # aucun rond coché au départ : on choisit d'abord « à plat » ou « vers le bas »
    for k, (texte, av, mo) in enumerate([('Reculer', -1, 0), ('Avancer', 1, 0), ('Descendre', 0, -1), ('Monter', 0, 1)]):
        b = tk.Button(cd, text=texte, font=titre, width=13, command=lambda av=av, mo=mo: ctrl.demander('deplacer', av * pas_mm.get(), mo * pas_mm.get(), incl.get())); b.grid(row=0, column=k, padx=4, pady=6)
        if not ctrl.flexion: b.configure(state='disabled')
    cpas = ttk.Frame(cd); cpas.grid(row=0, column=4, padx=10)
    ttk.Label(cpas, text='de', font=gros).pack(side='left')
    for v in (10, 20, 50, 100): ttk.Radiobutton(cpas, text=f'{v // 10} cm', variable=pas_mm, value=v).pack(side='left', padx=2)
    for k, (texte, v) in enumerate([('Pince à plat (par le côté, loin : 36 à 45 cm)', 0), ('En biais à 45° (34 à 42 cm)', -45), ('Presque vers le bas, 70° (26 à 34 cm)', -70), ('Vers le bas (par le dessus, près : 19 à 26 cm)', -90)]):
        r = ttk.Radiobutton(cd, text=texte, variable=incl, value=v, command=lambda: ctrl.demander('deplacer', 0, 0, incl.get(), True)); r.grid(row=1 + k // 2, column=2 * (k % 2), columnspan=3, sticky='w', padx=6)
        if not ctrl.flexion: r.configure(state='disabled')
    ou = ttk.Label(cd, text='', font=gros); ou.grid(row=3, column=0, columnspan=5, sticky='w', padx=6, pady=2)

    cp = ttk.LabelFrame(f, text=' Pince '); cp.pack(fill='x', padx=10, pady=6)
    for k, (texte, a) in enumerate([('Ouvrir', 'o'), ('Serrer doux', 's'), ('Serrer fort', 'S')]):
        tk.Button(cp, text=texte, font=titre, width=13, command=lambda a=a: ctrl.demander('pince', a)).grid(row=0, column=k, padx=6, pady=8)
    etats['pince'] = ttk.Label(cp, text='', font=gros, width=32); etats['pince'].grid(row=0, column=3, padx=8)

    cg = ttk.LabelFrame(f, text=' Gestes '); cg.pack(fill='x', padx=10, pady=6)
    tk.Button(cg, text='Repos (bras en haut)', font=titre, command=lambda: ctrl.demander('repos')).grid(row=0, column=0, padx=6, pady=8)
    tk.Button(cg, text='Poser sur la table', font=titre, command=lambda: ctrl.demander('poser')).grid(row=0, column=1, padx=6)
    tk.Button(cg, text='ARRÊT', font=('Segoe UI', 14, 'bold'), bg='#d0302a', fg='white', width=12, command=ctrl.stop).grid(row=0, column=2, padx=30)

    cr = ttk.LabelFrame(f, text=' Réglages (enregistrés tout seuls) '); cr.pack(fill='x', padx=10, pady=6)
    for k, cle in enumerate(DEFAUT):
        ttk.Label(cr, text=NOMS[cle], font=gros, width=36).grid(row=k, column=0, padx=6, sticky='w')
        s = tk.Scale(cr, from_=LIMITES[cle][0], to=LIMITES[cle][1], orient='horizontal', length=300, font=gros, command=lambda v, c=cle: ctrl.regler(c, v))
        s.set(ctrl.reglages[cle]); s.grid(row=k, column=1)
    ttk.Label(cr, text='Vitesse : 300 = lent et sûr (réglage des essais). Monte par petites marches.', font=('Segoe UI', 9)).grid(row=9, column=0, columnspan=2, sticky='w', padx=6)

    journal = tk.Text(f, height=5, font=('Consolas', 10), state='disabled'); journal.pack(fill='both', expand=True, padx=10, pady=6)
    premier = [True]; recaler = [False]
    def rafraichir():
        e = ctrl.etat
        if e.get('fini'): f.destroy(); return
        remettre = premier[0] or recaler[0]; recaler[0] = False
        if ctrl.occupe: alerte.configure(text='')
        for nom in ('socle', 'epaule', 'coude', 'poignet', 'flexion'):
            if nom in e:
                a, ch, t = e[nom]; etats[nom].configure(text=f'{a:+.0f}° · charge {ch:+.0f} % · {t} °C', foreground='#b00' if t >= 50 or abs(ch) >= 50 else '#000')
                if remettre: curseurs[nom].set(round(a))
        if 'pince' in e:
            a, ch, t = e['pince']; etats['pince'].configure(text=f'≈ {a:.0f} mm · charge {ch:+.0f} % · {t} °C', foreground='#b00' if t >= 50 else '#000')
            if 'pince_plan' in e: ou.configure(text=f"La pince est à {e['pince_plan'][0]:.0f} mm devant l'épaule, à {e['pince_plan'][1]:.0f} mm au-dessus de la table, inclinée de {e['pince_plan'][2]:+.0f}°")
            if ctrl.refus:                                   # geste refusé : on le dit en gros, et les curseurs reviennent à la position réelle
                alerte.configure(text='GESTE REFUSÉ : ' + ctrl.refus); ctrl.refus = None; recaler[0] = True
            resume.configure(text=f"Avant-bras : {e['avant_bras']:+.0f}° par rapport à l'horizontale · bas de la pince à {e['bas_pince']:.0f} mm de la table · {e['tension']:.1f} V"
                             + ('   ·   EN MOUVEMENT' if ctrl.occupe else ''))
            premier[0] = False
        while not ctrl.journal.empty():
            journal.configure(state='normal'); journal.insert('end', time.strftime('%H:%M:%S  ') + ctrl.journal.get() + '\n'); journal.see('end'); journal.configure(state='disabled')
        f.after(300, rafraichir)
    def quitter():
        if messagebox.askokcancel('Quitter', 'La force va être coupée : le bras va TOMBER s\'il n\'est pas tenu.\n\nTiens le bras (ou pose-le), puis clique sur OK.'):
            ctrl.stop(); ctrl.q.put(('fin',))
    f.protocol('WM_DELETE_WINDOW', quitter); rafraichir(); f.mainloop()

if __name__ == '__main__':
    try: ctrl = Controleur()
    except ErreurServo as err:
        try:
            import tkinter as tk; from tkinter import messagebox
            r = tk.Tk(); r.withdraw(); messagebox.showerror('Bras de Câlin', str(err))
        except Exception: pass
        raise SystemExit(str(err))
    fenetre(ctrl)
