"""Tête du robot — étape 3 : RÉPONDRE (et étape 4 : tout relier).

Boucle de conversation :  tu parles → Whisper écrit ta phrase → Claude répond → la voix la dit.
Le robot s'appelle Câlin, comme la borne d'accueil du club (on les réunira plus tard).

Utilisation :  python parler.py              (micro + voix ElevenLabs)
               python parler.py --clavier    (taper ses phrases au lieu de parler)
               python parler.py --muet       (réponses écrites seulement, sans voix)
               python parler.py --voix-pc    (voix de Windows, gratuite, au lieu d'ElevenLabs)
               python parler.py --ia opus    (IA plus puissante, plus lente)
Dire « au revoir » ou Ctrl + C pour arrêter.

Clés : fichier texte hors du projet (voir cles_exemple.txt), lignes ANTHROPIC_API_KEY=... et
ELEVENLABS_API_KEY=... ; facultatif : ELEVENLABS_VOICE_ID=... pour choisir une autre voix.
"""
import argparse, base64, itertools, os, queue, re, sys, threading, time
from pathlib import Path
import numpy as np

# --- Réglages -------------------------------------------------------------------------------
MODELES_IA = {'sonnet': 'claude-sonnet-5-5',   # par défaut (choix de Nicolas, 11/11/2026) : rapide, celui de la borne
              'opus': 'claude-opus-5-5'}       # plus puissant, plus lent et plus cher (--ia opus)
EFFORT = 'low'                         # conversation simple : réflexion courte, réponse plus rapide
VOIX_ELEVENLABS = 'JBFqnCBsd6RMkjVDRZzb'   # voix par défaut (multilingue) ; remplaçable dans le fichier des clés
MODELE_VOIX = 'eleven_v4'                 # ElevenLabs v4, choix de Nicolas (11/11/2026)
MODELE_VOIX_RAPIDE = 'eleven_v4_turbo'    # v4 rapide, prévue pour la conversation (--voix-rapide)
# Autres : 'eleven_multilingual_v2' (naturel, éprouvé), 'eleven_flash_v2_5' (très rapide, jugé mauvais)
HISTORIQUE_MAX = 20                    # nombre de messages gardés en mémoire pendant la conversation

PERSONNALITE = """Tu es Câlin, la tête d'un robot humanoïde en construction au centre équestre d'Agon-Coutainville, \
dans la Manche. C'est Nicolas, le gérant du club, qui te construit, pièce par pièce. Le même Câlin accueille déjà \
les visiteurs sur la borne d'accueil du club ; un jour, la borne et toi ne ferez plus qu'un.

Ce que tu es aujourd'hui : une caméra, un micro et un haut-parleur reliés à un ordinateur. Tu as un bras \
en cours de fabrication (un coude, bientôt une pince), deux bras et une tête qui bouge sont prévus. \
Tu ne peux encore rien attraper ni bouger : si on te le demande, dis-le gentiment et avec humour.

Ton caractère : chaleureux, curieux, un peu malicieux, passionné de chevaux, de poneys et de Pony Games. \
Tu aimes expliquer simplement comment tu fonctionnes, surtout aux enfants.

Règles :
- Tu parles à voix haute : réponses COURTES, 1 à 3 phrases, sans listes, sans emojis, sans mise en forme.
- Uniquement en français. Vouvoie les adultes ; tutoie un enfant s'il te tutoie ou dit son âge.
- Ce que tu entends passe par une reconnaissance vocale qui peut se tromper : si une phrase n'a pas de sens, \
demande de répéter plutôt que d'inventer.
- Tu ne connais ni les tarifs, ni le planning, ni les familles du club : pour ça, renvoie vers l'accueil ou la borne.
- Ne promets jamais qu'une activité à cheval convient à un âge ou un niveau : c'est l'équipe du club qui décide."""

MOTS_FIN = ('au revoir', 'arrête-toi', 'arrête toi', 'stop câlin', 'bonne nuit câlin')

# --- Clés -----------------------------------------------------------------------------------
ENDROITS_CLES = [Path('C:/projet robot') / n for n in ('cles_robot.txt', 'cles.txt', 'cles.env', '.env')] + \
                [Path.home() / 'cles_robot.txt', Path(__file__).resolve().parent / 'cles.txt']

def lire_cles():
    """Variables d'environnement d'abord, puis le premier fichier de clés trouvé.
    Accepte « NOM=valeur » ; reconnaît aussi une clé Anthropic (sk-ant-…) ou ElevenLabs (sk_…) seule sur sa ligne."""
    cles = {k: os.environ[k] for k in ('ANTHROPIC_API_KEY', 'ELEVENLABS_API_KEY', 'ELEVENLABS_VOICE_ID') if os.environ.get(k)}
    fichier = next((p for p in ENDROITS_CLES if p.is_file()), None)
    if fichier:
        for ligne in fichier.read_text(encoding='utf-8-sig').splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith('#'):
                continue
            nom, egal, valeur = ligne.partition('=')
            if not egal:
                nom, valeur = '', ligne
            nom, valeur = nom.strip().upper(), valeur.strip().strip('"\'')
            if 'colle-ta-cle' in valeur:
                continue
            if nom in ('ANTHROPIC_API_KEY', 'ELEVENLABS_API_KEY', 'ELEVENLABS_VOICE_ID'):
                cles.setdefault(nom, valeur)
            elif valeur.startswith('sk-ant-'):
                cles.setdefault('ANTHROPIC_API_KEY', valeur)
            elif valeur.startswith('sk_'):
                cles.setdefault('ELEVENLABS_API_KEY', valeur)
    return cles, fichier

# --- Cerveau : Claude ---------------------------------------------------------------------------
FIN_DE_PHRASE = re.compile(r'(?<=[.!?…])\s+')

class Cerveau:
    """Envoie la phrase à Claude et renvoie la réponse PHRASE PAR PHRASE, au fur et à mesure qu'elle s'écrit.
    L'historique ne garde que le TEXTE des échanges : on peut alors le raccourcir et y retirer les photos
    sans que l'API refuse la conversation (la réflexion interne du modèle n'y est pas rejouée)."""
    def __init__(self, cle, modele='claude-opus-5-5', personnalite=PERSONNALITE, outils=None, sur_outil=None):
        """outils : outils que Claude peut déclencher (liste de définitions) ; sur_outil(nom, entrées) les exécute
        et renvoie une phrase à dire, ou None."""
        import anthropic
        self.anthropic, self.modele, self.personnalite = anthropic, modele, personnalite
        self.outils, self.sur_outil = outils or [], sur_outil
        self.sur_morceau_outil = None
        self.client = anthropic.Anthropic(api_key=cle)
        self.messages = []
        self.duree_premier_mot = None

    def repondre(self, phrase, image_jpeg=None, contexte=None, sur_phrase=None, sur_morceau=None):
        """Renvoie le texte complet ; appelle sur_phrase(texte) dès qu'une phrase de la réponse est finie."""
        contenu = []
        if contexte:
            contenu.append({'type': 'text', 'text': contexte})
        if image_jpeg:
            contenu.append({'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg',
                                                        'data': base64.b64encode(image_jpeg).decode()}})
        contenu.append({'type': 'text', 'text': phrase})
        self.messages.append({'role': 'user', 'content': contenu})
        t0, self.duree_premier_mot, tampon, morceaux = time.time(), None, '', []
        self.sur_morceau_outil = sur_morceau
        def phrase_finie(texte):
            texte = texte.strip()
            if texte:
                morceaux.append(texte)
                if sur_phrase:
                    sur_phrase(texte)
        options = {'tools': self.outils} if self.outils else {}
        try:
            with self.client.beta.messages.stream(
                **options,
                model=self.modele,
                max_tokens=4000,
                system=self.personnalite,
                messages=self.messages,
                output_config={'effort': EFFORT},
                # si le modèle refuse une demande, l'API passe la main à un autre modèle dans le même appel
                betas=['server-side-fallback-2026-07-01'],
                fallbacks='default',
            ) as flux:
                for bout in flux.text_stream:
                    if self.duree_premier_mot is None:
                        self.duree_premier_mot = time.time() - t0
                    if sur_morceau:
                        sur_morceau(bout)             # la voix en direct reçoit le texte mot par mot
                    tampon += bout
                    *finies, tampon = FIN_DE_PHRASE.split(tampon)
                    for f in finies:
                        phrase_finie(f)
                reponse = flux.get_final_message()
            phrase_finie(tampon)
            notes = self._executer_outils(reponse, phrase_finie)
        except self.anthropic.AuthenticationError:
            return self._echec('Ma clé Anthropic ne marche pas. Vérifiez le fichier des clés.', sur_phrase)
        except self.anthropic.RateLimitError:
            return self._echec('Je réfléchis trop vite, laissez-moi souffler quelques secondes.', sur_phrase)
        except self.anthropic.APIConnectionError:
            return self._echec('Je n\'arrive pas à joindre internet.', sur_phrase)
        except self.anthropic.APIStatusError as e:
            return self._echec(f'Mon cerveau a un souci technique, erreur {e.status_code}.', sur_phrase)
        if reponse.stop_reason == 'refusal' and not morceaux:
            return self._echec('Je préfère ne pas répondre à ça.', sur_phrase)
        texte = ' '.join(morceaux + notes)
        # photo remplacée par une mention dans l'historique (sinon chaque tour la renverrait)
        self.messages[-1]['content'] = [b if b['type'] != 'image' else {'type': 'text', 'text': '[photo de la caméra]'}
                                        for b in contenu]
        self.messages.append({'role': 'assistant', 'content': texte or '…'})
        if len(self.messages) > HISTORIQUE_MAX:          # oublie les plus anciens échanges, par paires
            self.messages = self.messages[-HISTORIQUE_MAX:]
            while self.messages and self.messages[0]['role'] != 'user':
                self.messages.pop(0)
        return texte

    def _executer_outils(self, reponse, phrase_finie):
        """Exécute les outils demandés par Claude. On ne renvoie pas le résultat à Claude (pas de 2e appel, donc
        pas d'attente en plus) : ce qui doit être dit l'est tout de suite, et une note reste dans l'historique."""
        notes = []
        for bloc in reponse.content:
            if bloc.type != 'tool_use' or not self.sur_outil:
                continue
            entree = bloc.input if isinstance(bloc.input, dict) else {}
            # les entrées arrivent en flux sans vérification par l'API : on les vérifie ici
            if not all(isinstance(v, str) for v in entree.values()):
                continue
            try:
                a_dire = self.sur_outil(bloc.name, entree)
            except Exception as e:
                a_dire = None; print(f'   (outil {bloc.name} en échec : {e})')
            notes.append(f'[{bloc.name} : {", ".join(entree.values())}]')
            if a_dire:
                if self.sur_morceau_outil:
                    self.sur_morceau_outil(' ' + a_dire)
                phrase_finie(a_dire)
        return notes

    def _echec(self, texte, sur_phrase):
        self.messages.pop()
        if sur_phrase:
            sur_phrase(texte)
        return texte

# --- Voix ---------------------------------------------------------------------------------
# Levé pendant que Câlin parle : la caméra suspend ses calculs pour laisser le processeur au son.
PAROLE = threading.Event()

class VoixElevenLabs:
    FREQ = 22050
    AVANCE = 0.8          # secondes de son reçues AVANT de commencer à jouer : plus de trous si le réseau ralentit
    AVANCE_DIRECT = 0.3   # en direct, la voix arrive en continu : petite réserve

    def __init__(self, cle, voix, modele=None):
        from elevenlabs.client import ElevenLabs
        self.client, self.voix, self.modele = ElevenLabs(api_key=cle), voix, modele or MODELE_VOIX
        self.dernier_texte = ''
        self.options_en_plus = True     # contexte d'intonation + langue ; retirées si le modèle les refuse

    def dire(self, texte):
        import sounddevice as sd
        from elevenlabs.core.api_error import ApiError
        def demander():
            extra = {}
            if self.options_en_plus:
                # le texte déjà dit sert de contexte : l'intonation continue d'une phrase à l'autre
                extra = {'language_code': 'fr', 'previous_text': self.dernier_texte[-300:] or None}
            flux = self.client.text_to_speech.stream(self.voix, text=texte, model_id=self.modele,
                                                     output_format=f'pcm_{self.FREQ}', **extra)
            return flux, next(iter(flux), b'')       # le 1er morceau déclenche l'appel : une erreur arrive ici
        try:
            flux, premier = demander()
        except ApiError as e:
            if not (self.options_en_plus and e.status_code in (400, 422)):
                raise
            print(f'   (le modèle de voix {self.modele} refuse le contexte ou la langue : nouvel essai sans)')
            self.options_en_plus = False
            flux, premier = demander()
        flux = itertools.chain([premier], flux)
        self.dernier_texte = (self.dernier_texte + ' ' + texte).strip()
        seuil, recu, sortie, reste = int(self.FREQ * 2 * self.AVANCE), b'', None, b''
        try:
            for morceau in flux:
                if sortie is None:
                    recu += morceau
                    if len(recu) < seuil:
                        continue
                    sortie = sd.RawOutputStream(samplerate=self.FREQ, channels=1, dtype='int16', latency='high')
                    sortie.start(); morceau, recu = recu, b''
                donnees = reste + morceau
                n = len(donnees) - len(donnees) % 2       # échantillons de 2 octets entiers
                sortie.write(donnees[:n]); reste = donnees[n:]
            if sortie is None and recu:                   # phrase courte : tout est arrivé avant le seuil
                sortie = sd.RawOutputStream(samplerate=self.FREQ, channels=1, dtype='int16', latency='high')
                sortie.start(); sortie.write(recu[:len(recu) - len(recu) % 2])
        finally:
            if sortie is not None:
                sortie.stop(); sortie.close()             # stop() attend la fin du son déjà envoyé

    def dire_en_direct(self, morceaux):
        """Envoie le texte au fil de l'eau (connexion directe d'ElevenLabs) et joue le son dès qu'il arrive.
        Lève une exception si la connexion est refusée avant le premier son (l'appelant repasse en phrases)."""
        import sounddevice as sd
        flux = self.client.text_to_speech.convert_realtime(self.voix, text=morceaux, model_id=self.modele,
                                                            output_format=f'pcm_{self.FREQ}')
        seuil, recu, sortie, reste = int(self.FREQ * 2 * self.AVANCE_DIRECT), b'', None, b''
        try:
            for morceau in flux:
                if sortie is None:
                    recu += morceau
                    if len(recu) < seuil:
                        continue
                    sortie = sd.RawOutputStream(samplerate=self.FREQ, channels=1, dtype='int16', latency='high')
                    sortie.start(); morceau, recu = recu, b''
                donnees = reste + morceau
                n = len(donnees) - len(donnees) % 2
                sortie.write(donnees[:n]); reste = donnees[n:]
            if sortie is None and recu:
                sortie = sd.RawOutputStream(samplerate=self.FREQ, channels=1, dtype='int16', latency='high')
                sortie.start(); sortie.write(recu[:len(recu) - len(recu) % 2])
        finally:
            if sortie is not None:
                sortie.stop(); sortie.close()

class VoixPC:
    """Voix de Windows (gratuite, hors ligne), choisie en français si possible."""
    def __init__(self):
        self.moteur = None

    def dire(self, texte):
        if self.moteur is None:                  # créée dans le fil qui parle (exigence de Windows)
            import pyttsx3
            self.moteur = pyttsx3.init()
            for v in self.moteur.getProperty('voices'):
                if 'fr' in (v.id + v.name).lower() or 'french' in v.name.lower():
                    self.moteur.setProperty('voice', v.id); break
            self.moteur.setProperty('rate', 170)
        self.moteur.say(texte); self.moteur.runAndWait()

class Bouche:
    """Dit les phrases dans l'ordre, dans un fil à part : la 1re phrase est prononcée pendant que Claude
    écrit la suite. finir() attend que tout soit dit."""
    def __init__(self, voix):
        self.voix, self.file, self.duree_premier_son, self.t0 = voix, queue.Queue(), None, None
        self.direct_possible = True
        threading.Thread(target=self._parler, daemon=True).start()

    def debut_tour(self):
        self.t0, self.duree_premier_son = time.time(), None

    def dire(self, texte):
        print(f'Câlin : {texte}')
        if self.voix:
            self.file.put(texte)

    def _parler(self):
        while True:
            textes = [self.file.get()]
            while True:                     # regroupe les phrases déjà arrivées : moins de coupures entre elles
                try:
                    textes.append(self.file.get_nowait())
                except queue.Empty:
                    break
            try:
                PAROLE.set()
                if self.duree_premier_son is None and self.t0:
                    self.duree_premier_son = time.time() - self.t0
                self.voix.dire(' '.join(textes))
            except Exception as e:          # une panne de voix ne doit pas arrêter la conversation
                print(f'   (voix indisponible : {e})')
            finally:
                PAROLE.clear()
                for _ in textes:
                    self.file.task_done()

    def finir(self):
        self.file.join()

    def repondre_en_direct(self, cerveau, phrase, **options):
        """Fait répondre le cerveau en envoyant le texte à la voix MOT PAR MOT (voix ElevenLabs en direct).
        Repli : si la voix en direct n'est pas possible, réponse dite phrase par phrase comme avant."""
        if not (self.voix and hasattr(self.voix, 'dire_en_direct') and self.direct_possible):
            return cerveau.repondre(phrase, sur_phrase=self.dire, **options)
        file_texte, fini, echec = queue.Queue(), threading.Event(), []
        def morceaux():
            while (m := file_texte.get()) is not None:
                yield m
        def parler_fil():
            try:
                PAROLE.set(); self.voix.dire_en_direct(morceaux())
            except Exception as e:
                echec.append(e)
            finally:
                PAROLE.clear(); fini.set()
        def premier_son(m):
            if self.duree_premier_son is None and self.t0:
                self.duree_premier_son = time.time() - self.t0
            file_texte.put(m)
        threading.Thread(target=parler_fil, daemon=True).start()
        texte = cerveau.repondre(phrase, sur_phrase=lambda t: print(f'Câlin : {t}'), sur_morceau=premier_son, **options)
        file_texte.put(None); fini.wait()
        if echec:
            print(f'   (voix en direct impossible : {echec[0]} ; retour à la voix phrase par phrase)')
            self.direct_possible = False
            self.dire(texte.split(' [')[0]); self.finir()
        return texte

def creer_voix(a, cles):
    if a.muet:
        return None
    if a.voix_pc or 'ELEVENLABS_API_KEY' not in cles:
        if not a.voix_pc:
            print('Pas de clé ElevenLabs : voix de Windows à la place.')
        return VoixPC()
    return VoixElevenLabs(cles['ELEVENLABS_API_KEY'], cles.get('ELEVENLABS_VOICE_ID', VOIX_ELEVENLABS),
                          MODELE_VOIX_RAPIDE if a.voix_rapide else None)

def options_communes(ap):
    ap.add_argument('--clavier', action='store_true', help='taper ses phrases au lieu de parler')
    ap.add_argument('--muet', action='store_true', help='réponses écrites seulement')
    ap.add_argument('--voix-pc', action='store_true', help='voix de Windows au lieu d\'ElevenLabs')
    ap.add_argument('--voix-rapide', action='store_true', help='ElevenLabs v4 turbo : démarre plus vite')
    ap.add_argument('--micro', type=int, help='numéro du micro (voir lister_micros.bat)')
    ap.add_argument('--ecoute', default='direct', choices=['direct', 'elevenlabs', 'whisper'],
                    help='transcription : direct (Scribe en direct, défaut), elevenlabs (Scribe phrase par phrase) '
                         'ou whisper (sur le PC, gratuit)')
    ap.add_argument('--modele', default='small', choices=['base', 'small', 'medium'], help='modèle Whisper (avec --ecoute whisper)')
    ap.add_argument('--ia', default='sonnet', choices=list(MODELES_IA), help='sonnet (défaut, rapide) ou opus (plus puissant)')

def cles_ou_quitter():
    cles, fichier = lire_cles()
    print('Fichier des clés :', fichier or 'aucun trouvé')
    if 'ANTHROPIC_API_KEY' not in cles:
        print('Clé Anthropic introuvable. Endroits cherchés :'); [print('  ', p) for p in ENDROITS_CLES]
        sys.exit('Ajouter une ligne ANTHROPIC_API_KEY=... dans un de ces fichiers (voir cles_exemple.txt).')
    return cles

def creer_oreille(a, cles):
    """Le micro, avec la transcription choisie (ElevenLabs si la clé est là, sinon Whisper sur le PC)."""
    from ecouter import charger_modele, Oreille, OreilleTempsReel, ScribeElevenLabs
    if a.ecoute == 'direct' and 'ELEVENLABS_API_KEY' in cles:
        try:
            o = OreilleTempsReel(cles['ELEVENLABS_API_KEY'], a.micro, muet=PAROLE.is_set)
            print('Transcription : ElevenLabs Scribe v2 en direct')
            return o
        except Exception as e:
            print(f'   ({e} : transcription phrase par phrase à la place)')
            a.ecoute = 'elevenlabs'
    if a.ecoute == 'elevenlabs' and 'ELEVENLABS_API_KEY' in cles:
        print('Transcription : ElevenLabs Scribe v2 (en ligne)')
        return Oreille(ScribeElevenLabs(cles['ELEVENLABS_API_KEY']), a.micro)
    if a.ecoute == 'elevenlabs':
        print('Pas de clé ElevenLabs : transcription Whisper sur le PC.')
    return Oreille(charger_modele(a.modele), a.micro)

def afficher_durees(d_ecoute, cerveau, bouche, d_total):
    morceaux = []
    if d_ecoute is not None:
        morceaux.append(f'compris en {d_ecoute:.1f} s')
    if cerveau.duree_premier_mot is not None:
        morceaux.append(f'1er mot de l\'IA {cerveau.duree_premier_mot:.1f} s')
    if bouche.duree_premier_son is not None:
        morceaux.append(f'1re phrase dite à {bouche.duree_premier_son:.1f} s')
    morceaux.append(f'réponse complète {d_total:.1f} s')
    print('   (' + ' · '.join(morceaux) + ')')

# --- Boucle -----------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description='Tête du robot : conversation à voix haute')
    options_communes(ap)
    a = ap.parse_args()
    cles = cles_ou_quitter()
    cerveau = Cerveau(cles['ANTHROPIC_API_KEY'], MODELES_IA[a.ia])
    bouche = Bouche(creer_voix(a, cles))
    oreille = None if a.clavier else creer_oreille(a, cles)

    def tour(texte_dit):
        bouche.dire(texte_dit); bouche.finir()
        if oreille:
            oreille.vider()             # oublie ce que le micro a capté pendant que Câlin parlait

    tour('Bonjour, je suis Câlin. Je vous écoute !')
    try:
        while True:
            d_ecoute = None
            if oreille:
                phrase = oreille.phrase(); d_ecoute = oreille.duree_comprehension; print(f'Vous : {phrase}')
            else:
                phrase = input('Vous : ').strip()
                if not phrase:
                    continue
            t = time.time(); bouche.debut_tour()
            bouche.repondre_en_direct(cerveau, phrase)
            bouche.finir()
            afficher_durees(d_ecoute, cerveau, bouche, time.time() - t)
            if oreille:
                oreille.vider()
            if any(m in phrase.lower() for m in MOTS_FIN):
                break
    except (KeyboardInterrupt, EOFError):
        print('\nArrêt.')
    finally:
        if oreille:
            oreille.fermer()

if __name__ == '__main__':
    main()
