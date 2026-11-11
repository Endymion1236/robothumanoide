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
import argparse, queue, sys, threading, time, wave
import numpy as np

FREQ = 16000                 # Whisper travaille à 16 000 échantillons par seconde
BLOC = 480                   # 30 ms de son par bloc

class Decoupeur:
    """Découpe un flux de son en phrases : début quand le volume dépasse le seuil, fin après un silence.
    Logique pure (sans micro), pour pouvoir la tester avec un enregistrement."""
    def __init__(self, seuil, silence_fin=0.6, duree_min=0.4, duree_max=15.0):
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
    """Son (16 kHz, nombres entre -1 et 1) → texte français.
    modele : un modèle Whisper local, ou un objet qui a sa propre méthode comprendre() (ElevenLabs)."""
    if hasattr(modele, 'comprendre'):
        return modele.comprendre(son)
    # beam_size=1 : nettement plus rapide sur le processeur ; le découpage en phrases est déjà fait avant
    segments, _ = modele.transcribe(son.astype(np.float32), language='fr', vad_filter=False, beam_size=1)
    return ' '.join(s.text.strip() for s in segments).strip()

# Levé pendant la transcription locale : la caméra suspend ses calculs pour laisser le processeur à Whisper.
TRANSCRIPTION = threading.Event()

class ScribeElevenLabs:
    """Transcription par ElevenLabs (Scribe v2), dans le nuage : rapide, n'occupe pas le processeur du PC.
    Le son est envoyé brut (16 bits, 16 kHz, mono), la façon la plus rapide d'après ElevenLabs."""
    MODELE = 'scribe_v2'
    def __init__(self, cle):
        from elevenlabs.client import ElevenLabs
        self.client = ElevenLabs(api_key=cle)

    def comprendre(self, son):
        brut = (np.clip(son, -1, 1) * 32767).astype('<i2').tobytes()
        try:
            r = self.client.speech_to_text.convert(model_id=self.MODELE, file=brut, file_format='pcm_s16le_16',
                                                   language_code='fr', tag_audio_events=False)
        except Exception as e:
            print(f'   (transcription ElevenLabs impossible : {e})'); return ''
        return (getattr(r, 'text', '') or '').strip()

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
        self.duree_comprehension = None

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
                t = time.time()
                local = not hasattr(self.modele, 'comprendre')
                if local:
                    TRANSCRIPTION.set()
                try:
                    texte = comprendre(self.modele, son)
                finally:
                    TRANSCRIPTION.clear()
                self.duree_comprehension = time.time() - t
                if phrase_valable(texte):
                    return texte

    def fermer(self):
        self.flux.stop(); self.flux.close()

class OreilleTempsReel:
    """Transcription EN DIRECT (ElevenLabs Scribe v2 temps réel) : le son part pendant qu'on parle, et la phrase
    finie revient dès qu'on se tait (le serveur repère lui-même la fin de phrase). Même usage qu'Oreille :
    phrase(), vider(), fermer(). muet() : renvoie True quand le robot parle (on n'envoie alors rien).
    Si la connexion échoue au démarrage, lève une exception : l'appelant repasse sur la transcription classique."""
    MODELE = 'scribe_v2_realtime'
    SILENCE_FIN = 0.5                     # secondes de silence qui terminent une phrase (0,3 à 3)

    def __init__(self, cle, micro=None, muet=None, connecter=None, ouvrir_micro=True):
        import asyncio
        self.asyncio, self.cle, self.muet = asyncio, cle, muet or (lambda: False)
        self.textes, self.connexion, self.erreur = queue.Queue(), None, None
        self.t_dernier_son, self.duree_comprehension, self.ouverte = None, None, threading.Event()
        self.connecter = connecter or self._connecter_elevenlabs
        self.boucle = asyncio.new_event_loop()
        threading.Thread(target=self.boucle.run_forever, daemon=True).start()
        self._ouvrir()
        if not self.ouverte.wait(15) or self.erreur:
            raise RuntimeError(f'transcription en direct indisponible : {self.erreur or "pas de réponse"}')
        self.flux = None
        if ouvrir_micro:
            import sounddevice as sd
            self.flux = sd.InputStream(samplerate=FREQ, channels=1, blocksize=BLOC * 2, dtype='float32', device=micro,
                                       callback=lambda d, n, t, st: self.envoyer(d[:, 0].copy()))
            self.flux.start()

    async def _connecter_elevenlabs(self):
        from elevenlabs.client import ElevenLabs
        from elevenlabs.realtime.scribe import AudioFormat, CommitStrategy
        return await ElevenLabs(api_key=self.cle).speech_to_text.realtime.connect({
            'model_id': self.MODELE, 'audio_format': AudioFormat.PCM_16000, 'sample_rate': FREQ,
            'commit_strategy': CommitStrategy.VAD, 'vad_silence_threshold_secs': self.SILENCE_FIN,
            'language_code': 'fr', 'filter_background_audio': True})

    def _ouvrir(self):
        async def ouvrir():
            try:
                from elevenlabs.realtime.connection import RealtimeEvents as Ev
                c = await self.connecter()
                c.on(Ev.COMMITTED_TRANSCRIPT, self._phrase_recue)
                c.on(Ev.ERROR, lambda d: print(f'   (transcription en direct : {d})'))
                c.on(Ev.CLOSE, lambda *a: self._fermee())
                self.connexion = c
            except Exception as e:
                self.erreur = str(e)
            self.ouverte.set()
        self.asyncio.run_coroutine_threadsafe(ouvrir(), self.boucle)

    def _fermee(self):
        """Le serveur a fermé (limite de durée de session…) : on rouvre, sans bloquer."""
        self.connexion, self.erreur = None, None
        self.ouverte.clear(); self._ouvrir()

    def _phrase_recue(self, donnees):
        texte = (donnees.get('text') or donnees.get('transcript') or '').strip()
        if texte and not self.muet() and phrase_valable(texte):
            if self.t_dernier_son:
                self.duree_comprehension = time.time() - self.t_dernier_son
            self.textes.put(texte)

    def envoyer(self, bloc):
        """Appelé par le micro (bloc de son 16 kHz) : envoie au serveur, sauf quand le robot parle."""
        if self.muet() or self.connexion is None:
            return
        if float(np.sqrt(np.mean(bloc**2))) > 0.01:
            self.t_dernier_son = time.time()
        brut = (np.clip(bloc, -1, 1) * 32767).astype('<i2').tobytes()
        import base64
        self.asyncio.run_coroutine_threadsafe(
            self.connexion.send({'audio_base_64': base64.b64encode(brut).decode()}), self.boucle)

    def phrase(self):
        return self.textes.get()

    def vider(self):
        while not self.textes.empty():
            self.textes.get_nowait()

    def fermer(self):
        if self.flux:
            self.flux.stop(); self.flux.close()
        if self.connexion:
            self.asyncio.run_coroutine_threadsafe(self.connexion.close(), self.boucle)

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
