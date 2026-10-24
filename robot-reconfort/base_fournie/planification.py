from collections import deque
from typing import Tuple, Iterable, Callable, Optional, List, Dict

Case = Tuple[int, int]

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
    return (x, y)

def voisins(case: Case) -> List[Case]:
    x, y = case
    # Ordre fixe => parcours déterministe
    # Sud > Nord > Est > Ouest
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

def plus_court_chemin(depart: Case, arrivees: Iterable[Case], est_traversable: Callable[[Case], bool]) -> Optional[List[Case]]:

    for a in arrivees:
        if depart == a:
            return [a]

    predecesseur : Dict[Case, Optional[Case]] = {depart: None}
    file = deque([depart])

    while file:
        courant = file.popleft()
        voisins = voisins(courant)

        for v in (voisins):
            if v in predecesseur or not est_traversable(v):
                continue

            predecesseur[v] = courant

            if v in arrivees:
                return reconstruire(predecesseur, v)

            file.append(v)
    return None

def reconstruire(predecesseur: Dict[Case, Optional[Case]], fin: Case) -> List[Case]:
    chemin = [fin]
    while predecesseur[chemin[- 1]] is not None:
        chemin.append(predecesseur[chemin[- 1]])
    chemin.reverse()
    return chemin