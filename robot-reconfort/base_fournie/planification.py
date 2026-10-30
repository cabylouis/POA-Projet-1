from collections.abc import Callable
from collections import deque

Case = tuple[int, int]
DIRECTIONS = ("S", "N", "E", "O")


def voisin(case: Case, direction: str) -> Case:
    """ Retourne la case adjacente dans la direction indiquée. """

    x, y = case

    if direction == "S":
        x += 1
    elif direction == "N":
        x -= 1
    elif direction == "E":
        y += 1
    elif direction == "O":
        y -= 1
    else:
        raise ValueError(f"direction inconnue: {direction}")

    return x, y

def voisins(case: Case) -> list[Case]:
    """ Retourne les quatre cases voisines d'une case donnée."""

    voisins_case : list[Case] = []

    for direction in DIRECTIONS:
        voisins_case.append(voisin(case, direction))

    return voisins_case

def direction_entre(a: Case, b: Case) -> str:
    """ Retourne la direction permettant d'aller de a vers b. """

    x, y = b[0] - a[0], b[1] - a[1]

    if abs(x) + abs(y) != 1:
        raise Exception(f"Cases non adjacentes : {a}, {b}")

    if x == 1:
        return DIRECTIONS[0]
    elif x == -1:
        return DIRECTIONS[1]
    elif y == 1:
        return DIRECTIONS[2]
    else:
        return DIRECTIONS[3]

def plus_court_chemin(depart: Case, arrivees: list[Case], est_traversable: Callable[[Case], bool]) -> list[Case] | None:
    """ Calcule un plus court chemin vers l'une des cases d'arrivée.
    Utilise un parcours en largeur en évitant les cases
    déjà visitées et celles qui ne sont pas traversables.

    Voir Annexe B.4
    """

    for a in arrivees:
        if depart == a:
            return [a]

    predecesseur: dict[Case, Case | None] = {depart: None}
    file = deque([depart])

    while file:
        courant = file.popleft()

        voisins_case = voisins(courant)

        for v in voisins_case:
            if v in predecesseur or not est_traversable(v):
                continue

            predecesseur[v] = courant

            if v in arrivees:
                return reconstruire(predecesseur, v)

            file.append(v)
    return None


def reconstruire(predecesseur: dict[Case, Case | None], fin: Case) -> list[Case]:
    """ Reconstruit le chemin jusqu'à la case finale à partir des prédécesseurs. """

    chemin = [fin]

    while predecesseur[chemin[- 1]] is not None:
        chemin.append(predecesseur[chemin[- 1]])

    chemin.reverse()
    return chemin
