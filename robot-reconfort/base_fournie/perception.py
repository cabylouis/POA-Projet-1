from typing import Dict, List, Optional, Tuple

Case = Tuple[int, int]

MUR, LIBRE, ARMOIRE, DICTIONNAIRE, RESIDENT = ("mur", "libre", "armoire", "dictionnaire", "resident")

class Perception:
    voisins: Dict[str, str]
    devant_armoire: bool = False
    contenu_casier: Optional[str] = None

class Resultat:
    ok: bool = True
    donnees: object = None

class Connaissances:
    hauteur: int
    largeur: int
    depart: Case
    armoire: Case
    dictionnaire: Case
    residents: Dict[str, Case]      # id -> position
    noms_residents: Dict[str, str]  # id -> nom
    emotions: List[str]             # ordre de la roue
    intensites: List[str]
    casier_depart: Case