"""Comprendre une consigne dite à Câlin pendant le tri : « range les ronds dans le bac de gauche et le reste à droite »
(demande de Nicolas, 26/11/2026 : la voix et la reconnaissance des formes).

Comment ça marche :
  1. la phrase est entendue par l'oreille de la tête (tete/ecouter.py, Whisper, sur le PC) ;
  2. on envoie à Claude la PHOTO de la table, chaque objet numéroté (comme à l'écran), avec la phrase ;
  3. Claude reconnaît la forme de chaque objet (rond, carré, hexagone, barre, gobelet…) et répond, dans une forme imposée,
     quels numéros vont dans le bac de GAUCHE, lesquels dans celui de DROITE, et lesquels on laisse ;
  4. le tri prend ces objets un par un et les pose là où Claude l'a dit (au lieu de les ranger d'après leur taille).
« Stop » et « arrête » sont compris SANS Claude, tout de suite : le bras s'arrête et reste tenu, comme avec la touche ESPACE.

Pourquoi Claude pour les formes : le calcul seul (largeur de l'objet dans toutes les directions) a été essayé
sur les photos du 26/11/2026 : les ronds ressortaient en « barres » à cause du penché et des reflets. Claude voit la photo
comme nous. La clé d'API reste sur le PC de Nicolas (même fichier que la tête : voir tete/cles_exemple.txt), jamais dans le dépôt.
La photo de la table part chez Anthropic pour être analysée : n'y mettre que les objets à trier (pas de visages, pas de papiers)."""
import json, sys
from pathlib import Path
import cv2

TETE = Path(__file__).resolve().parent.parent / 'tete'
MOTS_STOP = ('stop', 'arrête', 'arrete', 'arrêtes', 'halte', 'pause')
FORMES = ['rond', 'carre', 'hexagone', 'barre', 'gobelet', 'autre']
NOMS = {'rond': 'rond', 'carre': 'carré', 'hexagone': 'hexagone', 'barre': 'barre', 'gobelet': 'gobelet', 'autre': 'autre objet'}

SCHEMA = {
    'type': 'object',
    'properties': {
        'objets': {'type': 'array', 'items': {
            'type': 'object',
            'properties': {'n': {'type': 'integer'}, 'forme': {'type': 'string', 'enum': FORMES}, 'description': {'type': 'string'}},
            'required': ['n', 'forme', 'description'], 'additionalProperties': False}},
        'action': {'type': 'string', 'enum': ['trier', 'taille', 'rien']},
        'gauche': {'type': 'array', 'items': {'type': 'integer'}},
        'droite': {'type': 'array', 'items': {'type': 'integer'}},
        'reponse': {'type': 'string'},
    },
    'required': ['objets', 'action', 'gauche', 'droite', 'reponse'],
    'additionalProperties': False,
}

CONSIGNES = """Tu es Câlin, un robot de table à un bras, chez Nicolas (centre équestre). Une caméra au-dessus de la table te montre
les objets à trier, chacun entouré et numéroté (« 1 : 46 mm (X … Y …) » : numéro, largeur vue, position en mm). Les 4 carrés
noir et blanc aux coins sont des repères, pas des objets. Le bac de GAUCHE et le bac de DROITE sont au bord de la table, vus
depuis derrière le bras (le bras est en bas de la photo : la GAUCHE de la photo est la gauche du bras).

Pour chaque numéro, donne sa forme vue d'en haut (rond = cylindre posé debout, carre = cube ou pavé à base carrée, hexagone,
barre = pavé nettement plus long que large, gobelet, autre) et une description de 2 à 5 mots. Les objets sont hauts de 6 cm
et vus un peu de biais : tu vois leur face du DESSUS (plus claire) et un ou deux flancs (plus sombres). La forme, c'est le
contour de la face du dessus : un cercle = rond, 4 côtés égaux = carre, 6 côtés = hexagone, rectangle allongé = barre.
Un petit cylindre reste un rond.

Puis lis la phrase de Nicolas :
- s'il demande de ranger, trier ou prendre des objets, action = "trier" : mets dans « gauche » et « droite » les numéros à poser
  dans chaque bac ; ceux dont il ne parle pas, ne les mets nulle part (on les laisse), sauf s'il dit « le reste » ou « tout » ;
- s'il demande de trier par TAILLE (petits / gros) sans parler de formes, action = "taille" (la pince mesure elle-même) ;
- sinon (question, bavardage, phrase mal entendue), action = "rien".
« reponse » : une phrase courte, en français, que Câlin dit à Nicolas (ce qu'il va faire, ou ce qu'il n'a pas compris).
N'invente pas de numéro qui n'est pas sur la photo."""

def est_stop(texte):
    t = texte.lower().strip(' .!?…,')
    return any(t == m or t.startswith(m + ' ') or t.endswith(' ' + m) for m in MOTS_STOP) or t in ('stop câlin', 'câlin stop')

def client_claude():
    """Le client Anthropic, avec la clé de la tête (variables d'environnement, ou fichier de clés de Nicolas)."""
    sys.path.insert(0, str(TETE))
    from parler import lire_cles                                     # même lecture des clés que la conversation de la tête
    import anthropic
    cles, _ = lire_cles()
    if 'ANTHROPIC_API_KEY' not in cles: raise RuntimeError('pas de clé Anthropic : voir tete/cles_exemple.txt')
    return anthropic.Anthropic(api_key=cles['ANTHROPIC_API_KEY'])

def planche(image, cadres, cote=260, par_ligne=4):
    """Une image où chaque objet est découpé dans la photo BRUTE, agrandi, son numéro écrit au-dessus (rien n'est dessiné sur
    l'objet). cadres : pour chaque objet, son rectangle (x0, y0, x1, y1) dans la photo. Premier tri à la voix de Nicolas
    (26/11/2026) : sur la photo annotée, les étiquettes recouvraient les objets et ils ne faisaient que 70 points de large ;
    l'hexagone était pris pour une barre, la barre pour un carré, le petit rond pour « autre »."""
    import numpy as np
    H, W = image.shape[:2]; cases = []
    for n, (x0, y0, x1, y1) in enumerate(cadres, 1):
        c = max(x1 - x0, y1 - y0) / 2 + 25; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        a, b_, d, e = int(max(cx - c, 0)), int(max(cy - c, 0)), int(min(cx + c, W)), int(min(cy + c, H))
        bout = image[b_:e, a:d]
        if bout.size == 0: bout = np.zeros((10, 10, 3), np.uint8)
        k = cote / max(bout.shape[:2]); bout = cv2.resize(bout, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
        case = np.full((cote + 44, cote, 3), 255, np.uint8); case[44:44 + bout.shape[0], :bout.shape[1]] = bout
        cv2.putText(case, f'objet {n}', (8, 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.rectangle(case, (0, 0), (cote - 1, cote + 43), (0, 0, 0), 1); cases.append(case)
    lignes = []
    for i in range(0, len(cases), par_ligne):
        r = cases[i:i + par_ligne]; r += [np.full_like(cases[0], 255)] * (par_ligne - len(r)); lignes.append(np.hstack(r))
    return np.vstack(lignes) if lignes else np.full((cote, cote, 3), 255, np.uint8)

def interpreter(client, image_annotee, phrase, objets, modele='claude-sonnet-5-5', gros_plans=None):
    """Envoie la photo numérotée et la phrase à Claude. Renvoie le dict du SCHEMA. objets : la liste dans l'ordre des numéros.
    gros_plans : la planche des objets agrandis (planche()), envoyée en plus : c'est elle qui sert à reconnaître les formes.
    Sonnet par défaut : c'est le choix de Nicolas pour la tête (rapide)."""
    import base64
    def jpg(im):
        ok, j = cv2.imencode('.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not ok: raise RuntimeError('photo illisible')
        return {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': base64.standard_b64encode(j.tobytes()).decode()}}
    images = [jpg(image_annotee)] + ([jpg(gros_plans)] if gros_plans is not None else [])
    liste = '\n'.join(f'{n} : vu {o["largeur"]:.0f} mm de large, en X {o["X"]:+.0f}, Y {o["Y"]:.0f}' for n, o in enumerate(objets, 1))
    demande = dict(
        model=modele, max_tokens=16000,
        output_config={'effort': 'medium', 'format': {'type': 'json_schema', 'schema': SCHEMA}},
        system=CONSIGNES,
        messages=[{'role': 'user', 'content': images + [
            {'type': 'text', 'text': ('Première image : la table entière, objets entourés et numérotés. Deuxième image : chaque objet '
                                      'découpé et agrandi, son numéro écrit au-dessus (« objet 3 ») : sers-toi de celle-ci pour les formes.\n'
                                      if gros_plans is not None else '')
                                     + f'Objets numérotés :\n{liste}\n\nNicolas dit : « {phrase} »'}]}])
    try:   # si la demande est refusée par sécurité, un autre modèle la reprend (paramètre « fallbacks »)
        r = client.beta.messages.create(betas=['server-side-fallback-2026-07-01'], fallbacks='default', **demande)
    except TypeError:
        try: r = client.messages.create(**demande)                       # bibliothèque anthropic trop ancienne pour « fallbacks »
        except TypeError: raise RuntimeError('bibliothèque anthropic trop ancienne : ..\\tete\\.venv\\Scripts\\python -m pip install -U anthropic')
    if r.stop_reason == 'refusal': raise RuntimeError('Claude a refusé la demande')
    texte = next((b.text for b in r.content if b.type == 'text'), '')
    return verifier(json.loads(texte), len(objets))

def verifier(rep, nb):
    """Garde-fous sur la réponse : numéros existants, un objet dans un seul bac."""
    ok = set(range(1, nb + 1))
    g = [n for n in dict.fromkeys(rep.get('gauche', [])) if n in ok]
    d = [n for n in dict.fromkeys(rep.get('droite', [])) if n in ok and n not in g]
    rep['gauche'], rep['droite'] = g, d
    if rep.get('action') == 'trier' and not (g or d): rep['action'] = 'rien'
    return rep

def plan_de(rep, objets):
    """La liste des objets à poser : [{'X', 'Y', 'zone', 'forme'}] ; zone 'petit' = bac de gauche, 'gros' = bac de droite."""
    formes = {o['n']: o['forme'] for o in rep.get('objets', [])}
    return [{'X': objets[n - 1]['X'], 'Y': objets[n - 1]['Y'], 'zone': z, 'forme': formes.get(n, '?'), 'n': n}
            for cote, z in (('gauche', 'petit'), ('droite', 'gros')) for n in rep[cote]]
