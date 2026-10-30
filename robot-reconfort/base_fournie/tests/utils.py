import copy
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

DICO = json.loads((RACINE / "donnees" / "dictionnaire.json").read_text("utf-8"))
ARMOIRE = json.loads((RACINE / "donnees" / "armoire_standard.json").read_text("utf-8"))
CARTE_01 = json.loads((RACINE / "cartes" / "appartement_01.json").read_text("utf-8"))
SCENARIO_01 = json.loads((RACINE / "cartes" / "scenario_01.json").read_text("utf-8"))


def copie(x):
    return copy.deepcopy(x)


def carte_depuis_grille(grille, nom="mini"):
    """Construit un dict carte à partir d'une grille de texte (R, A, D, P)."""
    pos = {}
    residents = []
    for l, ligne in enumerate(grille):
        for c, ch in enumerate(ligne):
            if ch == "P":
                residents.append({
                    "id": f"R{len(residents) + 1}",
                    "nom": f"N{len(residents) + 1}",
                    "position": [l, c]
                })
            elif ch in "RAD":
                pos[ch] = [l, c]
    return {
        "format": "robot-reconfort/carte", "version": 1, "nom": nom,
        "dimensions": {"hauteur": len(grille), "largeur": len(grille[0])},
        "grille": list(grille), "depart_robot": pos["R"],
        "armoire": {"position": pos["A"]},
        "dictionnaire": {"position": pos["D"]}, "residents": residents
    }


def scenario(demandes, carte="mini"):
    return {
        "format": "robot-reconfort/scenario", "version": 1, "nom": "sc",
        "carte": carte, "armoire": "armoire_standard",
        "demandes": [{"numero": i + 1, "resident": r, "message": m} for i, (r, m) in enumerate(demandes)]
    }


def armoire_avec(vides=(), objets=None):
    """Armoire standard dont les casiers `vides` (ligne, colonne) sont vides."""
    a = copie(ARMOIRE)
    for c in a["casiers"]:
        if (c["ligne"], c["colonne"]) in vides:
            c["objet"] = None
    return a
