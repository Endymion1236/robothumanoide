# Berceau STS3215 — V4.1 (à préparer pour le prochain essai)

Même berceau que la V4, trois changements seulement. Unités : mm. **Aucune validation physique.**

## Ce qui change par rapport à la V4

| | V4 | V4.1 |
|---|---|---|
| Fixation de la bride | vis M3 × 50 traversante + écrou carré sous le socle (la vis dépassait d'environ 1,1 mm sous le socle) | **insert fileté M3 posé à chaud** en haut de chaque colonne, vis **M3 × 10** |
| Jeu sous la bride | 0 (contact « parfait ») | **1 mm**, à combler par un patin caoutchouc de 1 à 1,5 mm |
| Bandes d'appui | fente de 0,2 mm contre parois et butées (non imprimable) | bandes collées aux parois et butées ; la zone qui porte le servo est inchangée (2 mm sous son bord, 140,8 mm²) |

Conséquences : colonnes et sommet du berceau à Z = 45,9 (au lieu de 44,9), bride de Z = 45,9 à 49,9.
Plus de trous ni de logements d'écrou sous le socle.

Inchangé : socle 80 × 60 × 5, logement 45,6 × 24,8, appuis à Z = 12, 5 mm sous les reliefs,
marge bossage/appui 1,05, fenêtre de câbles, position de la bride (côté bossage — l'axe de sortie
est au-dessus du cylindre, donc loin de la bride).

## Inserts M3

- Paramètres : `insert_D` = 4 mm (diamètre du trou), `insert_depth` = 7 mm (profondeur).
- **Mesure tes inserts avant de lancer le script** : le trou se fait en général 0,2 à 0,5 mm
  plus petit que le diamètre extérieur moleté de l'insert (voir l'indication du vendeur), et la
  profondeur doit dépasser la longueur de l'insert d'au moins 1 mm. Change ces deux paramètres
  si besoin.
- Avec un trou de 4 mm dans une colonne de 8 mm, il reste 2 mm de paroi : imprimer avec
  **au moins 4 périmètres** (parois) pour que la colonne ne fende pas à la pose de l'insert.
- Pose : fer à souder vers 220-240 °C pour le PETG, enfoncer droit, sans forcer, jusqu'à affleurer.

## Utilisation

1. Dans Fusion : Utilitaires → Scripts et compléments → « + » → choisir le dossier
   `ServoCradleV4_1`, puis Exécuter. Le script crée un nouveau document et exporte dans
   `outputs/servo_cradle_v4_1` (STL Fusion, archive `.f3d`, rapport `verification_V4_1.json`).
2. Les STL déjà présents dans `outputs/servo_cradle_v4_1` ont été construits **hors de Fusion**
   (`verify_mesh.py`, même tableau de paramètres) : fermés, d'un seul volume, aucune collision
   avec le servo de référence. Le script Fusion V4.1 lui-même **n'a pas encore été exécuté** :
   s'il signale une erreur, envoyer le message affiché.
3. Après exécution dans Fusion : `python check_fusion_exports.py` compare les STL de Fusion aux
   STL indépendants.

## Avant d'imprimer la bride

Mesurer, au pied à coulisse, la hauteur du servo **à l'endroit où passe la bride** (côté bossage,
X local 29 à 37) : le modèle suppose 32,9 mm et un dessus plat. Résultats de l'essai de la V4
à reporter ici avant toute V4.2.
