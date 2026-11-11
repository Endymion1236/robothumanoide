"""Tête du robot — étape 3 : RÉPONDRE (et étape 4 : tout relier).

Boucle de conversation :  tu parles → Whisper écrit ta phrase → Claude répond → la voix la dit.
Le robot s'appelle Câlin, comme la borne d'accueil du club (on les réunira plus tard).

Utilisation :  python parler.py              (micro + voix ElevenLabs)
               python parler.py --clavier    (taper ses phrases au lieu de parler)
               python parler.py --muet       (réponses écrites seulement, sans voix)
               python parler.py --voix-pc    (voix de Windows, gratuite, au lieu d'ElevenLabs)
Dire « au revoir » ou Ctrl + C pour arrêter.

Clés : fichier texte hors du projet (voir cles_exemple.txt), lignes ANTHROPIC_API_KEY=... et
ELEVENLABS_API_KEY=... ; facultatif : ELEVENLABS_VOICE_ID=... pour choisir une autre voix.
"""
import argparse, os, sys, time
from pathlib import Path
import numpy as np

# --- Réglages -------------------------------------------------------------------------------
MODELE_IA = 'claude-opus-5-5'          # la borne du club utilise claude-sonnet-5-5 (plus rapide, moins cher)
EFFORT = 'low'                         # conversation simple : réflexion courte, réponse plus rapide
VOIX_ELEVENLABS = 'JBFqnCBsd6RMkjVDRZzb'   # voix par défaut (multilingue) ; remplaçable dans le fichier des clés
MODELE_VOIX = 'eleven_multilingual_v2'     # parle français avec n'importe quelle voix
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
class Cerveau:
    def __init__(self, cle):
        import anthropic
        self.anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=cle)
        self.messages = []

    def repondre(self, phrase):
        self.messages.append({'role': 'user', 'content': phrase})
        try:
            reponse = self.client.beta.messages.create(
                model=MODELE_IA,
                max_tokens=4000,
                system=PERSONNALITE,
                messages=self.messages,
                output_config={'effort': EFFORT},
                # si le modèle refuse une demande, l'API passe la main à un autre modèle dans le même appel
                betas=['server-side-fallback-2026-07-01'],
                fallbacks='default',
            )
        except self.anthropic.AuthenticationError:
            self.messages.pop(); return 'Ma clé Anthropic ne marche pas. Vérifiez le fichier des clés.'
        except self.anthropic.RateLimitError:
            self.messages.pop(); return 'Je réfléchis trop vite, laissez-moi souffler quelques secondes.'
        except self.anthropic.APIConnectionError:
            self.messages.pop(); return 'Je n\'arrive pas à joindre internet.'
        except self.anthropic.APIStatusError as e:
            self.messages.pop(); return f'Mon cerveau a un souci technique, erreur {e.status_code}.'
        if reponse.stop_reason == 'refusal':
            self.messages.pop(); return 'Je préfère ne pas répondre à ça.'
        # on garde la réponse complète dans l'historique (la réflexion du modèle doit lui être rendue telle quelle)
        self.messages.append({'role': 'assistant', 'content': reponse.content})
        if len(self.messages) > HISTORIQUE_MAX:          # oublie les plus anciens échanges, par paires
            self.messages = self.messages[-HISTORIQUE_MAX:]
            while self.messages and self.messages[0]['role'] != 'user':
                self.messages.pop(0)
        return ' '.join(b.text for b in reponse.content if b.type == 'text').strip()

# --- Voix ---------------------------------------------------------------------------------
class VoixElevenLabs:
    def __init__(self, cle, voix):
        from elevenlabs.client import ElevenLabs
        self.client, self.voix = ElevenLabs(api_key=cle), voix

    def dire(self, texte):
        import sounddevice as sd
        morceaux = self.client.text_to_speech.convert(
            self.voix, text=texte, model_id=MODELE_VOIX, language_code='fr', output_format='pcm_22050')
        son = np.frombuffer(b''.join(morceaux), dtype=np.int16)
        sd.play(son, 22050); sd.wait()

class VoixPC:
    """Voix de Windows (gratuite, hors ligne), choisie en français si possible."""
    def __init__(self):
        import pyttsx3
        self.moteur = pyttsx3.init()
        for v in self.moteur.getProperty('voices'):
            if 'fr' in (v.id + v.name).lower() or 'french' in v.name.lower():
                self.moteur.setProperty('voice', v.id); break
        self.moteur.setProperty('rate', 170)

    def dire(self, texte):
        self.moteur.say(texte); self.moteur.runAndWait()

# --- Boucle -----------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description='Tête du robot : conversation à voix haute')
    ap.add_argument('--clavier', action='store_true', help='taper ses phrases au lieu de parler')
    ap.add_argument('--muet', action='store_true', help='réponses écrites seulement')
    ap.add_argument('--voix-pc', action='store_true', help='voix de Windows au lieu d\'ElevenLabs')
    ap.add_argument('--micro', type=int, help='numéro du micro (voir lister_micros.bat)')
    ap.add_argument('--modele', default='small', choices=['base', 'small', 'medium'], help='reconnaissance vocale')
    a = ap.parse_args()

    cles, fichier = lire_cles()
    print('Fichier des clés :', fichier or 'aucun trouvé')
    if 'ANTHROPIC_API_KEY' not in cles:
        print('Clé Anthropic introuvable. Endroits cherchés :'); [print('  ', p) for p in ENDROITS_CLES]
        sys.exit('Ajouter une ligne ANTHROPIC_API_KEY=... dans un de ces fichiers (voir cles_exemple.txt).')
    cerveau = Cerveau(cles['ANTHROPIC_API_KEY'])

    voix = None
    if not a.muet:
        if a.voix_pc or 'ELEVENLABS_API_KEY' not in cles:
            if not a.voix_pc:
                print('Pas de clé ElevenLabs : voix de Windows à la place.')
            voix = VoixPC()
        else:
            voix = VoixElevenLabs(cles['ELEVENLABS_API_KEY'], cles.get('ELEVENLABS_VOICE_ID', VOIX_ELEVENLABS))

    oreille = None
    if not a.clavier:
        from ecouter import charger_modele, Oreille
        oreille = Oreille(charger_modele(a.modele), a.micro)

    def dire(texte):
        print(f'Câlin : {texte}')
        if voix:
            try:
                voix.dire(texte)
            except Exception as e:      # une panne de voix ne doit pas arrêter la conversation
                print(f'   (voix indisponible : {e})')
        if oreille:
            oreille.vider()             # oublie ce que le micro a capté pendant que Câlin parlait

    dire('Bonjour, je suis Câlin. Je vous écoute !')
    try:
        while True:
            if oreille:
                phrase = oreille.phrase(); print(f'Vous : {phrase}')
            else:
                phrase = input('Vous : ').strip()
                if not phrase:
                    continue
            t = time.time()
            reponse = cerveau.repondre(phrase)
            print(f'   (réponse en {time.time() - t:.1f} s)')
            dire(reponse)
            if any(m in phrase.lower() for m in MOTS_FIN):
                break
    except (KeyboardInterrupt, EOFError):
        print('\nArrêt.')
    finally:
        if oreille:
            oreille.fermer()

if __name__ == '__main__':
    main()
