from reconfort_io import normaliser
from typing import List, Dict, Tuple, Optionnal

def lire(message: str, entrees: List[dict]) -> Optionnal(Tuple(str, str)):
    index: Dict[str, Tuple(str, str)] = {};

    for entree in entrees:
        for forme in entree["formes"]:
            entree[forme] = (emotion["emotion"], intensite["intensite"]);

    msg = normaliser(message);

    for mot in message:
        if mot in index:
            return index[mot];

    return None;