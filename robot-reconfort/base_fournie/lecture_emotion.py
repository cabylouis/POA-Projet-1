from reconfort_io import normaliser

def lire(message: str, entrees: list[dict]) -> tuple[str, str] | None:
    """ Identifie l'émotion et son intensité à partir d'un message
    en recherchant les mots associés dans le dictionnaire émotionnel.
    """

    index: dict[str, tuple[str, str]] = {}

    for entree in entrees:
        for forme in entree["formes"]:
            index[forme] = (entree["emotion"], entree["intensite"])

    msg = normaliser(message)

    for mot in msg:
        if mot in index:
            return index[mot]

    return None