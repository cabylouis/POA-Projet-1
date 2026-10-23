from reconfort_io import normaliser
from typing import List, Dict, Tuple, Optional

def lire(message: str, entrees: List[dict]) -> Optional(Tuple(str, str)):
    index: Dict[str, Tuple(str, str)] = {}

    for entree in entrees:
        for forme in entree["formes"]:
            index[forme] = (entree["emotion"], entree["intensite"])

    msg = normaliser(message)

    for mot in msg:
        if mot in index:
            return index[mot]

    return None;