"""Lance TOUTES les vérifications de la pince, dans l'ordre, et dit clairement si tout est bon.
    python tout_verifier.py
1. generer_pince.py        : construit les pièces, collisions sur toute la course, pose d'impression, fichiers STL
2. verifier_cinematique.py : le doigt ne peut pas se retourner (point mort), le test détecte bien le défaut de la V2
3. verifier_engrenages.py  : place entre les dents
4. verifier_jeux.py        : jeu entre toutes les pièces, sur toute la course
5. verifier_visserie.py    : vis, écrous et rondelles ne touchent rien
6. test_gobelets.py        : gobelets de 55, 80 et 90 mm
7. ../bras/test_securites.py : sécurités du programme (butées, chaleur, pince coincée) sur un faux servo
Il faut : pip install numpy trimesh manifold3d python-fcl pyserial"""
import subprocess, sys, json
from pathlib import Path
ICI = Path(__file__).resolve().parent
ETAPES = [('pièces, collisions, pose d\'impression', ICI / 'generer_pince.py'), ('doigt qui se retourne (point mort)', ICI / 'verifier_cinematique.py'),
          ('place entre les dents', ICI / 'verifier_engrenages.py'), ('jeu entre les pièces', ICI / 'verifier_jeux.py'),
          ('visserie', ICI / 'verifier_visserie.py'), ('gobelets', ICI / 'test_gobelets.py'),
          ('sécurités du programme (faux servo)', ICI.parent / 'bras' / 'test_securites.py')]
bilan = []
for nom, script in ETAPES:
    r = subprocess.run([sys.executable, str(script)], cwd=script.parent, capture_output=True, text=True)
    ok = r.returncode == 0
    if ok and script.name == 'generer_pince.py':
        ok = not json.loads((ICI / 'sortie' / 'verification_pince.json').read_text(encoding='utf-8'))['collisions']
    if ok and script.name == 'test_gobelets.py':
        ok = all(not g['touche'] for g in json.loads((ICI / 'sortie' / 'test_gobelets.json').read_text(encoding='utf-8')))
    bilan.append((nom, ok)); print(('OK      ' if ok else 'ÉCHEC   ') + nom)
    if not ok: print(r.stdout[-1500:], r.stderr[-1500:])
print('\n' + ('TOUT EST BON : ' if all(ok for _, ok in bilan) else 'À CORRIGER : ') + f"{sum(ok for _, ok in bilan)} vérifications réussies sur {len(bilan)}")
(ICI / 'sortie' / 'bilan_verifications.json').write_text(json.dumps([{'verification': n, 'reussie': ok} for n, ok in bilan], ensure_ascii=False, indent=1), encoding='utf-8')
sys.exit(0 if all(ok for _, ok in bilan) else 1)
