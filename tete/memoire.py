"""Mémoire de Câlin : des faits courts, datés, rattachés à une personne, gardés d'une conversation à l'autre.

Fichier : calin_donnees/memoire.json (hors du projet). Pour tout effacer : supprimer ce fichier,
ou dire « Câlin, oublie tout ce que tu sais sur moi »."""
import json, time
from pathlib import Path

MAX_DANS_LE_PROMPT = 80          # au-delà, seuls les plus récents sont rappelés à Câlin

class Memoire:
    def __init__(self, chemin):
        self.chemin = Path(chemin)
        self.faits = json.loads(self.chemin.read_text(encoding='utf-8')) if self.chemin.is_file() else []

    def _ecrire(self):
        tmp = self.chemin.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.faits, ensure_ascii=False, indent=1), encoding='utf-8')
        tmp.replace(self.chemin)              # écriture d'un coup : pas de fichier à moitié écrit

    def retenir(self, fait, personne=''):
        fait, personne = fait.strip(), personne.strip()
        if not fait:
            return False
        if any(f['fait'].lower() == fait.lower() and f['personne'].lower() == personne.lower() for f in self.faits):
            return False                       # déjà su
        self.faits.append({'date': time.strftime('%d/%m/%Y'), 'personne': personne, 'fait': fait})
        self._ecrire()
        return True

    def oublier(self, personne):
        """Efface tous les faits d'une personne ; renvoie leur nombre."""
        avant = len(self.faits)
        self.faits = [f for f in self.faits if f['personne'].lower() != personne.strip().lower()]
        self._ecrire()
        return avant - len(self.faits)

    def texte(self):
        if not self.faits:
            return 'Tu ne te souviens encore de rien : c\'est ta première conversation.'
        lignes = [f"- {f['date']}{' (' + f['personne'] + ')' if f['personne'] else ''} : {f['fait']}"
                  for f in self.faits[-MAX_DANS_LE_PROMPT:]]
        return 'Ce dont tu te souviens des conversations précédentes :\n' + '\n'.join(lignes)
