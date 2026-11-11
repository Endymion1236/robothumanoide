"""Où Câlin range ce qu'il apprend (souvenirs, visages) : sur le PC, HORS du dossier du projet.
Jamais sur GitHub, et pas effacé quand on retélécharge le projet."""
from pathlib import Path

def dossier_perso():
    racine = Path('C:/projet robot')
    d = (racine if racine.is_dir() else Path.home()) / 'calin_donnees'
    d.mkdir(parents=True, exist_ok=True)
    return d
