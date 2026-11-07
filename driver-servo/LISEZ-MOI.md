# Pilotes et logiciels du servo STS3215 + carte Waveshare Bus Servo Adapter (A)

## Ce qu'il y a dans ce dossier

| Fichier | À quoi il sert | Quand |
|---|---|---|
| `STServo_Python.zip` | Programmes Python de Waveshare pour piloter le servo depuis le PC (dossier `sms_sts` : `ping.py` trouve le servo, `read.py` lit sa position, `write.py` le fait bouger, `change_id.py` change son numéro) | Solution de secours si le logiciel FD ne marche pas, ou sur Mac |
| `ST_Servo_Arduino_ESP32.zip` | Bibliothèque Arduino « SCServo » + exemples (dossier `SMS_STS` pour le STS3215) | Plus tard, quand l'ESP32 pilotera le servo (cavaliers en **A**) |
| `Protocole_servo_bus.zip` | Manuel du protocole + **table des registres du STS3215** (fichier Excel) | Référence |
| `Schema_Bus_Servo_Adapter_A.pdf` | Schéma électronique de ta carte (puce USB : **CH343P**) | Référence |

## Les deux fichiers à télécharger toi-même

Ces deux sites refusent les téléchargements depuis le serveur de Claude : il faut les prendre
directement sur ton PC Windows.

1. **Logiciel FD (Feetech)** — prends **FD1.9.8.2 (离线版 = version hors ligne)** :
   https://www.feetechrc.com/Data/feetechrc/upload/file/20240706/FD1.9.8.2.zip
   Décompresser (clic droit → Extraire tout), lancer `FD.exe`. Si Windows bloque :
   « Informations complémentaires » → « Exécuter quand même ».

2. **Pilote USB CH343** (fabricant WCH) — **seulement si Windows ne reconnaît pas la carte** :
   https://www.wch-ic.com/downloads/CH343SER_EXE.html → bouton de téléchargement, puis lancer
   `CH343SER.EXE` → « Install ». Sur Windows 10 et 11, le pilote s'installe en général tout seul :
   vérifie d'abord dans le Gestionnaire de périphériques (voir plus bas).

## Branchement, dans cet ordre

**Jamais brancher ni débrancher le servo quand le 12 V est branché.**

1. Vérifier « 12V » sur l'étiquette du servo (C018 = version 12 V).
2. Cavaliers jaunes sur **B** (USB ↔ SERVO).
3. Servo sur une prise **D V G**, palonnier libre.
4. Alimentation 12 V dans la prise ronde → LED **PWR** allumée.
5. USB-C vers le PC → Gestionnaire de périphériques → **Ports (COM et LPT)** :
   une ligne « USB-SERIAL CH343 (COMx) » doit apparaître. Noter le numéro COM.
6. FD : port COMx, vitesse **1000000**, **Search** → le servo apparaît (ID 1 en général).
   Lire la position (0 à 4095 = un tour), puis demander une position proche (± 200 ≈ 17°)
   avec une vitesse faible.

## Secours en Python (si FD ne trouve rien)

1. Installer Python depuis python.org (cocher « Add Python to PATH »).
2. Décompresser `STServo_Python.zip`, ouvrir un terminal dans `STServo_Python/stservo-env/sms_sts`.
3. `pip install pyserial`
4. Ouvrir `ping.py` avec le Bloc-notes, remplacer le nom du port par le tien (ex. `COM3`), enregistrer.
5. `python ping.py` → doit afficher le numéro et le modèle du servo.
