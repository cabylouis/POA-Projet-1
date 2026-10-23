import unittest

from planification import plus_court_chemin

B3 = ["######",
      "#..#.#",
      "#.#..#",
      "#...##",
      "######"]

def libre(grille):
    return lambda c: (0 <= c[0] < len(grille) and 0 <= c[1] < len(grille[0])
                      and grille[c[0]][c[1]] == ".")

class TestPlanification(unittest.TestCase):
    def test_longueur_connue_annexe_b3(self):
        chemin = plus_court_chemin((1, 1), {(1, 4)}, libre(B3))
        self.assertEqual(len(chemin) - 1, 7)
        self.assertEqual(chemin[0], (1, 1))
        self.assertEqual(chemin[-1], (1, 4))

    def test_pas_de_chemin(self):
        g = ["#####", "#.#.#", "#####"]
        self.assertIsNone(plus_court_chemin((1, 1), {(1, 3)}, libre(g)))

    def test_depart_deja_cible(self):
        self.assertEqual(plus_court_chemin((1, 1), {(1, 1)}, libre(B3)), [(1, 1)])

    def test_plus_proche_de_plusieurs_cibles(self):
        g = ["#######", "#.....#", "#######"]
        chemin = plus_court_chemin((1, 3), {(1, 1), (1, 5), (1, 4)}, libre(g))
        self.assertEqual(chemin[-1], (1, 4))