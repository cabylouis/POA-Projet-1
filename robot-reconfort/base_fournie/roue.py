from typing import NamedTuple

RAYON_MAX = 2

class Candidat(NamedTuple):
    """ Représente un casier candidat sur la roue des émotions. """

    ligne: int
    colonne: int
    distance: int
    repli: str

    def casier(self) -> tuple[int, int]:
        """ Retourne la position du casier sous forme (ligne, colonne). """

        return self.ligne, self.colonne

def repli(distance: int, meme_intensite: bool) -> str:
    """ Détermine la stratégie de repli selon la distance et l'intensité. """

    if distance == 0:
        return "aucun" if meme_intensite else "intensite"

    return f"voisine_{distance}"

def distance_roue(emotion_1: int, emotion_2: int, n_emotions: int) -> int:
    """ Calcule la distance minimale entre deux positions sur une roue circulaire. """

    ecart = (emotion_1 - emotion_2) % n_emotions
    return min(ecart, n_emotions - ecart)

def candidats(emotion: int, intensite: int, n_emotions: int, n_intensites: int, rayon: int = RAYON_MAX) -> list[Candidat]:
    """ Génère les casiers candidats dans un rayon donné autour d'une émotion.
    Trie les candidats par distance émotionnelle, écart d'intensité,
    le niveau d'intensité, puis sens horaire avant antihoraire.
    """

    cles = []

    for emotion_candidate in range(n_emotions):
        distance = distance_roue(emotion, emotion_candidate, n_emotions)

        if distance > rayon:
            continue

        horaire = (emotion_candidate - emotion) % n_emotions == distance

        for intensite_candidate in range(n_intensites):
            cle = (distance, abs(intensite_candidate - intensite), intensite_candidate, 0 if horaire else 1)
            cles.append((cle, Candidat(intensite_candidate, emotion_candidate, distance, repli(distance, intensite_candidate == intensite))))

    cles.sort(key=lambda paire: paire[0])

    return [c for _, c in cles]