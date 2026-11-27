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
import math, queue, sys, time
from servos import Bus, ErreurServo, degres, pas
import test_epaule as E, test_pince as P, piloter_bras as B, geometrie as G
from controle_bras import Controleur, MILIEU

class Pointeur:
    def __init__(self, bus=None, port=None, demander=input, dire=print):
        self.c = Controleur.__new__(Controleur); c = self.c
        c.bus = bus or Bus(port); c.journal = queue.Queue(); c.reglages = {'vitesse': 300, 'acceleration': 20, 'serrage_doux': P.FORCE_DOUCE, 'serrage_fort': P.FORCE_FERME, 'maintien': P.FORCE_MAINTIEN}
        import threading; c.arret = threading.Event()
        c._preparer(); self.demander, self.dire, self.prise, self.haut, self.incl = demander, dire, None, None, 0.0
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
        ae, ac, f = self.angles(); bas = B.bas_de_pince(c.hauteur, ae, ac, f, roulis=0.0)
        if bas < B.MARGE_TABLE and arrivee[0] > ae + 1:
            # Le bras a fléchi sous son poids : la pince est plus bas que prévu, sous la garde de la table. On la dégage d'abord en
            # relevant l'épaule seule de 15° (tout le bras monte), puis on fait le geste demandé. Sans cela, « m » et « r » étaient
            # refusés et le bras restait bloqué en bas (Nicolas, 24/11/2026).
            self.dire(f'   La pince est plus bas que prévu ({bas:.0f} mm de la table par le calcul, le bras fléchit) : je la dégage d\'abord.')
            if not c._bouger([(c.epaule, E.position(min(ae + 15, E.REPOS), c.haut))], 'Dégagement, épaule relevée'): self.vider(); return False
            self.vider()
        if not G.trajet_sur(list(self.angles()), arrivee, c.hauteur): raise ErreurServo('sur ce trajet la pince passerait trop près de la table (rien n\'a bougé). Essaie « r » (repos) ; si « r » est refusé aussi, quitte avec « q » en TENANT le bras.')
        ok = c._bouger([(c.epaule, E.position(arrivee[0], c.haut)), (c.coude, MILIEU + c.sc * pas(arrivee[1])), (c.flexion, MILIEU + c.sf * pas(arrivee[2]))], nom)
        self.vider(); return ok

    def preparer(self, X, Y, imposee=None, leve=0.0):
        """Calcule le geste pour saisir en (X, Y) et l'annonce, SANS bouger. Renvoie (prise, approche), ou None si c'est impossible."""
        c = self.c
        try: incl, prise, haut = G.choisir_inclinaison(X, Y, c.hauteur, imposee, leve)
        except G.HorsDePortee as e:
            if imposee is not None:
                bd = G.bande(imposee, c.hauteur, math.degrees(math.atan2(X, Y)))
                self.dire(f'   Impossible avec la pince inclinée de {abs(imposee):.0f}° ({e}). ' + (f'Dans cette direction, il faut poser entre {bd[0]} et {bd[1]} mm du socle.' if bd else 'Aucune distance possible dans cette direction.')); return
            z = G.zone_toutes(c.hauteur); self.dire(f'   Hors de portée : {e}. Zone possible droit devant : de {z[0]} à {z[1]} mm du socle.'); return
        comment = 'à plat' if abs(incl) < 1 else 'pointée vers le bas' if incl <= -89 else f'inclinée de {abs(incl):.0f}° vers le bas'
        self.incl = incl
        self.dire(f"   Pour saisir en X {X:+.0f}, Y {Y:+.0f}, pince {comment}{'' if imposee is None else ' (demandé)'} : socle {prise['socle']:+.0f}°, épaule {prise['epaule']:+.0f}°, coude {prise['coude']:+.0f}°, poignet {prise['flexion']:+.0f}°")
        if imposee is None and abs(incl) >= 1: self.dire('   (à plat, ce point est trop près : j\'incline la pince juste ce qu\'il faut)')
        self.dire(f"   D'abord au-dessus : épaule {haut['epaule']:+.0f}°, coude {haut['coude']:+.0f}°, poignet {haut['flexion']:+.0f}° (pince à {G.ou_est_la_pince(**haut, hauteur_epaule=c.hauteur)[2]:.0f} mm de la table)")
        if abs(c._roulis()) > 15 and not getattr(self, 'roulis_permis', False): self.dire('   La pince est tournée : remets-la droite d\'abord (fenêtre de contrôle, ou tester_poignet).'); return
        return prise, haut

    def aller(self, prise, haut, relever=False):
        """Fait le geste préparé : relève le bras s'il faut tourner, tourne le socle, place la pince au-dessus du point.
        relever : passer TOUJOURS par le bras relevé avant de tourner. Pour un bac : sans cela, la pince partait d'une position
        basse et montait en biais vers le bac, en frôlant son bord (Nicolas, 26/11/2026 : « encore un peu de frottement »)."""
        c = self.c; ae, ac, _ = self.angles()
        if (relever or ae < 55) and abs(degres(c.bus.etat(c.socle)['position'] - MILIEU) - prise['socle']) > 3:
            if not self.poser_bras({'epaule': E.REPOS, 'coude': 0, 'flexion': 0}, 'Bras relevé avant de tourner'): return     # on ne tourne pas bras baissé : il balaierait la table
        if not c._bouger([(c.socle, MILIEU + pas(prise['socle']))], f"Socle à {prise['socle']:+.0f}°"): self.vider(); return
        self.vider()
        if self.poser_bras(haut, 'Pince au-dessus du point'): self.prise, self.haut = prise, haut

    def viser(self, X, Y, imposee=None):
        plan = self.preparer(X, Y, imposee)
        if plan and self.demander('   J\'y vais ? (o/n) ').strip().lower().startswith('o'): self.aller(*plan)

    def descendre_au_contact(self, X, Y, pas_mm=4.0, remonte=4.0, plancher=-6.0, d_un_trait=14.0):
        """Pour les objets BAS (1 à 2 cm, demande de Nicolas du 27/11/2026) : depuis la position de prise, où le bas de la pince est
        à 22 mm de la table par le calcul, la pince continue de descendre À LA VERTICALE du point (X, Y), par marches de 3 mm,
        en surveillant l'effort de l'épaule, du coude et du poignet. Dès que l'effort change d'un coup (les mâchoires touchent
        la table ou l'objet), elle remonte d'une marche et s'arrête : les mâchoires sont au ras de la table, quelle que soit la
        flexion du bras, sans forcer. Sans contact senti, elle s'arrête quand les servos se lisent à 3 mm de la table, ou au plus
        tard quand le calcul la place `plancher` mm sous la table.
        Renvoie (contact senti ?, hauteur calculée du bas de la pince à l'arrêt)."""
        c = self.c; incl = self.incl; z0 = G.hauteur_prise(incl); garde = z0 - (B.MARGE_TABLE + 2.0)      # du milieu des mâchoires à leur point le plus bas
        poser = lambda a, nom: c._bouger([(c.epaule, E.position(a['epaule'], c.haut)), (c.coude, MILIEU + c.sc * pas(a['coude'])), (c.flexion, MILIEU + c.sf * pas(a['flexion']))], nom)
        effort = lambda: [sum(c.bus.etat(i)['charge'] for _ in range(3)) / 3 for i in (c.epaule, c.coude, c.flexion)]
        # Pour ne pas y passer des heures (Nicolas, 27/11/2026) : la première partie se fait D'UN TRAIT, jusqu'à 14 mm de la table par
        # le calcul (le bras fléchit de 3 à 8 mm : il reste de la marge), puis des marches de 4 mm, 2 lectures d'effort au lieu de 3,
        # 0,1 s de pause au lieu de 0,2 : 3 marches au plus dans le cas courant, environ 2 secondes en tout.
        effort = lambda: [sum(c.bus.etat(i)['charge'] for _ in range(2)) / 2 for i in (c.epaule, c.coude, c.flexion)]
        z, prec, contact = z0, dict(self.prise), False
        try:
            a = G.angles_pour(X, Y, garde + d_un_trait, c.hauteur, incl)
            if poser(a, f'Descente rapide : bas de la pince à {d_un_trait:.0f} mm par le calcul'): z, prec = garde + d_un_trait, a
        except G.HorsDePortee: pass
        time.sleep(0.1); avant = effort()
        while z - pas_mm - garde >= plancher:
            if c.arret.is_set(): break
            try: a = G.angles_pour(X, Y, z - pas_mm, c.hauteur, incl)
            except G.HorsDePortee: break
            if not poser(a, f'Descente au contact : bas de la pince à {z - pas_mm - garde:.0f} mm par le calcul'): break
            z -= pas_mm; time.sleep(0.1); apres = effort()
            if max(abs(x - y) for x, y in zip(apres, avant)) >= B.SEUIL_CONTACT:
                contact = True; poser(prec, f'Contact senti : je remonte de {remonte:.0f} mm'); z += pas_mm; break
            avant, prec = apres, a
            # deuxième sécurité : la hauteur LUE sur les servos (ils s'arrêtent 1 à 2° sous la consigne : le bras est plus bas que
            # le calcul ne le dit). À 3 mm de la table d'après eux, on s'arrête même si aucun effort n'a été senti.
            lu = B.bas_de_pince(c.hauteur, *self.angles(), roulis=0.0)
            if lu <= 3.0: self.dire(f'   Les servos se lisent à {lu:.0f} mm de la table : je m\'arrête là.'); break
        self.prise = dict(prec, socle=self.prise['socle']); self.vider()
        self.dire(f'   {"Table sentie" if contact else "Pas de contact senti"} : bas de la pince à {z - garde:.0f} mm de la table par le calcul.')
        return contact, z - garde

    def descendre(self):
        if not self.prise: self.dire('   Vise d\'abord un point : v X Y'); return False
        return self.poser_bras(self.prise, 'Descente sur le point')
    def monter(self):
        if not self.haut: self.dire('   Vise d\'abord un point : v X Y'); return False
        return self.poser_bras(self.haut, 'Remontée')
    def monter_droit(self, hauteur=40.0, marche=20.0, decale=0.0):
        """Après avoir lâché un objet : la pince monte À LA VERTICALE de `hauteur` mm, sans changer d'inclinaison, avant la remontée
        habituelle. Celle-ci n'est pas verticale (épaule, coude et poignet tournent chacun vers leur angle d'arrivée, et quand le
        bras a fléchi l'épaule se relève d'abord SEULE de 15° : la pince avance alors de 3 cm en penchant) : une mâchoire
        accrochait le petit cylindre qu'elle venait de poser et le couchait (Nicolas, 27/11/2026 : « quand le bras remonte »).
        decale : avant de monter, la pince ouverte se décale de `decale` mm vers SA droite (vu de derrière le bras ; négatif = vers
        la gauche), pour écarter du pion la mâchoire qui le touche encore : son tapis antidérapant le soulève en montant (idée
        de Nicolas, 27/11/2026 : « ça accroche encore à droite »). Rien si la pince est tournée (les mâchoires ne sont plus de côté).
        On part de la position de prise calculée, on monte vers le haut : pas de contrôle de garde de table à faire."""
        c = self.c
        if not self.prise: return False
        x, y, z, incl = G.ou_est_la_pince(**{k: self.prise[k] for k in ('socle', 'epaule', 'coude', 'flexion')}, hauteur_epaule=c.hauteur)
        def poser(a, nom, avec_socle=False):
            try: c._verifier(a['epaule'], a['coude'], a['flexion'])
            except ErreurServo: return False
            ordres = [(c.epaule, E.position(a['epaule'], c.haut)), (c.coude, MILIEU + c.sc * pas(a['coude'])), (c.flexion, MILIEU + c.sf * pas(a['flexion']))]
            return c._bouger(([(c.socle, MILIEU + pas(a['socle']))] if avec_socle else []) + ordres, nom)
        fait, socle = False, self.prise['socle']
        if abs(decale) >= 0.5 and abs(c._roulis()) <= 15:
            R = math.hypot(x, y); xd, yd = x + decale * y / R, y - decale * x / R        # vers la droite de la pince, vue de derrière
            try:
                a = G.angles_pour(xd, yd, z + 2.0, c.hauteur, incl)
                if abs(a['socle'] - socle) <= 4.0 and poser(a, f'Pince décalée de {abs(decale):.0f} mm vers la {"droite" if decale > 0 else "gauche"}', True): x, y, socle, fait = xd, yd, a['socle'], True
            except G.HorsDePortee: pass
        dz = marche
        while dz <= hauteur + 0.1 and not c.arret.is_set():
            try: a = G.angles_pour(x, y, z + dz, c.hauteur, incl)
            except G.HorsDePortee: break
            if abs(a['socle'] - socle) > 1.0: break                                   # pas la même solution : on laisse la remontée habituelle
            if not poser(a, f'Montée droite de {dz:.0f} mm'): break
            fait = True; dz += marche
        self.vider(); return fait
    def glisser(self, X, Y, en_bas):
        """Petit déplacement de la pince vers un point voisin (X, Y), sans changer son inclinaison ni remonter : socle, épaule,
        coude et poignet bougent ensemble. en_bas : la pince est descendue sur le point (sinon elle est à l'approche)."""
        c = self.c
        if not self.prise: self.dire('   Vise d\'abord un point.'); return False
        prise, haut = G.prise_et_approche(X, Y, c.hauteur, self.incl)
        cible = prise if en_bas else haut; arrivee = [cible['epaule'], cible['coude'], cible['flexion']]
        c._verifier(*arrivee)
        if not G.trajet_sur(list(self.angles()), arrivee, c.hauteur): raise ErreurServo('ce décalage ferait passer la pince trop près de la table (rien n\'a bougé)')
        ok = c._bouger([(c.socle, MILIEU + pas(cible['socle'])), (c.epaule, E.position(arrivee[0], c.haut)), (c.coude, MILIEU + c.sc * pas(arrivee[1])), (c.flexion, MILIEU + c.sf * pas(arrivee[2]))], 'Pince décalée')
        self.vider()
        if ok: self.prise, self.haut = prise, haut
        return ok
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
    return terminer(p)

def terminer(p):
    """La fin commune : on ne coupe la force qu'une fois le bras tenu."""
    c = p.c
    print('\nLa force va être coupée : le bras va TOMBER s\'il n\'est pas tenu.')
    try:
        input('TIENS le bras et la pince, ou pose-les, puis Entrée... ')
        for i in [c.epaule, c.coude, c.pince, c.socle, c.flexion] + ([c.poignet] if c.poignet else []): c.bus.relacher(i)
        print('Force coupée. Au revoir.')
    except (Exception, KeyboardInterrupt): print('\n⚠️  Les servos retiennent peut-être encore le bras : TIENS-LE avant de couper le 12 V.')
    c.bus.fermer(); return 0

if __name__ == '__main__': sys.exit(main())
