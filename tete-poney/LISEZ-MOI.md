# Tête de Câlin : un poney palomino (idée du 16/11/2026)

Aperçu de la forme : `sortie/apercu_tete_poney.png` (`python apercu_tete_poney.py`). **Maquette en formes simples,
rien n'est encore dessiné en pièces.**

## Le principe
- **Crâne imprimé** léger en forme de tête de poney (≈ 23 cm du chignon au bout du nez, proportionné au bras de 35 cm),
  qui porte tout et se fixe sur le cou.
- **Habillage en tissu** doux (robe palomino dorée, crinière et toupet crème, liste blanche), à enfiler, cousu sur
  mesure par une couturière d'après la forme du crâne ; retirable pour le lavage et l'accès à l'électronique.
- **Yeux lumineux** : anneaux de LED derrière deux dômes translucides qui traversent le tissu ; animations selon
  l'humeur (écoute, réflexion, parole, repos).
- **Oreilles mobiles** : 2 MG90S. Dressées en avant quand il écoute, l'une qui pivote vers un bruit, détendues au
  repos. **Jamais plaquées en arrière** (méfiance, colère : à éviter devant les enfants).
- **Caméra** au milieu du front (dans la liste), **micro** sous le menton, **haut-parleur** dans la tête.
- **Cou** : les 2 STS3215 de rechange (tourner, hocher) ; tête de 400 à 500 g.
- Plus tard, en option : mâchoire qui s'ouvre un peu quand il parle (un petit servo de plus).

## Choix du 16/11/2026 (Nicolas : « fais comme tu le sens »)
- **Style peluche** plutôt que réaliste : front bombé, nez plus court et rond. Plus rassurant pour les enfants, plus
  facile à habiller, et la tête est plus compacte (moins lourde au bout du cou).
- **Grands yeux tournés de 35° vers l'avant** (au lieu des côtés comme un vrai poney) : Câlin a l'air de regarder
  la personne en face.

## Matériel envisagé (à confirmer avec ce que Nicolas a déjà)
| Quoi | Proposition | Pourquoi |
|---|---|---|
| Caméra | la webcam USB déjà utilisée par `tete/` (caméra 1), sortie de son boîtier si possible | logiciel déjà réglé ; à mesurer |
| Yeux | 2 anneaux de LED adressables WS2812B, 12 ou 16 LED (Ø ext. 37 ou 44 mm), derrière un dôme imprimé en blanc translucide | couleurs et animations par programme |
| Oreilles | 2 MG90S (du premier projet de main) | légers, assez forts pour des oreilles creuses |
| Pilotage yeux + oreilles | l'ESP32 déjà en stock, relié au PC en USB | le PC reste le cerveau (vision, voix, IA) |
| Haut-parleur, micro | pour commencer, ceux déjà branchés au PC ; plus tard un haut-parleur 40 mm 3 W + petit ampli, et un micro USB dans la tête | rien à acheter tout de suite |
| Cou | les 2 STS3215 de rechange (n° 7 tourner, n° 8 hocher, sur le bus des servos) | même carte, mêmes sécurités |

## Ce que le cou permettra
Tourner la tête vers la personne qui parle ou un visage reconnu, faire oui / non, regarder l'objet que le bras va saisir.

## Prochaines étapes
1. Valider la forme générale (cet aperçu).
2. Choisir caméra, anneaux de LED, haut-parleur, micro (mesures exactes avant de dessiner).
3. Dessiner le crâne en deux coques (dessus, dessous) avec les supports intérieurs, le cou et les oreilles.
4. Patron de l'habillage pour la couturière, tiré de la forme du crâne.
