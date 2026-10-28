from collections import deque
from typing import Iterable, Callable, Optional

Case = tuple[int, int]
DIRECTIONS = ("S", "N", "E", "O")


def voisin(case: Case, direction: str) -> Case:
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


def direction_entre(a: Case, b: Case) -> str:
    for d, dl, dc in DIRECTIONS:
        if (a[0] + dl, a[1] + dc) == b:
            return d
    raise ValueError(f"{a} et {b} cases non adjacentes")


def plus_court_chemin(depart: Case, arrivees: Iterable[Case], est_traversable: Callable[[Case], bool]) -> Optional[list[Case]]:
    for a in arrivees:
        if depart == a:
            return [a]

    predecesseur: dict[Case, Optional[Case]] = {depart: None}
    file = deque([depart])

    while file:
        courant = file.popleft()

        voisins = []
        for dir in DIRECTIONS:
            voisins.append(voisin(courant, dir))

        for v in voisins:
            if v in predecesseur or not est_traversable(v):
                continue

            predecesseur[v] = courant

            if v in arrivees:
                return reconstruire(predecesseur, v)

            file.append(v)
    return None


def reconstruire(predecesseur: dict[Case, Optional[Case]], fin: Case) -> list[Case]:
    chemin = [fin]
    while predecesseur[chemin[- 1]] is not None:
        chemin.append(predecesseur[chemin[- 1]])
    chemin.reverse()
    return chemin
