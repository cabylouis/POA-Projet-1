from itertools import combinations


Casier = tuple[int, int]

def appliquer_deplacement(casier: Casier, direction: str, n_lignes: int, n_colonnes: int) -> Casier:
    """ Applique un déplacement depuis un casier et retourne la nouvelle position. """

    ligne, colonne = casier

    if direction == "N":
        ligne -= 1
    elif direction == "S":
        ligne += 1
    elif direction == "E":
        colonne = (colonne + 1) % n_colonnes
    elif direction == "O":
        colonne = (colonne - 1) % n_colonnes
    else:
        raise ValueError(f"direction inconnue : {direction}")

    if not 0 <= ligne < n_lignes:
        raise ValueError("déplacement vertical hors de l'armoire")

    return ligne, colonne

def mouv_horizontaux(colonne_1: int, colonne_2: int, n_emotions: int) -> list[list[str]]:
    """ Retourne les déplacements horizontaux les plus courts entre deux colonnes.
    Renvoie les deux possibilités si les déplacements Est et Ouest
    ont la même longueur.
    """

    distance_est = (colonne_2 - colonne_1) % n_emotions

    if distance_est == 0:
        return [[]]

    options = []
    if distance_est <= n_emotions - distance_est:
        options.append(["E"] * distance_est)

    if n_emotions - distance_est <= distance_est:
        options.append(["O"] * (n_emotions - distance_est))

    return options

def distance(casier_1: Casier, casier_2: Casier, n_colonnes: int) -> int:
    """ Calcule la distance minimale entre deux casiers.
    Le résultat est le déplacement vertical plus le déplacement
    horizontal le plus court sur l'armoire circulaire.
    """

    ecart_horizontal = (casier_2[1] - casier_1[1]) % n_colonnes

    return abs(casier_2[0] - casier_1[0]) + min(ecart_horizontal, n_colonnes - ecart_horizontal)

def plus_court_chemins(depart: Casier, arrivee: Casier, n_colonnes: int) -> list[list[str]]:
    """ Génère tous les plus courts chemins entre deux casiers. """

    ecart_vertical = arrivee[0] - depart[0]
    mouvements_verticaux = "S" if ecart_vertical > 0 else "N"
    nb_mouvements_verticaux = abs(ecart_vertical)

    resultats: list[list[str]] = []

    for mouvements_horizontaux in mouv_horizontaux(depart[1], arrivee[1], n_colonnes):
        longueur_totale = nb_mouvements_verticaux + len(mouvements_horizontaux)

        for positions_verticales in combinations(range(longueur_totale), len(mouvements_verticaux)):
            chemin = []

            for indice in range(longueur_totale):
                if indice in positions_verticales:
                    chemin.append(mouvements_verticaux)
                else:
                    chemin.append(mouvements_horizontaux[0])

            if chemin not in resultats:
                resultats.append(chemin)

    return resultats

def casiers_traverses(depart: Casier, mouvements: list[str], n_lignes: int, n_colonnes: int) -> list[Casier]:
    """ Retourne les casiers traversés en appliquant une suite de mouvements.
    La position de départ n'est pas incluse dans la liste retournée.
    """

    courant, vus = depart, []

    for mouv in mouvements:
        courant = appliquer_deplacement(courant, mouv, n_lignes, n_colonnes)
        vus.append(courant)

    return vus