from perception import (MUR, LIBRE, ARMOIRE, DICTIONNAIRE, RESIDENT, Resultat, Connaissances)
from planification import (DIRECTIONS, voisin)
from reconfort_io import ACTIONS
from selecteur import appliquer_deplacement
from perception import Perception

Case = tuple[int, int]

SYMBOLES = {"#": MUR, ".": LIBRE, "R": LIBRE, "A": ARMOIRE, "D": DICTIONNAIRE, "P": RESIDENT}

class ActionIllegale(Exception):
    """ Action impossible ou non autorisée dans l'environnement. """
    pass

def adjacent(a: Case, b: Case) -> bool:
    """ Indique si deux cases sont adjacentes. """
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

class Environnement:
    """Représente le monde du robot et gère l'exécution de ses actions.

    Attributs :
        plan : Grille représentant la nature des cases.
        pos : Position actuelle du robot.
        armoire_pos : Position de l'armoire.
        dict_pos : Position du dictionnaire.
        residents : Positions des résidents, indexées par identifiant.
        casiers : Contenu des casiers, indexé par position.
        selecteur_pos : Position actuelle du sélecteur de casier.
        n_ligne : Nombre de lignes de l'armoire.
        n_colonne : Nombre de colonnes de l'armoire.
        entrees : Entrées du dictionnaire des émotions.
        objet_porte : Objet actuellement transporté par le robot.
        resident_courant : Identifiant du résident concerné.
    """

    def __init__(self, carte: dict, armoire: dict, dictionnaire: dict) -> None:
        """ Initialise l'environnement à partir des données du monde. """

        self.plan = []

        for ligne in carte["grille"]:
            nouvelle_ligne = []

            for symbole in ligne:
                nouvelle_ligne.append(SYMBOLES[symbole])

            self.plan.append(nouvelle_ligne)

        self.pos: Case = tuple(carte["depart_robot"])
        self.armoire_pos: Case = tuple(carte["armoire"]["position"])
        self.dict_pos: Case = tuple(carte["dictionnaire"]["position"])

        self.residents: dict[str, Case] = {}
        for resident in carte["residents"]:
            self.residents[resident["id"]] = tuple(resident["position"])

        self.casiers: dict[Case, str] = {}
        for casier in armoire["casiers"]:
            self.casiers[(casier["ligne"], casier["colonne"])] = casier["objet"]

        self.selecteur_pos: Case = tuple(armoire["casier_depart"])
        self.n_ligne = len(armoire["intensites"])
        self.n_colonne = len(armoire["emotions"])

        self.entrees = dictionnaire["entrees"]

        self.objet_porte: str | None = None
        self.resident_courant: str | None = None

    def accepter_demande(self, resident: str) -> None:
        """ Enregistre le résident à qui le robot doit répondre. """

        self.resident_courant = resident

    def type(self, case: Case) -> str:
        """ Retourne la nature de la case indiquée. """

        return self.plan[case[0]][case[1]]

    def percevoir(self) -> Perception:
        """Retourne la perception actuelle du robot."""

        voisins = {}

        for direction in DIRECTIONS:
            voisins[direction] = self.type(voisin(self.pos, direction))

        devant = adjacent(self.pos, self.armoire_pos)
        contenu = self.casiers[self.selecteur_pos] if devant else None

        return Perception(voisins, devant, contenu)

    def executer(self, nom_action: str, argument_action: str | None = None) -> Resultat:
        """ Vérifie et exécute l'action demandée. """

        if nom_action not in ACTIONS:
            raise ActionIllegale(f"Action inconnue : {nom_action!r}")

        return getattr(self, nom_action.lower())(argument_action)

    def avancer(self, direction: str) -> Resultat:
        """ Déplace le robot d'une case dans la direction indiquée. """

        if direction not in DIRECTIONS:
            raise ActionIllegale(f"Direction inconnue : {direction!r}")

        cible = voisin(self.pos, direction)
        if self.type(cible) != LIBRE:
            raise ActionIllegale(f"AVANCER {direction} depuis {self.pos} : "f"la case {cible} n'est pas libre")

        self.pos = cible
        return Resultat()

    def consulter(self, _) -> Resultat:
        """ Retourne les entrées du dictionnaire si le robot est adjacent. """

        if not adjacent(self.pos, self.dict_pos):
            raise ActionIllegale(f"CONSULTER : Pas adjacent au dictionnaire")

        return Resultat(True, self.entrees)

    def chercher(self, direction) -> Resultat:
        """ Déplace le sélecteur de casier dans la direction indiquée. """

        if not adjacent(self.pos, self.armoire_pos):
            raise ActionIllegale(f"CHERCHER : Pas adjacent a l'armoire")

        try:
            self.selecteur_pos = appliquer_deplacement(self.selecteur_pos, direction, self.n_ligne, self.n_colonne)

        except ValueError as err:
            raise ActionIllegale(f"CHERCHER : {direction} : {err}")

        return Resultat()

    def prendre(self, nom_objet) -> Resultat:
        """ Prend l'objet indiqué dans le casier sélectionné. """

        if not adjacent(self.pos, self.armoire_pos):
            raise ActionIllegale("PRENDRE : pas adjacent a l'armoire")

        if self.objet_porte is not None:
            raise ActionIllegale("PRENDRE : le robot transporte deja un objet")

        if self.casiers.get(self.selecteur_pos) is None:
            raise ActionIllegale("PRENDRE : casier vide")

        if nom_objet != self.casiers[self.selecteur_pos]:
            raise ActionIllegale(f"PRENDRE {nom_objet!r} : le casier contient "f"{self.casiers[self.selecteur_pos]!r}")

        self.objet_porte = nom_objet
        return Resultat()

    def donner(self, nom_objet) -> Resultat:
        """ Donne l'objet transporté au résident concerné. """

        cible = self.residents.get(self.resident_courant)

        if cible is None or not adjacent(self.pos, cible):
            raise ActionIllegale("DONNER : pas adjacent au resident concerne")

        if self.objet_porte is None or self.objet_porte != nom_objet:
            raise ActionIllegale(f"DONNER {nom_objet!r} : objet non transporte")

        self.objet_porte = None
        return Resultat()

    def attendre(self, _) -> Resultat:
        """ Exécute l'action d'attente sans modifier l'environnement. """

        return Resultat()


def preparer_monde(carte: dict, armoire: dict, dictionnaire: dict) -> tuple[Environnement, Connaissances]:
    """ Prépare l'environnement et les connaissances initiales du robot. """

    positions_residents = {}
    for resident in carte["residents"]:
        positions_residents[resident["id"]] = tuple(resident["position"])

    noms_residents = {}
    for resident in carte["residents"]:
        noms_residents[resident["id"]] = resident["nom"]

    connaissances = Connaissances(
        hauteur = carte["dimensions"]["hauteur"],
        largeur = carte["dimensions"]["largeur"],

        depart = tuple(carte["depart_robot"]),
        casier_depart = tuple(armoire["casier_depart"]),
        armoire = tuple(carte["armoire"]["position"]),
        dictionnaire = tuple(carte["dictionnaire"]["position"]),

        residents = positions_residents,
        noms_residents = noms_residents,

        emotions = list(armoire["emotions"]),
        intensites = list(armoire["intensites"])
    )
    return Environnement(carte, armoire, dictionnaire), connaissances
