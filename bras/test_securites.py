"""Essais des sécurités de servos.py sur un faux servo (aucun matériel). Lancer : python test_securites.py
Chaque ligne « ok » est une sécurité vérifiée ; le programme s'arrête en erreur à la première qui ne marche pas."""
import time
from servos import Bus, ErreurServo
from servo_simule import ServoSimule

def bus_avec(**k):
    s = ServoSimule(**k); return Bus(paquets=s), s

def refuse(fonction, *a, **k):
    try: fonction(*a, **k)
    except ErreurServo as e: return str(e)
    raise AssertionError('aurait dû être refusé')

# 1. sans butées : aucun mouvement
b, s = bus_avec()
assert 'butées non réglées' in refuse(b.aller, 1, 2100); print('ok  sans butées dans le servo : mouvement refusé')
# 2. butées écrites, mémoire reverrouillée
b.regler_butees(1, 1663, 2433); assert (s.butee_min, s.butee_max, s.verrou) == (1663, 2433, 1); print('ok  butées écrites, mémoire reverrouillée')
# 3. mouvement normal
r = b.aller(1, 2300); assert r.startswith('arrivé') and abs(s.pos - 2300) < 2, r; print('ok  mouvement normal :', r)
# 4. hors butées
assert 'hors des butées' in refuse(b.aller, 1, 2500); print('ok  cible hors butées : refusée')
# 5. servo trop chaud
b2, s2 = bus_avec(butees=(1663, 2433), temperature=60)
assert 'trop chaud' in refuse(b2.aller, 1, 2100); print('ok  servo à 60 °C : refus de partir')
# 6. pince coincée, force limitée à 50 % : le cas de l'essai du 14/11/2026
b3, s3 = bus_avec(butees=(1663, 2433), obstacle=2200)
b3.limiter_force(1, 50); t = time.time(); r = b3.aller(1, 2400, charge_max=35); d = time.time() - t
assert r.startswith('ARRÊT') and not s3.force and d < 2.0, (r, d); print(f'ok  coincé avec la force limitée à 50 % : force coupée en {d:.1f} s —', r[:38])
# 7. même chose si on oublie de baisser le seuil (seuil 70 % jamais atteint) : le deuxième filet coupe quand même
b4, s4 = bus_avec(butees=(1663, 2433), obstacle=2200)
b4.limiter_force(1, 50); t = time.time(); r = b4.aller(1, 2400); d = time.time() - t
assert 'n\'avance plus' in r and not s4.force and d < 2.5, (r, d); print(f'ok  seuil trop haut (l\'ancien défaut) : coupé quand même en {d:.1f} s')
# 8. serrer sur un objet : s'arrête dessus et le tient
b5, s5 = bus_avec(butees=(1663, 2433), obstacle=1900)
r, pos, tenu = b5.serrer(1, 1663, force=20); assert tenu and s5.force and abs(pos - 1900) < 3, (r, pos); print('ok  serrage :', r)
# 9. serrer à vide : va au bout, dit qu'il n'y a rien
b6, s6 = bus_avec(butees=(1663, 2433))
r, pos, tenu = b6.serrer(1, 1700, force=20); assert not tenu and 'rien entre les doigts' in r, r; print('ok  serrage à vide : rien entre les doigts')
# 10. étalonnage du milieu
b7, s7 = bus_avec(position=2300, butees=(1663, 2433))
assert b7.etalonner_milieu(1) == 2048 and not s7.force; print('ok  étalonnage : la position devient 2048, force coupée')
# 11. épaule : en cas de blocage, le bras est RETENU sur place (force réduite), pas lâché
b8, s8 = bus_avec(butees=(1663, 2433), obstacle=2200)
r = b8.aller(1, 2400, si_arret='retenir')
assert r.startswith('ARRÊT') and 'RETIENT' in r and s8.force and s8.limite == 400 and abs(s8.cible - 2200) < 3, (r, s8.force, s8.limite, s8.cible)
print('ok  épaule bloquée : bras retenu sur place, force réduite à 40 % —', r[:44])
# 12. retenir : tient la position actuelle
b9, s9 = bus_avec(position=2300, butees=(1663, 2433)); assert b9.retenir(1) == 2300 and s9.force and s9.cible == 2300; print('ok  retenir : le servo tient là où il est')
print('\nToutes les sécurités répondent.')
