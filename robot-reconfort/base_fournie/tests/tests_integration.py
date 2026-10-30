import random
import unittest

from tests.utils import (ARMOIRE, CARTE_01, DICO, RACINE, SCENARIO_01,
                          armoire_avec, carte_depuis_grille, copie, scenario)
from tests.verificateur import verifier
from agent import executer_scenario

MINI = ["#########",
        "#R..A.D.#",
        "#.......#",
        "#P.....P#",
        "#########"]


def lancer(carte, sc, armoire=ARMOIRE):
    trace = executer_scenario(carte, sc, DICO, armoire, ["test"])
    return trace.en_dictionnaire()


class TestScenariosFournis(unittest.TestCase):
    def test_appartement_01_trace_conforme(self):
        t = lancer(CARTE_01, SCENARIO_01)

        self.assertEqual(verifier(CARTE_01, ARMOIRE, DICO, SCENARIO_01, t), [])
        self.assertEqual(t["resume"]["reussies"], 4)
        self.assertEqual(
            [l["objet"] for l in t["livraisons"]],
            ["couverture", "veilleuse", "balle antistress",
            "photo de famille"]
        )

    def test_le_robot_se_cogne_au_mur_et_replanifie(self):
        t = lancer(CARTE_01, SCENARIO_01)
        vus = [p for p in t["pas"] if p["position"] == [6, 6] and p["perception"]["E"] == "mur"]

        self.assertTrue(vus)
        self.assertTrue(any("replanification" in (p["commentaire"] or "") for p in t["pas"]))


class TestFouille(unittest.TestCase):
    def test_colonne_surprise_vide_repli_voisine(self):
        # annexe C.5 : surprise/forte, colonne 3 vide
        carte = carte_depuis_grille(MINI)
        sc = scenario([("R1", "Je suis sidéré, la télévision s'est allumée.")])
        t = lancer(carte, sc)
        l = t["livraisons"][0]

        self.assertTrue(l["succes"])
        self.assertEqual((l["casier_choisi"], l["repli"], l["objet"]),([2, 4], "voisine_1", "telephone"))
        self.assertEqual(verifier(carte, ARMOIRE, DICO, sc, t), [])

    def test_ordre_prime_sur_ce_qu_on_croise(self):
        carte = carte_depuis_grille(MINI)
        sc = scenario([("R1", "Je suis sidéré.")])
        t = lancer(carte, sc)

        # [2,2] peur/forte vu mais pas pris
        croise = [p for p in t["pas"] if p["casier"] == [2, 2] and p["contenu_casier"]]
        self.assertTrue(croise)
        self.assertEqual(t["livraisons"][0]["casier_choisi"], [2, 4])

    def test_repli_intensite(self):
        carte = carte_depuis_grille(MINI)
        a = armoire_avec(vides={(1, 4)})    # tristesse/moyenne vide
        sc = scenario([("R1", "Je me sens triste.")])
        t = lancer(carte, sc, a)
        l = t["livraisons"][0]

        self.assertEqual((l["casier_choisi"], l["repli"]), ([0, 4], "intensite"))
        self.assertEqual(verifier(carte, a, DICO, sc, t), [])

    def test_colonne_entiere_vide_repli_voisine_2(self):
        carte = carte_depuis_grille(MINI)
        # 3,4,5 vides -> joie ou colere
        vides = {(l, c) for l in range(3) for c in (3, 4, 5)}
        a = armoire_avec(vides=vides)
        sc = scenario([("R1", "Je me sens triste.")])
        t = lancer(carte, sc, a)
        l = t["livraisons"][0]

        self.assertTrue(l["succes"])
        self.assertEqual(l["repli"], "voisine_2")

        # à distance 2 de tristesse 4 : colère 6 (sens horaire) avant peur 2
        self.assertEqual(l["casier_choisi"], [1, 6])
        self.assertEqual(verifier(carte, a, DICO, sc, t), [])

    def test_aucun_casier_garni_a_distance_2(self):
        carte = carte_depuis_grille(MINI)
        vides = {(l, c) for l in range(3) for c in (2, 3, 4, 5, 6)}
        a = armoire_avec(vides=vides)
        sc = scenario([("R1", "Je me sens triste."), ("R2", "Je suis heureux.")])
        t = lancer(carte, sc, a)
        l = t["livraisons"][0]

        self.assertFalse(l["succes"])
        self.assertEqual(l["motif_echec"], "armoire vide")
        self.assertEqual(l["emotion"], "tristesse")
        self.assertTrue(t["livraisons"][1]["succes"])
        self.assertEqual(verifier(carte, a, DICO, sc, t), [])


class TestEchecs(unittest.TestCase):
    def test_emotion_indeterminee_puis_suite(self):
        carte = carte_depuis_grille(MINI)
        sc = scenario([("R1", "Bonjour, il fait beau."), ("R2", "Je suis heureux.")])
        t = lancer(carte, sc)

        self.assertFalse(t["livraisons"][0]["succes"])
        self.assertEqual(t["livraisons"][0]["motif_echec"], "emotion indeterminee")
        self.assertTrue(t["livraisons"][1]["succes"])
        self.assertEqual(verifier(carte, ARMOIRE, DICO, sc, t), [])

    def test_resident_mure_sur_grille_minuscule(self):
        grille = ["#########",
                  "#R..A.D.#",
                  "#.......#",
                  "#..###..#",
                  "#..#P#..#",
                  "#..###..#",
                  "#########"]
        carte = carte_depuis_grille(grille)
        sc = scenario([("R1", "Je suis heureux."), ("R1", "Je suis triste.")])
        t = lancer(carte, sc)

        for l in t["livraisons"]:
            self.assertFalse(l["succes"])
            self.assertEqual(l["motif_echec"], "resident inaccessible")
            self.assertIsNotNone(l["emotion"])    # dictionnaire lu

        # Le robot n'a jamais pris d'objet qu'il ne pouvait pas livrer
        self.assertFalse(any(p["action"] == "PRENDRE" for p in t["pas"]))
        self.assertEqual(verifier(carte, ARMOIRE, DICO, sc, t), [])

    def test_resident_mure_n_empeche_pas_les_autres_demandes(self):
        grille = ["#########",
                  "#R..A.D.#",
                  "#.......#",
                  "#.P.###.#",
                  "#...#P#.#",
                  "#..P###.#",
                  "#########"]
        carte = carte_depuis_grille(grille)
        sc = scenario([("R2", "Je suis heureux."), ("R1", "Je suis heureux."), ("R3", "Je suis triste.")])
        t = lancer(carte, sc)
        etats = [(l["succes"], l["motif_echec"]) for l in t["livraisons"]]

        self.assertEqual(etats[0], (False, "resident inaccessible"))
        self.assertTrue(t["livraisons"][1]["succes"])
        self.assertTrue(t["livraisons"][2]["succes"])
        self.assertEqual(verifier(carte, ARMOIRE, DICO, sc, t), [])


def carte_aleatoire(rng, h, l):
    """Grille aléatoire valide ; les résidents peuvent être enmurés"""
    g = [["#"] * l for _ in range(h)]
    for i in range(1, h - 1):
        for j in range(1, l - 1):
            g[i][j] = "#" if rng.random() < 0.25 else "."

    libres = [(i, j) for i in range(1, h - 1) for j in range(1, l - 1)]
    rng.shuffle(libres)

    for sym, n in (("R", 1), ("A", 1), ("D", 1), ("P", 3)):
        for _ in range(n):
            i, j = libres.pop()
            g[i][j] = sym

    return carte_depuis_grille(["".join(r) for r in g], nom="alea")


class TestAleatoire(unittest.TestCase):
    """Cartes jamais vues"""

    def test_cent_cartes_aleatoires(self):
        rng = random.Random(2024)
        messages = [
            "Je suis heureux.", "Je suis sidéré.", "Je me sens seule.",
            "Quelle terreur !", "Rien de special.", "Ça m'agace."
        ]
        inaccessibles = 0
        for n in range(100):
            carte = carte_aleatoire(rng, rng.randint(6, 16), rng.randint(6, 22))
            vides = {(rng.randrange(3), rng.randrange(8)) for _ in range(rng.randint(0, 12))}
            a = armoire_avec(vides=vides)
            sc = scenario([(f"R{rng.randint(1, 3)}", rng.choice(messages)) for _ in range(5)], carte="alea")
            t = lancer(carte, sc, a)

            self.assertEqual(verifier(carte, a, DICO, sc, t), [], f"carte {n}")
            inaccessibles += sum(l["motif_echec"] == "resident inaccessible" for l in t["livraisons"])

        self.assertGreater(inaccessibles, 0)


class TestSeparation(unittest.TestCase):
    """L'agent ne doit jamais lire la grille ni le contenu des casiers"""

    def test_modules_de_l_agent_ne_citent_pas_la_grille(self):
        for nom in ("decision", "memoire", "actions", "perception", "roue",
                    "selecteur", "planification", "lecture_emotion",
                    "affichage", "agent"):
            source = (RACINE / f"{nom}.py").read_text("utf-8")
            self.assertNotIn('["grille"]', source, nom)
            self.assertNotIn("['grille']", source, nom)
            self.assertNotIn('["objet"]', source, nom)
            self.assertNotIn('"casiers"', source, nom)


if __name__ == "__main__":
    unittest.main()
