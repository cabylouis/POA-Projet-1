import unittest

from roue import candidats, distance_roue
from selecteur import appliquer_deplacement, casiers_traverses, distance, plus_court_chemins

class TestSelecteur(unittest.TestCase):
    def test_bouclage_des_colonnes(self):
        self.assertEqual(appliquer_deplacement((1, 7), "E", 3, 8), (1, 0))
        self.assertEqual(appliquer_deplacement((1, 0), "O", 3, 8), (1, 7))

    def test_les_lignes_ne_bouclent_pas(self):
        with self.assertRaises(ValueError): appliquer_deplacement((0, 3), "N", 3, 8)
        with self.assertRaises(ValueError): appliquer_deplacement((2, 3), "S", 3, 8)

    def test_exemples_annexe_c3(self):
        self.assertEqual(distance((1, 0), (1, 4), 8), 4)
        self.assertEqual(distance((2, 7), (0, 1), 8), 4)
        self.assertEqual(distance((1, 0), (2, 6), 8), 3)

    def test_itineraire_par_le_bouclage(self):
        routes = plus_court_chemins((1, 0), (2, 6), 8)
        self.assertTrue(all(len(r) == 3 for r in routes))
        self.assertIn(["S", "O", "O"], routes)
        self.assertIn(["O", "O", "S"], routes)
        self.assertEqual(len(routes), 3)

    def test_deux_sens_equivalents_quand_a_vaut_4(self):
        routes = plus_court_chemins((1, 0), (1, 4), 8)
        self.assertIn(["E"] * 4, routes)
        self.assertIn(["O"] * 4, routes)

    def test_les_routes_ne_montrent_pas_les_memes_casiers(self):
        vert = casiers_traverses((1, 0), ["S", "O", "O"], 3, 8)
        hori = casiers_traverses((1, 0), ["O", "O", "S"], 3, 8)
        self.assertEqual(vert, [(2, 0), (2, 7), (2, 6)])
        self.assertEqual(hori, [(1, 7), (1, 6), (2, 6)])


class TestRepli(unittest.TestCase):
    """annexe C.5"""

    def test_distance_roue(self):
        self.assertEqual(distance_roue(0, 4, 8), 4)  # joie opposé à tristesse
        self.assertEqual(distance_roue(7, 0, 8), 1)  # anticipation similaire à joie

    def test_ordre_annexe_c5(self):
        liste = candidats(3, 2, 8, 3)  # surprise forte
        self.assertEqual([c.casier() for c in liste[:5]],[(2, 3), (1, 3), (0, 3), (2, 4), (2, 2)])
        self.assertEqual([c.repli for c in liste[:5]], ["aucun", "intensite", "intensite", "voisine_1", "voisine_1"])

    def test_quinze_candidats_jamais_de_distance_3_ou_4(self):
        for e in range(8):
            for i in range(3):
                liste = candidats(e, i, 8, 3)
                self.assertEqual(len(liste), 15)
                self.assertEqual(len({c.casier() for c in liste}), 15)
                self.assertTrue(all(c.distance <= 2 for c in liste))

    def test_casier_exact_en_premier(self):
        for e in range(8):
            for i in range(3):
                self.assertEqual(candidats(e, i, 8, 3)[0].casier(), (i, e))
                self.assertEqual(candidats(e, i, 8, 3)[0].repli, "aucun")

    def test_intensite_la_plus_faible_d_abord_a_ecart_egal(self):
        liste = candidats(4, 1, 8, 3)  # tristesse moyenne
        self.assertEqual([c.casier() for c in liste[:3]], [(1, 4), (0, 4), (2, 4)])

    def test_opposees_exclues(self):
        liste = candidats(0, 1, 8, 3)  # joie moyenne
        self.assertNotIn(4, {c.colonne for c in liste})
        self.assertNotIn(3, {c.colonne for c in liste})
        self.assertNotIn(5, {c.colonne for c in liste})


if __name__ == "__main__":
    unittest.main()
