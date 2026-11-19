# Robot humanoïde de Nicolas — consignes pour toute session

Nicolas gère un centre équestre et débute en électronique : réponses en français, simples, pas à pas.
La feuille de route et l'état du projet sont dans `README.md` ; chaque dossier a son `LISEZ-MOI.md`.

## Règle de conception (demande de Nicolas, 19/11/2026)

**Avant de modéliser une pièce, demander les mesures de tout élément dont la cote n'est pas déjà mesurée et notée** :
longueur des vis (sous tête), diamètre et longueur des inserts, roulements, épaisseur d'une planche, longueur des câbles,
servo ou composant jamais mesuré. Ne pas supposer qu'une vis « fournie » a la bonne longueur.
Exemples de ce que cette règle aurait évité : vis M2,5 du servo trop courtes pour l'engrenage A puis pour le moyeu du
socle (elles font 5,3 mm sous tête), inserts trop longs pour les doigts, câble de la pince trop court.

Mesures déjà connues : voir « Repères sur le servo » et « Matériel » dans `README.md` ; vis M2,5 fournies avec les
servos : 5,3 mm sous tête ; inserts courts M3 × 5 × 4 ; roulements 6807 : 47 × 35 × 6,8 ; 623 : 10 × 3 × 4.

## Autres habitudes du projet

- Toute pièce est vérifiée par le calcul avant d'être proposée (collisions sur toute la course, visserie comprise) et
  annoncée comme « prototype » tant qu'elle n'a pas été montée ; tout programme est essayé sur un servo simulé et
  annoncé comme tel.
- Sécurité des servos : butées réglées avant de monter quoi que ce soit, jamais brancher ou débrancher sous tension,
  un bras qui porte du poids est RETENU, jamais lâché, par les sécurités.
- Les clés d'API et les données personnelles (visages, souvenirs) restent sur le PC de Nicolas, jamais dans le dépôt.
- Un commit par sujet, en français : le problème tel que Nicolas l'a vu, puis ce qui change.
