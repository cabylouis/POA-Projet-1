from typing import NamedTuple, Tuple

RAYON_MAX = 2

class Candidat(NamedTuple):
    ligne: int
    colonne: int
    distance: int
    repli: str

def repli(distance: int, meme_intensite: bool) -> str:
    if distance == 0:
        return "aucun" if meme_intensite else "intensite"
    return f"voisine_{distance}"

def distance_roue(i: int, j: int, n: int) -> int:
    ecart = (i - j) % n
    return min(ecart, n - ecart)

def candidats(emotion: int, intensite: int, n_emotions: int, n_intensites: int, rayon: int = RAYON_MAX) -> List[Candidat]:

    cles = []

    for colonne in range(n_emotions):
        d = distance_roue(emotion, colonne, n_emotions)

        if d > rayon:
            continue

        horaire = (colonne - emotion) % n_emotions == d

        for ligne in range(n_intensites):
            cle = (d, abs(ligne - intensite), ligne, 0 if horaire else 1)
            cles.append((cle, Candidat(ligne, colonne, d, repli(d, ligne == intensite))))

    cles.sort(key=lambda paire: paire[0])

    return [c for _, c in cles]