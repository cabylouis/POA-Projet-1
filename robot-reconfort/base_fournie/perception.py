from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

Case = Tuple[int, int]

MUR, LIBRE, ARMOIRE, DICTIONNAIRE, RESIDENT = ("mur", "libre", "armoire", "dictionnaire", "resident")

@dataclass
class Perception:
    voisins: Dict[str, str]
    devant_armoire: bool = False
    contenu_casier: Optional[str] = None

@dataclass
class Resultat:
    ok: bool = True
    donnees: object = None

@dataclass
class Connaissances:
    hauteur: int
    largeur: int
    depart: Case
    armoire: Case
    dictionnaire: Case
    residents: Dict[str, Case]
    noms_residents: Dict[str, str]
    emotions: List[str]
    intensites: List[str]
    casier_depart: Case