from typing import Dict, List, Optional, Tuple

Case = Tuple[int, int]

MUR, LIBRE, ARMOIRE, DICTIONNAIRE, RESIDENT = ("mur", "libre", "armoire", "dictionnaire", "resident")

class Perception:
    voisins: Dict[str, str]
    devant_armoire: bool = False
    contenu_casier: Optional[str] = None

class Resultat:
    def __init__(self, ok: bool = True, donnees: object = None):
        self.ok = ok
        self.donnees = donnees

class Connaissances:
    def __init__(
        self,
        hauteur: int,
        largeur: int,
        depart: Case,
        armoire: Case,
        dictionnaire: Case,
        residents: Dict[str, Case],
        noms_residents: Dict[str, str],
        emotions: List[str],
        intensites: List[str],
        casier_depart: Case
    ) -> None:
        self.hauteur = hauteur
        self.largeur = largeur
        self.depart = depart
        self.armoire = armoire
        self.dictionnaire = dictionnaire
        self.residents = residents
        self.noms_residents = noms_residents
        self.emotions = emotions
        self.intensites = intensites
        self.casier_depart = casier_depart