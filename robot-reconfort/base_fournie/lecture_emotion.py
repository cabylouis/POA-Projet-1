from reconfort_io import normaliser
from typing import Optional

def lire(message: str, entrees: list[dict]) -> Optional[tuple[str, str]]:
    index: dict[str, tuple[str, str]] = {}

    for entree in entrees:
        for forme in entree["formes"]:
            index[forme] = (entree["emotion"], entree["intensite"])

    msg = normaliser(message)

    for mot in msg:
        if mot in index:
            return index[mot]

    return None;