import unittest
import json

from pathlib import Path
from lecture_emotion import lire

RACINE = Path(__file__).resolve().parent.parent
DICT = json.loads((RACINE / "donnees" / "dictionnaire.json").read_text("utf-8"))

class TestLecture(unittest.TestCase):
    def lire(self, msg):
        return lire(msg, DICT["entrees"])

    def test_une_phrase_par_emotion(self):
        cas = {
            "Je suis tellement heureux !": "joie",
            "J'ai confiance en toi.": "confiance",
            "Je suis terrifiée.": "peur",
            "Quelle surprise, je suis sidéré.": "surprise",
            "Je me sens triste.": "tristesse",
            "Je suis dégoûtée par ce repas.": "degout",
            "Ça m'agace depuis hier.": "colere",
            "J'attends ma fille, j'ai hâte.": "anticipation",
        }
        for message, attendu in cas.items():
            lu = self.lire(message)
            self.assertIsNotNone(lu, message)
            self.assertEqual(lu[0], attendu, message)

    def test_exemple_enonce(self):
        self.assertEqual(self.lire("Je suis sidéré, la télévision s'est allumée toute seule."), ("surprise", "forte"));

    def test_ordre_inverse(self):
        self.assertEqual(self.lire("Toute seule, je suis sidérée.")[0], "tristesse");

    def test_exemples_scenario_01(self):
        self.assertEqual(self.lire("Je me sens tellement seule ce soir, personne n'est passé."), ("tristesse", "moyenne"));

    def test_aucun_reconnu(self):
        self.assertIsNone(self.lire("Bonjour, il fait beau aujourd'hui."))
        self.assertIsNone(self.lire(""))
        self.assertIsNone(self.lire("hrtyrjkdfhertk fgdjdhgfd ysyhest"))


if __name__ == "__main__":
    unittest.main()
