# Robot humanoïde — projet de Nicolas

Premier objectif : **un petit bras de table** avec un coude en servo Feetech STS3215-C018 et une
**pince** au bout. La main robotique (ESP32, servos MG90S, gestes préenregistrés, puis gant à
capteurs et voix) viendra ensuite.

## Vision d'ensemble (09/11/2026)

À terme : **deux bras à 6 axes et une tête**, avec **reconnaissance vocale**, une **IA qui répond**
et **reconnaissance d'objets** (« prends la balle rouge »).

| Partie | Matériel | Difficulté |
|---|---|---|
| 2 bras à 6 axes | 12 STS3215 | ⭐⭐ (le même bras, en double, symétrique) |
| Tête qui bouge | 2 servos (tourner, hocher), caméra, micro, haut-parleur | ⭐⭐ |
| Voix + IA qui répond | micro, IA de conversation, voix de synthèse (expérience de la borne du club) | ⭐⭐ |
| Reconnaissance d'objets | caméra + logiciel de détection | ⭐⭐ |
| Attraper l'objet vu | position de l'objet → pince ; piste : **LeRobot** (Hugging Face), fait pour les bras SO-100/SO-101 à servos Feetech : on montre le geste, le robot apprend à le refaire | ⭐⭐⭐⭐ |

**Cerveau** : l'ESP32 ne suffit pas pour la vision et la voix → d'abord l'**ordinateur**, puis un
mini-ordinateur embarqué (**Raspberry Pi 5**, ou **NVIDIA Jetson** pour la vision dans le robot) ;
l'ESP32 reste pour les petites tâches (LED, capteurs, boutons).
**Électricité** : 14 servos → alimentation 12 V de 10 à 15 A, probablement une carte servos par bras.

Ordre prévu :
1. Finir **un bras complet** (en cours).
2. **La tête en parallèle**, sur l'ordinateur : vision et voix, sans moteur, donc sans risque.
3. **Le 2e bras**, copie symétrique du premier.
4. **Tout relier** : la tête trouve l'objet, le bras va le chercher.
5. **Tout embarquer** dans le robot (Raspberry Pi ou Jetson).

## La tête (commencée le 11/11/2026)

Dossier `tete/`, voir `tete/LISEZ-MOI.md`. Étape 1 **voir** : `vision.py`, essayé sur le PC (80 objets
fixes, ou sa propre liste avec YOLO-World). Étape 2 **entendre** : `ecouter.py` (Whisper, en français,
sur le PC), **validé le 11/11/2026**. Étape 3 **répondre** : `parler.py`, conversation
à voix haute avec **Câlin** (même personnage que la borne d'accueil, fusion prévue), Claude + voix ElevenLabs,
**validé le 11/11/2026** (puis accéléré). Étape 4 **tout relier** : `robot.py` (caméra en continu, photo envoyée
à Claude sur une question visuelle), à essayer. Étape 5 **mémoire et visages** (outils de Claude, données
biométriques apprises seulement à la demande de la personne, jamais pour un enfant, rangées hors du projet), à essayer.
Puis bouger (2 servos).

## Objectif : Câlin sert le café (11/11/2026)

**But** : « Câlin, un café s'il te plaît » → il reconnaît la personne → prend un gobelet → lance la machine
→ **pose le gobelet couvert devant la personne, sur la table** → « Voilà ton café ! ».

**Sécurité (café brûlant, enfants au club) — conditions pour servir une boisson chaude :**
- gobelets **avec couvercle** ; petits gobelets (expresso, environ 100 g : le bras porte 200 à 300 g au mieux) ;
- **posé sur la table devant la personne, jamais tendu dans les mains, jamais au-dessus de quelqu'un** ;
- trajet **lent, bas et à plat** quand il porte ; **force limitée** dans les servos ;
- la caméra surveille la zone : **une main trop près → arrêt** ; **interrupteur d'arrêt d'urgence** à portée ;
- au club : **boissons froides pour les enfants**, service chaud réservé aux adultes.

**Étapes :**
1. Bras complet (socle, épaule, coude, pince) et gestes enregistrés en montrant le bras à la main.
2. **Station café** : pile de gobelets, machine **déclenchée par l'ESP32 avec un relais** (pas par le bras), zone de service.
3. Premiers essais avec des **gobelets vides**, puis d'eau froide, puis seulement le café.
4. Outil `servir_cafe` pour Câlin (enchaîne les gestes, vérifie que la zone est libre).
5. Plus tard, peut-être : une **base à roulettes** pour servir plus loin que la portée du bras.

## Feuille de route du premier bras

| # | Étape | État |
|---|---|---|
| 1 | Berceau de banc V4 imprimé, essai à sec (entrée, stabilité, reliefs libres, câbles) | **fait le 07/11/2026** : entre sans forcer, stable, câbles OK (hauteur côté bossage non mesurée) |
| 2 | Berceau V4.1 + bride (inserts M3, vis M3 × 10, patin 1 mm) — `berceau-sts3215/` | abandonné au profit du bras V1 |
| 3 | Premier mouvement : carte Waveshare Bus Servo Adapter (A), cavaliers B, alim 12 V, logiciel FD 1.9.8.2 (COM3, 1000000) | **fait le 07/11/2026** : servo trouvé, 12,3 V, 35 °C, mouvement de 17° à vitesse 300 |
| 4 | Essai sous charge sur le banc : facultatif pour un bras de table (le servo a une grande marge) | reporté |
| 5 | Coude : fourche en deux moitiés tenant l'avant-bras des deux côtés (palonnier + disque libre du dessous) — `coude-sts3215/` | V1 imprimée : écart faux (40,2 calculé, 36,4 mesuré) ; V1.1 aurait frotté sur la partie haute → **V1.2 à imprimer** ; **bras V1** imprimé et monté ; le servo basculait vers l'axe → **bride V1.2 avec cale de 1,4 mm** (serrage 0,5) à imprimer ; rotation de l'avant-bras ± 109° vérifiée hors Fusion |
| 6 | Pince au bout de l'avant-bras — `pince/` | **V1 dessinée (11/11/2026)** : mâchoires parallèles à engrenages, 6 à 95 mm, aucune collision sur tout le mouvement (vérifié hors impression), 125 g ; à imprimer |
| 7 | Piloter depuis le PC : `bras/servos.py` (sécurités : butées obligatoires, lent, chaleur, effort, blocage → force coupée) et `bras/test_coude.py` | écrit et testé sur un servo simulé (11/11/2026) ; essai réel dès la carte neuve |

## Incident du 08/11/2026 et règles de sécurité

Premier branchement avec la fourche du coude montée : **odeur de brûlé**, puis plus rien. La carte
Waveshare n'apparaît plus du tout sur l'ordinateur (ni COM, ni périphérique inconnu, deux câbles USB
essayés) : sa partie USB est morte. Câble du servo intact, aucune trace visible sur la carte.
Cause **non établie** ; hypothèse la plus probable : servo bloqué contre une colonne (butées pas
encore réglées), forçant en continu. Servo d'origine **suspect** : ne le rebrancher qu'en dernier.

Reprise : carte neuve testée seule (port COM) → avec un servo neuf seul, sans rien dessus → enfin
l'ancien servo, seul, sans fourche, prêt à tout débrancher.

Règles désormais :
1. **Butées réglées dans le servo (Min/Max Angle Limit) AVANT de monter quoi que ce soit dessus.**
2. **Protection de couple et de courant** réglée dans FD.
3. **Interrupteur sur le 12 V** pour tout couper d'un geste.
4. **Jamais brancher ou débrancher un servo sous tension.**

## Matériel (décisions du 07/11/2026)

- **Servos** : 8 STS3215-12V (C018, 30 kg·cm, 1/345) de plus, chez Feetech (Shenzhen Feite Model, Alibaba) →
  9 en tout : bras de table complet à 6 axes + rechanges. Vérifier que disques, vis et câble sont inclus.
- **Carte** : la Waveshare Bus Servo Adapter (A) suffit pour tous les servos (en chaîne, un ID par servo).
  **À racheter** (USB de la première carte mort le 08/11/2026).
- **Alimentation** : prévoir 12 V, 5 A minimum (6 à 10 A conseillé) pour 6 servos.
- **Socle tournant** : roulements **6807-2RS** (35 × 47 × 7) ; **deux roulements empilés et
  espacés** dans le socle pour que le bras ne bascule pas, le servo ne fait que tourner.
- **Roulements commandés le 10/11/2026** (123roulement, commande C 81156268, 75,84 € TTC) :
  **6807-2RS × 8** (35 × 47 × 7) = 2 par socle de bras × 2 bras + 2 pour la rotation de la tête
  + 2 de rechange ; **623ZZ × 10** (3 × 10 × 4, axe = vis M3) pour les petits pivots (doigts de
  pince, tête). À réception : mesurer un roulement de chaque au pied à coulisse avant de dessiner
  les logements.
  Coude, épaule et poignet n'en ont pas besoin : chaque servo est tenu des deux côtés par ses deux disques.

## Repères sur le servo (STS3215-C018)

- Boîtier mesuré : 45,2 × 24,4. **Hauteur variable** (08/11/2026) : **28,8** côté palonnier, **33** à partir de 15,6 mm
  du bout côté palonnier (partie haute, plaque de l'étiquette).
- Dessous : cylindre Ø5,5 (centre à 8,1 mm du petit côté X−) et bossage 11,9 × 18,3 côté X+,
  reliefs de 2 mm ; connecteurs entre les deux.
- Étiquette : **STS3215-12V** (alimentation 12 V confirmée).
- Palonnier : **disque aluminium Ø19,7 mm**, dépasse de **4,3 mm** au-dessus du boîtier, centre à **8,1 mm** du petit côté, **aligné avec le cylindre du dessous** (remesuré le 07/11/2026 ; une première mesure à 10,5 était fausse).
  4 trous taraudés sur un cercle de **≈ 13,45 mm** de diamètre (bords intérieurs 10,3, extérieurs 16,6), petites vis fournies (taille à confirmer, probablement M3), vis centrale.
  Vis fournies : **≈ 2,5 mm de diamètre → M2,5** (trou de passage à prévoir ≈ 2,9 mm dans les pièces imprimées).
  **Second disque** fourni (palonnier libre du dessous) : 4 trous taraudés, alésage central avec collerette côté servo ; monté sur le cylindre, il **tourne librement** (pas de cannelures) et dépasse de **3 mm** sous le boîtier.
  Entre les faces extérieures des deux disques : **36,4 mm mesurés** le 08/11/2026 = 3,3 (disque bas) + 28,8 (boîtier) + 4,3 (palonnier).
  Leçon : une cote de hauteur se prend **à l'endroit précis** où la pièce appuie.
- **Axe de sortie au-dessus du cylindre** (côté X−) : le cylindre est **coaxial** à la sortie
  (confirmé) et sert de second pivot au coude.
- Servo « bus série » : jamais branché directement sur une broche de l'ESP32 ; carte d'interface
  et alimentation dédiée obligatoires.

## Référence utile

Les bras de table open source SO-100 / SO-101 utilisent ce même servo (6 par bras) : bonne source
d'inspiration pour le coude, le poignet et la pince.
