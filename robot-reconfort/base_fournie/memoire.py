from perception import (ARMOIRE, DICTIONNAIRE, LIBRE, MUR, RESIDENT, Connaissances, Perception)
from planification import voisin, DIRECTIONS
from selecteur import Casier, appliquer_deplacement

Case = tuple[int, int]

class CarteMentale:
    """ Représentation connue du monde par le robot. """

    def __init__(self, connaissances: Connaissances) -> None:
        """ Initialise la carte à partir des connaissances initiales.
        Les cases du bord sont considérées comme des murs.
        """

        self.hauteur, self.largeur = connaissances.hauteur, connaissances.largeur
        self.cases: dict[Case, str] = {}

        # Règle 3.1 : le bord est toujours un mur.
        for ligne in range(self.hauteur):
            for colonne in range(self.largeur):
                if ligne in (0, self.hauteur - 1) or colonne in (0, self.largeur - 1):
                    self.cases[(ligne, colonne)] = MUR

        self.cases[connaissances.depart] = LIBRE
        self.cases[connaissances.armoire] = ARMOIRE
        self.cases[connaissances.dictionnaire] = DICTIONNAIRE

        for position_resident in connaissances.residents.values():
            self.cases[position_resident] = RESIDENT

    def dans_les_bornes(self, case: Case) -> bool:
        """ Indique si une case appartient aux limites de la carte. """

        return 0 <= case[0] < self.hauteur and 0 <= case[1] < self.largeur

    def type_connu(self, case: Case) -> str | None:
        """ Retourne le type connu d'une case, ou None si inconnu. """

        return self.cases.get(case)

    def observer(self, case: Case, type_case: str) -> None:
        """ Enregistre le type observé d'une case si elle est dans la carte. """

        if self.dans_les_bornes(case):
            self.cases[case] = type_case

    def traversable_optimiste(self, case: Case) -> bool:
        """ Indique si une case est supposée traversable. """

        return self.dans_les_bornes(case) and self.cases.get(case) in (None, LIBRE)

    def libre_connue(self, case: Case) -> bool:
        """ Indique si une case est connue comme étant libre. """

        return self.cases.get(case) == LIBRE

    def voisines(self, case: Case) -> list[Case]:
        """Retourne les cases voisines situées dans les limites de la carte."""

        resultat = []

        for direction in DIRECTIONS:
            case_voisine = voisin(case, direction)

            if self.dans_les_bornes(case_voisine):
                resultat.append(case_voisine)

        return resultat

    def cases_d_acces(self, objet: Case, certaines: bool = False) -> list[Case]:
        """ Retourne les cases d'accès possibles à un objet.
        Si certaines vaut True, seules les cases libres connues sont retenues.
        Sinon, les cases inconnues sont également considérées comme traversables.
        """

        est_traversable = self.libre_connue if certaines else self.traversable_optimiste
        return [case_voisine for case_voisine in self.voisines(objet) if est_traversable(case_voisine)]

    def inconnues(self) -> int:
        """ Retourne le nombre de cases dont le type est inconnu. """

        return self.hauteur * self.largeur - len(self.cases)


class MemoireArmoire:
    """ Mémorise les casiers observés et leur contenu. """

    def __init__(self) -> None:
        """ Initialise la mémoire des casiers. """

        self.vus: dict[Casier, str | None] = {}

    def observer(self, casier: Casier, contenu: str | None) -> None:
        """ Enregistre le contenu observé d'un casier. """

        self.vus[casier] = contenu

    def est_vu(self, casier: Casier) -> bool:
        """ Indique si un casier a déjà été observé. """

        return casier in self.vus

    def objet(self, casier: Casier) -> str | None:
        """ Retourne le contenu mémorisé d'un casier, ou None. """

        return self.vus.get(casier)


class Memoire:
    """ Intégralité de la mémoire du robot à chaque instant. """

    def __init__(self, k: Connaissances) -> None:
        """ Initialise la mémoire à partir des connaissances initiales. """

        self.k = k
        self.carte = CarteMentale(k)
        self.armoire = MemoireArmoire()
        self.position: Case = k.depart
        self.selecteur: Casier = k.casier_depart
        self.objet_porte: str | None = None
        self.n_lignes = len(k.intensites)
        self.n_colonnes = len(k.emotions)

    def integrer(self, perception: Perception) -> None:
        """ Intègre les nouvelles perceptions à la mémoire. """

        for direction, type_case in perception.voisins.items():
            self.carte.observer(voisin(self.position, direction), type_case)

        if perception.devant_armoire:
            self.armoire.observer(self.selecteur, perception.contenu_casier)

    def apres_action(self, nom_action: str, argument_action: str | None, action_reussie: bool) -> None:
        """ Met à jour l'état mémorisé après une action réussie. """

        if not action_reussie:
            return

        if nom_action == "AVANCER":
            if argument_action is not None:
                self.position = voisin(self.position, argument_action)
        elif nom_action == "CHERCHER":
            if argument_action is not None:
                self.selecteur = appliquer_deplacement(self.selecteur, argument_action, self.n_lignes, self.n_colonnes)
        elif nom_action == "PRENDRE":
            self.objet_porte = argument_action
        elif nom_action == "DONNER":
            self.objet_porte = None
