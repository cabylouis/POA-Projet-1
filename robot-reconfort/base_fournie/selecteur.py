from itertools import combinations
from typing import List, Tuple

Casier = Tuple[int, int]

def appliquer(casier: Casier, direction: str, n_lignes: int, n_colonnes: int) -> Casier:
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
    return (ligne, colonne)

def mouv_horizontaux(c: int, c2: int, n: int) -> List[List[str]]:
    a = (c2 - c) % n
    if a == 0:
        return [[]]
    options = []
    if a <= n - a:
        options.append(["E"] * a)
    if n - a <= a:
        options.append(["O"] * (n - a))
    return options

def distance(a: Casier, b: Casier, n_colonnes: int) -> int:
    ecart = (b[1] - a[1]) % n_colonnes
    return abs(b[0] - a[0]) + min(ecart, n_colonnes - ecart)

def plus_court_chemins(depart: Casier, arrivee: Casier, n_colonnes: int) -> List[List[str]]:
    dist_v = arrivee[0] - depart[0]
    vertical = ["S" if dist_v > 0 else "N"] * abs(dist_v)

    resultats: List[List[str]] = []
    for horizontal in mouv_horizontaux(depart[1], arrivee[1], n_colonnes):
        total = len(vertical) + len(horizontal)

        for positions in combinations(range(total), len(vertical)):
            marques = set(positions)
            v, h = iter(vertical), iter(horizontal)
            chemin = [next(v) if k in marques else next(h) for k in range(total)]

            if chemin not in resultats:
                resultats.append(chemin)

    return resultats

def casiers_traverses(depart: Casier, mouvements: List[str], n_lignes: int, n_colonnes: int) -> List[Casier]:
    courant, vus = depart, []
    for m in mouvements:
        courant = appliquer(courant, m, n_lignes, n_colonnes)
        vus.append(courant)
    return vus