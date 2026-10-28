from dataclasses import dataclass

Case = tuple[int, int]

MUR, LIBRE, ARMOIRE, DICTIONNAIRE, RESIDENT = ("mur", "libre", "armoire", "dictionnaire", "resident")

@dataclass
class Perception:
    """ Informations perçues par le robot dans son environnement. """

    voisins: dict[str, str]
    devant_armoire: bool = False
    contenu_casier: str | None = None

@dataclass
class Resultat:
    """ Résultat d'une action exécutée par le robot. """

    ok: bool = True
    donnees: list[dict[str, str]] | None = None

@dataclass
class Connaissances:
    """ Informations connues par le robot sur son environnement. """

    hauteur: int
    largeur: int
    depart: Case
    armoire: Case
    dictionnaire: Case
    residents: dict[str, Case]
    noms_residents: dict[str, str]
    emotions: list[str]
    intensites: list[str]
    casier_depart: Case