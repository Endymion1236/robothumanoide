"""Tête du robot — étape 2 : ENTENDRE.

Écoute le micro en continu, repère quand quelqu'un parle (le son monte au-dessus du bruit de fond,
puis retombe pendant un court silence), et écrit la phrase comprise. Reconnaissance vocale Whisper
(faster-whisper), en français, sur l'ordinateur : gratuite et sans internet une fois le modèle téléchargé.

Utilisation :  python ecouter.py                 (micro par défaut, modèle « small »)
               python ecouter.py --lister        (quels micros sont branchés ?)
               python ecouter.py --micro 2       (choisir un micro)
               python ecouter.py --modele base   (plus rapide, moins précis ; « medium » : l'inverse)
               python ecouter.py --fichier a.wav (comprendre un enregistrement au lieu du micro)
Ctrl + C pour arrêter.
"""
import argparse, queue, sys, time, wave
import numpy as np

FREQ = 16000                 # Whisper travaille à 16 000 échantillons par seconde
BLOC = 480                   # 30 ms de son par bloc

class Decoupeur:
    """Découpe un flux de son en phrases : début quand le volume dépasse le seuil, fin après un silence.
    Logique pure (sans micro), pour pouvoir la tester avec un enregistrement."""
    def __init__(self, seuil, silence_fin=0.8, duree_min=0.4, duree_max=15.0):
        self.seuil, self.silence_fin, self.duree_min, self.duree_max = seuil, silence_fin, duree_min, duree_max
        self.morceaux, self.en_cours, self.silence, self.avant = [], False, 0.0, []

    def ajouter(self, bloc):
        """Ajoute un bloc de son ; renvoie une phrase (tableau de son) quand elle est finie, sinon None."""
        volume = float(np.sqrt(np.mean(bloc**2)))
        duree_bloc = len(bloc)/FREQ
        if not self.en_cours:
            self.avant = (self.avant + [bloc])[-10:]          # garde 0,3 s avant le début, pour ne pas couper la 1re syllabe
            if volume > self.seuil:
                self.en_cours, self.morceaux, self.silence = True, list(self.avant), 0.0
            return None
        self.morceaux.append(bloc)
        self.silence = self.silence + duree_bloc if volume <= self.seuil else 0.0
        duree = sum(len(m) for m in self.morceaux)/FREQ
        if self.silence >= self.silence_fin or duree >= self.duree_max:
            self.en_cours, self.avant = False, []
            phrase = np.concatenate(self.morceaux); self.morceaux = []
            return phrase if duree - self.silence >= self.duree_min else None
        return None

def charger_modele(taille):
    from faster_whisper import WhisperModel
    print(f'Chargement de la reconnaissance vocale « {taille} » (le premier lancement la télécharge : '
          f'{ {"base": "environ 150 Mo", "small": "environ 480 Mo", "medium": "environ 1,5 Go"}.get(taille, "")})...')
    return WhisperModel(taille, device='cpu', compute_type='int8')

def comprendre(modele, son):
    """Son (16 kHz, nombres entre -1 et 1) → texte français."""
    segments, _ = modele.transcribe(son.astype(np.float32), language='fr', vad_filter=True, beam_size=5)
    return ' '.join(s.text.strip() for s in segments).strip()

def lire_wav(chemin):
    w = wave.open(chemin)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)/32768
    if w.getnchannels() > 1:
        x = x.reshape(-1, w.getnchannels()).mean(axis=1)
    sr = w.getframerate()
    return np.interp(np.arange(0, len(x), sr/FREQ), np.arange(len(x)), x).astype(np.float32) if sr != FREQ else x

def lister_micros():
    import sounddevice as sd
    print('Micros disponibles :')
    for i, d in enumerate(sd.query_devices()):
        if d['max_input_channels'] > 0:
            print(f"  {i} : {d['name']}" + ('   <- micro par défaut' if i == sd.default.device[0] else ''))

# Phrases que Whisper « entend » parfois dans le silence ou le bruit (il a appris sur des vidéos sous-titrées).
HALLUCINATIONS = ('sous-titres', 'amara.org', 'merci d\'avoir regardé', 'abonnez-vous', 'sous-titrage')

def phrase_valable(texte):
    t = texte.lower().strip(' .!?…')
    return len(t) >= 2 and not any(h in t for h in HALLUCINATIONS)

class Oreille:
    """Le micro, ouvert en continu, avec une pause possible (quand le robot parle, il ne doit pas s'entendre)."""
    def __init__(self, modele, micro=None, seuil=None):
        import sounddevice as sd
        self.modele, self.file = modele, queue.Queue()
        self.flux = sd.InputStream(samplerate=FREQ, channels=1, blocksize=BLOC, dtype='float32', device=micro,
                                   callback=lambda d, n, t, s: self.file.put(d[:, 0].copy()))
        self.flux.start()
        if seuil is None:
            print('Silence 2 secondes : je mesure le bruit de fond...')
            fond = [self.file.get() for _ in range(int(2*FREQ/BLOC))]
            bruit = float(np.sqrt(np.mean(np.concatenate(fond)**2)))
            seuil = max(bruit*3, 0.01)
            print(f'Bruit de fond {bruit:.4f} → seuil {seuil:.4f}')
        self.seuil = seuil
        self.decoupeur = Decoupeur(seuil)

    def vider(self):
        """Oublie tout ce que le micro a capté jusqu'ici (à appeler après que le robot a parlé)."""
        while not self.file.empty():
            self.file.get_nowait()
        self.decoupeur = Decoupeur(self.seuil)

    def phrase(self):
        """Attend la prochaine phrase et la renvoie en texte (ignore le bruit et les phrases fantômes)."""
        while True:
            son = self.decoupeur.ajouter(self.file.get())
            if son is not None:
                texte = comprendre(self.modele, son)
                if phrase_valable(texte):
                    return texte

    def fermer(self):
        self.flux.stop(); self.flux.close()

def ecouter_micro(modele, micro=None, seuil=None):
    """Écoute en continu et renvoie les phrases comprises une par une, avec le temps de calcul."""
    oreille = Oreille(modele, micro, seuil)
    print('Je t\'écoute. Parle normalement ; Ctrl + C pour arrêter.')
    try:
        while True:
            t = time.time(); texte = oreille.phrase()
            yield texte, time.time() - t
    finally:
        oreille.fermer()

def main():
    ap = argparse.ArgumentParser(description='Tête du robot : reconnaissance vocale')
    ap.add_argument('--lister', action='store_true', help='lister les micros')
    ap.add_argument('--micro', type=int, help='numéro du micro (voir --lister)')
    ap.add_argument('--modele', default='small', choices=['base', 'small', 'medium'], help='taille du modèle')
    ap.add_argument('--seuil', type=float, help='volume à partir duquel on considère qu\'on parle (mesuré tout seul sinon)')
    ap.add_argument('--fichier', help='comprendre un enregistrement .wav au lieu du micro')
    a = ap.parse_args()
    if a.lister:
        lister_micros(); return
    modele = charger_modele(a.modele)
    if a.fichier:
        print('Compris :', comprendre(modele, lire_wav(a.fichier)) or '(rien)'); return
    try:
        for texte, duree in ecouter_micro(modele, a.micro, a.seuil):
            print(f'Tu as dit : « {texte} »   ({duree:.1f} s)')
    except KeyboardInterrupt:
        print('\nArrêt.')

if __name__ == '__main__':
    main()
