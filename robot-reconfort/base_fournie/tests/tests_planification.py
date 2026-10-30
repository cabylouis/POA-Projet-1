import unittest

from memoire import CarteMentale
from perception import Connaissances
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

    def test_chemin_legal(self):
        chemin = plus_court_chemin((1, 1), {(1, 4)}, libre(B3))
        for a, b in zip(chemin, chemin[1:]):
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)
            self.assertTrue(libre(B3)(b))

    def test_pas_de_chemin(self):
        g = ["#####", "#.#.#", "#####"]
        self.assertIsNone(plus_court_chemin((1, 1), {(1, 3)}, libre(g)))

    def test_depart_deja_cible(self):
        self.assertEqual(plus_court_chemin((1, 1), {(1, 1)}, libre(B3)), [(1, 1)])

    def test_plus_proche_de_plusieurs_cibles(self):
        g = ["#######", "#.....#", "#######"]
        chemin = plus_court_chemin((1, 3), {(1, 1), (1, 5), (1, 4)}, libre(g))
        self.assertEqual(chemin[-1], (1, 4))


class TestReplanification(unittest.TestCase):
    """Un mur decouvert en route change le trajet (hypothese optimiste)."""

    def setUp(self):
        self.k = Connaissances(
            hauteur=5, largeur=7, depart=(2, 1), armoire=(1, 1),
            dictionnaire=(3, 1), residents={}, noms_residents={},
            emotions=["a"], intensites=["b"], casier_depart=(0, 0)
        )
        self.carte = CarteMentale(self.k)

    def test_chemin_optimiste_droit_puis_contournement(self):
        cible = {(2, 5)}
        avant = plus_court_chemin((2, 1), cible, self.carte.traversable_optimiste)
        self.assertEqual(len(avant) - 1, 4)    # tout droit, sans mur connu
        self.assertIn((2, 3), avant)
        self.carte.observer((2, 3), "mur")    # mur découvert en route
        apres = plus_court_chemin((2, 2), cible, self.carte.traversable_optimiste)
        self.assertNotIn((2, 3), apres)    # le trajet change
        self.assertGreater(len(apres) - 1, 3)    # et s'allonge (3 pas avant)

    def test_preuve_d_inaccessibilite_sur_carte_mentale(self):
        # un resident dont les 4 voisines sont des murs connus : aucun acces
        for c in [(1, 4), (3, 4), (2, 3), (2, 5)]:
            self.carte.observer(c, "mur")
        self.assertEqual(self.carte.cases_d_acces((2, 4)), [])


if __name__ == "__main__":
    unittest.main()