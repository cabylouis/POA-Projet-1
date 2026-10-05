
from collections import *

from typing import Tuple, Iterable, Callable, Optional, List, Dict

Case = Tuple[int, int]

def voisin(actuelle: Case) -> List[Case]:
    x, y = actuelle
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

def plus_court_chemin(depart: Case, arrivees: Iterable[Case], est_traversable: Callable[[Case], bool]) -> Optional[List[Case]] :

    for a in arrivees:
        if depart == a:
            return [a]

    predecesseur : Dict[Case, Optional[Case]] = {depart: None}
    file = deque([depart])

    while file:
        courant = file.popleft()
        vsn = voisin(courant)

        for v in vsn:
            if v in predecesseur or not est_traversable(v):
                continue

            predecesseur[v] = courant

            if v in arrivees:
                return reconstruire(predecesseur, courant)

            file.appendleft(v)
    return None

def reconstruire(predecesseur: Dict[Case, Optional[Case]], fin: Case) -> List[Case]:
    chemin = [fin]
    while predecesseur[chemin[- 1] is not None]:
        chemin.append(predecesseur[chemin[- 1]])
    return chemin