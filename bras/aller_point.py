"""Envoyer la pince à un point de la table. Premier essai du « aller à un point », sans caméra :
on tape la position à la main (celle que donne camera\\voir_table.bat, ou mesurée à la règle).

Lancer : aller_point.bat (FD et la fenêtre de contrôle fermés, 12 V allumé). Il faut le poignet complet et tous les étalonnages.
Repère : origine sur l'axe du socle, X vers la droite du robot (vu de derrière), Y vers l'avant, en millimètres.
Commandes :
  v X Y   viser le point : le programme CHOISIT L'INCLINAISON de la pince (à plat si possible, sinon inclinée vers le bas juste
          ce qu'il faut, jusqu'à pointée vers le bas), affiche les angles, demande confirmation, tourne le socle et place la
          pince AU-DESSUS du point. Exemple : v 0 400.   v X Y 45 : impose une inclinaison de 45° vers le bas.
  d       descendre sur le point (hauteur de prise : bas des mâchoires à 2 cm de la table par le calcul, moins en vrai)
  m       remonter au-dessus      o / s   ouvrir / serrer la pince
  r       repos                   i       où est la pince        q   quitter
Chaque geste est vérifié avant d'être fait (butées, table) ; un geste arrêté RETIENT le bras."""
import queue, sys
from servos import Bus, ErreurServo, degres, pas
import test_epaule as E, test_pince as P, piloter_bras as B, geometrie as G
from controle_bras import Controleur, MILIEU

class Pointeur:
    def __init__(self, bus=None, port=None, demander=input, dire=print):
        self.c = Controleur.__new__(Controleur); c = self.c
        c.bus = bus or Bus(port); c.journal = queue.Queue(); c.reglages = {'vitesse': 300, 'acceleration': 20, 'serrage_doux': P.FORCE_DOUCE, 'serrage_fort': P.FORCE_FERME, 'maintien': P.FORCE_MAINTIEN}
        import threading; c.arret = threading.Event()
        c._preparer(); self.demander, self.dire, self.prise, self.haut = demander, dire, None, None
        if not (c.socle and c.flexion): raise ErreurServo('Il faut le socle (n° 1) et la flexion du poignet (n° 6) pour aller à un point.')
        self.vider()

    def vider(self):
        while not self.c.journal.empty(): self.dire('   ' + self.c.journal.get())
    def angles(self):
        c = self.c; ae, ac = c._angles(); return ae, ac, c._flex()
    def poser_bras(self, cible, nom):
        """Épaule, coude et poignet ensemble vers un jeu d'angles, après vérification du trajet."""
        c = self.c; arrivee = [cible['epaule'], cible['coude'], cible['flexion']]
        c._verifier(*arrivee)
        if not G.trajet_sur(list(self.angles()), arrivee, c.hauteur): raise ErreurServo('sur ce trajet la pince passerait trop près de la table : fais d\'abord « r » (repos)')
        ok = c._bouger([(c.epaule, E.position(arrivee[0], c.haut)), (c.coude, MILIEU + c.sc * pas(arrivee[1])), (c.flexion, MILIEU + c.sf * pas(arrivee[2]))], nom)
        self.vider(); return ok

    def viser(self, X, Y, imposee=None):
        c = self.c
        try: incl, prise, haut = G.choisir_inclinaison(X, Y, c.hauteur, imposee)
        except G.HorsDePortee as e:
            z = G.zone_toutes(c.hauteur); self.dire(f'   Hors de portée : {e}. Zone possible droit devant : de {z[0]} à {z[1]} mm du socle.'); return
        comment = 'à plat' if abs(incl) < 1 else 'pointée vers le bas' if incl <= -89 else f'inclinée de {abs(incl):.0f}° vers le bas'
        self.dire(f"   Pour saisir en X {X:+.0f}, Y {Y:+.0f}, pince {comment}{'' if imposee is None else ' (demandé)'} : socle {prise['socle']:+.0f}°, épaule {prise['epaule']:+.0f}°, coude {prise['coude']:+.0f}°, poignet {prise['flexion']:+.0f}°")
        if imposee is None and abs(incl) >= 1: self.dire('   (à plat, ce point est trop près : j\'incline la pince juste ce qu\'il faut)')
        self.dire(f"   D'abord au-dessus : épaule {haut['epaule']:+.0f}°, coude {haut['coude']:+.0f}°, poignet {haut['flexion']:+.0f}° (pince à {G.ou_est_la_pince(**haut, hauteur_epaule=c.hauteur)[2]:.0f} mm de la table)")
        if abs(c._roulis()) > 15: self.dire('   La pince est tournée : remets-la droite d\'abord (fenêtre de contrôle, ou tester_poignet).'); return
        if not self.demander('   J\'y vais ? (o/n) ').strip().lower().startswith('o'): return
        ae, ac, _ = self.angles()
        if ae < 55 and abs(degres(c.bus.etat(c.socle)['position'] - MILIEU) - prise['socle']) > 3:
            if not self.poser_bras({'epaule': E.REPOS, 'coude': 0, 'flexion': 0}, 'Bras relevé avant de tourner'): return     # on ne tourne pas bras baissé : il balaierait la table
        if not c._bouger([(c.socle, MILIEU + pas(prise['socle']))], f"Socle à {prise['socle']:+.0f}°"): self.vider(); return
        self.vider()
        if self.poser_bras(haut, 'Pince au-dessus du point'): self.prise, self.haut = prise, haut

    def descendre(self):
        if not self.prise: self.dire('   Vise d\'abord un point : v X Y'); return
        self.poser_bras(self.prise, 'Descente sur le point')
    def monter(self):
        if not self.haut: self.dire('   Vise d\'abord un point : v X Y'); return
        self.poser_bras(self.haut, 'Remontée')
    def repos(self):
        self.poser_bras({'epaule': E.REPOS, 'coude': 0, 'flexion': 0}, 'Repos'); self.prise = self.haut = None
    def infos(self):
        c = self.c; ae, ac, f = self.angles(); so = degres(c.bus.etat(c.socle)['position'] - MILIEU)
        x, y, z, t = G.ou_est_la_pince(so, ae, ac, f, c.hauteur)
        self.dire(f'   socle {so:+.0f}°, épaule {ae:+.0f}°, coude {ac:+.0f}°, poignet {f:+.0f}° → pince en X {x:+.0f}, Y {y:+.0f}, à {z:.0f} mm de la table, inclinée de {t:+.0f}°')

    def boucle(self):
        c = self.c; z, zt = G.zone(G.H_PRISE, c.hauteur), G.zone_toutes(c.hauteur)
        self.dire(f'Zone atteinte droit devant : de {zt[0]} à {zt[1]} mm de l\'axe du socle (pince à plat de {z[0]} à {z[1]} mm ; plus près, je l\'incline).')
        self.dire('Commandes : v X Y (viser) · v X Y 45 (viser, pince inclinée de 45°) · d (descendre) · m (remonter) · o / s (pince) · r (repos) · i (infos) · q (quitter)')
        while True:
            mots = self.demander('> ').replace(',', '.').split()
            if not mots: continue
            try:
                if mots[0] == 'q': break
                elif mots[0] == 'v' and len(mots) in (3, 4):
                    incl = None if len(mots) == 3 else -abs(float(mots[3]))                 # 4e nombre : inclinaison voulue, vers le bas
                    if incl is not None and incl < -90: raise ErreurServo('inclinaison entre 0 (à plat) et 90 (pointée vers le bas)')
                    self.viser(float(mots[1]), float(mots[2]), incl)
                elif mots[0] == 'd': self.descendre()
                elif mots[0] == 'm': self.monter()
                elif mots[0] == 'r': self.repos()
                elif mots[0] == 'i': self.infos()
                elif mots[0] in ('o', 's'): c._pince(mots[0]); self.vider()
                else: self.dire('   commande inconnue (rien n\'a bougé). Exemple : v 0 400')
            except ValueError: self.dire('   il faut deux nombres : v X Y, par exemple v -50 380')
            except ErreurServo as err: self.dire(f'   Refusé : {err}'); self.vider()

def main():
    try: p = Pointeur()
    except ErreurServo as err: print('Impossible de commencer :', err); return 1
    try: p.boucle()
    except KeyboardInterrupt: print('\nInterrompu : le bras reste tenu.')
    c = p.c
    print('\nLa force va être coupée : le bras va TOMBER s\'il n\'est pas tenu.')
    try:
        input('TIENS le bras et la pince, ou pose-les, puis Entrée... ')
        for i in [c.epaule, c.coude, c.pince, c.socle, c.flexion] + ([c.poignet] if c.poignet else []): c.bus.relacher(i)
        print('Force coupée. Au revoir.')
    except (Exception, KeyboardInterrupt): print('\n⚠️  Les servos retiennent peut-être encore le bras : TIENS-LE avant de couper le 12 V.')
    c.bus.fermer(); return 0

if __name__ == '__main__': sys.exit(main())
