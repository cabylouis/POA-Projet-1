from typing import Tuple, Dict, Optional

from perception import (MUR, LIBRE, ARMOIRE, DICTIONNAIRE, RESIDENT, Resultat, Connaissances)
from planification import (DIRECTIONS, voisin)
from reconfort_io import ACTIONS
from selecteur import appliquer

Case = Tuple[int, int]

SYMBOLES = {"#": MUR, ".": LIBRE, "R": LIBRE, "A": ARMOIRE, "D": DICTIONNAIRE, "P": RESIDENT}


class ActionIllegale(Exception):
    pass


class Environnement:
    def __init__(self, carte: dict, armoire: dict, dictionnaire: dict) -> None:
        self.plan = []

        for ligne in carte["grille"]:
            nouvelle_ligne = []

            for s in ligne:
                nouvelle_ligne.append(SYMBOLES[s])

            self.plan.append(nouvelle_ligne)

        self.pos: Case = tuple(carte["depart_robot"])
        self.armoire_pos: Case = tuple(carte["armoire"]["position"])
        self.dict_pos: Case = tuple(carte["dictionnaire"]["position"])

        self.residents: Dict[str, Case] = {}
        for r in carte["residents"]:
            self.residents[r["id"]] = tuple(r["position"])

        self.casiers: Dict[Case, str] = {}
        for c in armoire["casiers"]:
            self.casiers[(c["ligne"], c["colonne"])] = c["objet"]

        self.selecteur: Case = tuple(armoire["casier_depart"])
        self.n_ligne = len(armoire["intensites"])
        self.n_colonne = len(armoire["emotions"])

        self.entrees = dictionnaire["entrees"]

        self.objet_porte: Optional[str] = None
        self.resident_courant: Optional[str] = None

    def accepter_demande(self, resident: str):
        self.resident_courant = resident

    def type(self, case: Case):
        return self.plan[case[0]][case[1]]

    def adjacent(self, a: Case, b: Case) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def executer(self, nom: str, argument: Optional[str] = None) -> Resultat:
        if nom not in ACTIONS:
            raise ActionIllegale(f"Action inconnue : {nom!r}")

        return getattr(self, nom.lower())(argument)

    def avancer(self, direction: str):
        if direction not in DIRECTIONS:
            raise ActionIllegale(f"Direction inconnue : {direction!r}")

        cible = voisin(self.pos, direction)
        if self.type(cible) != LIBRE:
            raise ActionIllegale(f"AVANCER {direction} depuis {self.pos} : "f"la case {cible} n'est pas libre")

        self.pos = cible
        return Resultat()

    def consulter(self, _):
        if not self.adjacent(self.pos, self.dict_pos):
            raise ActionIllegale(f"CONSULTER : Pas adjacent au dictionnaire")

        return Resultat(True, self.entrees)

    def chercher(self, direction):
        if not self.adjacent(self.pos, self.armoire_pos):
            raise ActionIllegale(f"CHERCHER : Pas adjacent a l'armoire")

        try:
            self.selecteur = appliquer(self.selecteur, direction, self.n_ligne, self.n_colonne)

        except ValueError as err:
            raise ActionIllegale(f"CHERCHER : {direction} : {err}")

        return Resultat()

    def prendre(self, objet):
        if not self.adjacent(self.pos, self.armoire_pos):
            raise ActionIllegale("PRENDRE : pas adjacent a l'armoire")

        if self.objet_porte is not None:
            raise ActionIllegale("PRENDRE : le robot transporte deja un objet")

        if self.casiers.get(self.selecteur) is None:
            raise ActionIllegale("PRENDRE : casier vide")

        if objet != self.casiers[self.selecteur]:
            raise ActionIllegale(f"PRENDRE {objet!r} : le casier contient "f"{self.casiers[self.selecteur]!r}")

        self.objet_porte = objet
        return Resultat()

    def donner(self, objet):
        cible = self.residents.get(self.resident_courant)

        if cible is None or not self.adjacent(self.pos, cible):
            raise ActionIllegale("DONNER : pas adjacent au resident concerne")

        if self.objet_porte is None or self.objet_porte != objet:
            raise ActionIllegale(f"DONNER {objet!r} : objet non transporte")

        self.objet_porte = None
        return Resultat()

    def attendre(self, _):
        return Resultat()


def preparer_monde(carte: dict, armoire: dict, dictionnaire: dict):
    r = {}
    for res in carte["residents"]:
        r[res["id"]] = tuple(res["position"])

    nr = {}
    for res in carte["residents"]:
        nr[res["id"]] = res["nom"]

    c = Connaissances(
        hauteur=carte["dimensions"]["hauteur"],
        largeur=carte["dimensions"]["largeur"],

        depart=tuple(carte["depart_robot"]),
        casier_depart=tuple(armoire["casier_depart"]),
        armoire=tuple(carte["armoire"]["position"]),
        dictionnaire=tuple(carte["dictionnaire"]["position"]),

        residents=r,
        noms_residents=nr,

        emotions=list(armoire["emotions"]),
        intensites=list(armoire["intensites"])
    )
    return Environnement(carte, armoire, dictionnaire), c
