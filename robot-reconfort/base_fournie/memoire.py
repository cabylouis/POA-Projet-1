from perception import (ARMOIRE, DICTIONNAIRE, LIBRE, MUR, RESIDENT, Connaissances, Perception)
from planification import voisin, voisins
from selecteur import Casier, appliquer

Case = Tuple[int, int]

class CarteMentale:
    def __init__(self, k: Connaissances) -> None:
        self.hauteur, self.largeur = k.hauteur, k.largeur
        self._cases: Dict[Case, str] = {}

        # Règle 3.1 : le bord est toujours un mur.
        for l in range(self.hauteur):
            for c in range(self.largeur):
                if l in (0, self.hauteur - 1) or c in (0, self.largeur - 1):
                    self._cases[(l, c)] = MUR

        self._cases[k.depart] = LIBRE
        self._cases[k.armoire] = ARMOIRE
        self._cases[k.dictionnaire] = DICTIONNAIRE
        for pos in k.residents.values():
            self._cases[pos] = RESIDENT

    def dans_les_bornes(self, case: Case) -> bool:
        return 0 <= case[0] < self.hauteur and 0 <= case[1] < self.largeur

    def type_connu(self, case: Case) -> Optional[str]:
        return self._cases.get(case)

    def observer(self, case: Case, type_case: str) -> None:
        if self.dans_les_bornes(case):
            self._cases[case] = type_case

    def traversable_optimiste(self, case: Case) -> bool:
        return self.dans_les_bornes(case) and self._cases.get(case) in (None, LIBRE)

    def libre_connue(self, case: Case) -> bool:
        return self._cases.get(case) == LIBRE

    def voisines(self, case: Case) -> Iterator[Case]:
        v = voisins(case)
        if self.dans_les_bornes(v):
            yield v

    def cases_d_acces(self, objet: Case, certaines: bool = False) -> set:
        test = self.libre_connue if certaines else self.traversable_optimiste
        return {v for v in self.voisines(objet) if test(v)}

    def inconnues(self) -> int:
        return self.hauteur * self.largeur - len(self._cases)


class MemoireArmoire:
    """Casiers déjà vus : casier -> objet (None = vu et vide)."""

    def __init__(self) -> None:
        self._vus: Dict[Casier, Optional[str]] = {}

    def observer(self, casier: Casier, objet: Optional[str]) -> None:
        self._vus[casier] = objet

    def est_vu(self, casier: Casier) -> bool:
        return casier in self._vus

    def objet(self, casier: Casier) -> Optional[str]:
        return self._vus.get(casier)


class Memoire:
    """Intégralité de la mémoire du robot à chaque instant."""

    def __init__(self, k: Connaissances) -> None:
        self.k = k
        self.carte = CarteMentale(k)
        self.armoire = MemoireArmoire()
        self.position: Case = k.depart
        self.selecteur: Casier = k.casier_depart
        self.objet_porte: Optional[str] = None
        self.n_lignes = len(k.intensites)
        self.n_colonnes = len(k.emotions)

    def integrer(self, p: Perception) -> None:
        for direction, type_case in p.voisins.items():
            self.carte.observer(voisin(self.position, direction), type_case)
        if p.devant_armoire:
            self.armoire.observer(self.selecteur, p.contenu_casier)

    def apres_action(self, action: str, argument: Optional[str], ok: bool) -> None:
        if not ok:
            return
        if action == "AVANCER":
            self.position = voisin(self.position, argument)
        elif action == "CHERCHER":
            self.selecteur = appliquer(self.selecteur, argument, self.n_lignes, self.n_colonnes)
        elif action == "PRENDRE":
            self.objet_porte = argument
        elif action == "DONNER":
            self.objet_porte = None
