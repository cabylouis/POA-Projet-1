"""Un fichier cassé par catégorie (5.6).

Chaque cas lance le vrai programme (4 arguments) et vérifie les trois choses :
code de retour non nul, message lisible sur stderr, aucun fichier de trace.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.utils import (ARMOIRE, CARTE_01, DICO, RACINE, SCENARIO_01, copie)


class TestAgent:
    """Un dossier temporaire avec 4 fichiers valides à âbimer."""

    def __init__(self, dossier: Path):
        self.d = dossier
        self.carte = copie(CARTE_01)
        self.scenario = copie(SCENARIO_01)
        self.dico = copie(DICO)
        self.armoire = copie(ARMOIRE)
        self.brut = {}

    def ecrire(self):
        (self.d / "donnees").mkdir(exist_ok=True)
        fichiers = {
            "carte.json": self.carte,
            "scenario.json": self.scenario,
            "donnees/dictionnaire.json": self.dico,
            "donnees/armoire_standard.json": self.armoire
        }
        for nom, contenu in fichiers.items():
            (self.d / nom).write_text(json.dumps(contenu), encoding="utf-8")
        for nom, octets in self.brut.items():
            (self.d / nom).write_bytes(octets)

    def lancer(self, *, supprimer=(), arguments=None):
        self.ecrire()
        for nom in supprimer:
            (self.d / nom).unlink()
        trace = self.d / "sortie" / "trace.json"
        args = arguments or [
            str(self.d / "carte.json"),
            str(self.d / "scenario.json"),
            str(self.d / "donnees"), str(trace)
        ]
        r = subprocess.run(
            [sys.executable, str(RACINE / "agent.py"), *args],
            capture_output=True,
            text=True, timeout=60
        )
        return r, trace


class TestFichiersCasses(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.agent = TestAgent(Path(self._tmp.name))

    def refuse(self, fragment="", **kw):
        r, trace = self.agent.lancer(**kw)
        self.assertNotEqual(r.returncode, 0, "devait échouer")
        self.assertTrue(r.stderr.strip(), "aucun message d'erreur")
        self.assertNotIn("Traceback", r.stderr)
        self.assertFalse(trace.exists(), "une trace a été écrite")
        if fragment:
            self.assertIn(fragment, r.stderr)

    # l'agent intact fonctionne, sinon tous les refus sont suspects
    def test_jeu_intact_accepte(self):
        r, trace = self.agent.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(trace.exists())

    # fichiers et JSON
    def test_01_fichier_absent(self):
        self.refuse("introuvable", supprimer=["carte.json"])

    def test_02_non_utf8(self):
        self.agent.brut["carte.json"] = b'{"nom": "\xe9\xff"}'
        self.refuse("UTF-8")

    def test_03_json_invalide(self):
        self.agent.brut["scenario.json"] = b'{"format": '
        self.refuse("JSON")

    def test_04_racine_pas_un_objet(self):
        self.agent.brut["donnees/dictionnaire.json"] = b'[1, 2, 3]'
        self.refuse("objet")

    def test_05_format_inattendu(self):
        self.agent.carte["format"] = "autre/chose"
        self.refuse("format")

    def test_06_version_inattendue(self):
        self.agent.armoire["version"] = 2
        self.refuse("version")

    # champs
    def test_07_champ_absent(self):
        del self.agent.carte["dimensions"]
        self.refuse("dimensions")

    def test_08_mauvais_type(self):
        self.agent.carte["dimensions"]["hauteur"] = "9"
        self.refuse("hauteur")

    def test_09_booleen_n_est_pas_un_entier(self):
        self.agent.carte["dimensions"]["largeur"] = True
        self.refuse("largeur")

    # grille
    def test_10_grille_non_rectangulaire(self):
        self.agent.carte["grille"][3] = self.agent.carte["grille"][3] + "#"
        self.refuse("rectangulaire")

    def test_11_dimensions_incoherentes(self):
        self.agent.carte["dimensions"]["hauteur"] = 10
        self.refuse("hauteur")

    def test_12_largeur_incoherente(self):
        self.agent.carte["dimensions"]["largeur"] = 12
        self.refuse("largeur")

    def test_13_position_hors_grille(self):
        self.agent.carte["armoire"]["position"] = [20, 4]
        self.refuse("hors de la grille")

    def test_14_resident_pas_sur_un_P(self):
        self.agent.carte["residents"][0]["position"] = [1, 1]
        self.refuse("resident")

    def test_15_depart_pas_sur_un_R(self):
        self.agent.carte["depart_robot"] = [2, 2]
        self.refuse("depart_robot")

    def test_16_dictionnaire_pas_sur_un_D(self):
        self.agent.carte["dictionnaire"]["position"] = [7, 5]
        self.refuse("dictionnaire")

    def test_17_armoire_pas_sur_un_A(self):
        self.agent.carte["armoire"]["position"] = [6, 3]
        self.refuse("armoire")

    def test_18_deux_residents_meme_id(self):
        self.agent.carte["residents"][1]["id"] = "R1"
        self.refuse("R1")

    # scenario
    def test_19_scenario_pour_une_autre_carte(self):
        self.agent.scenario["carte"] = "appartement_04"
        self.refuse("appartement_04")

    def test_20_demande_a_un_resident_absent(self):
        self.agent.scenario["demandes"][0]["resident"] = "R9"
        self.refuse("R9")

    def test_21_armoire_du_scenario_introuvable(self):
        self.agent.scenario["armoire"] = "armoire_fantome"
        self.refuse("armoire_fantome")

    # armoire
    def test_22_casier_hors_dimensions(self):
        self.agent.armoire["casiers"][0]["colonne"] = 8
        self.refuse("hors de l'armoire")

    def test_23_casier_en_double(self):
        c = self.agent.armoire["casiers"]
        c[1]["ligne"], c[1]["colonne"] = c[0]["ligne"], c[0]["colonne"]
        self.refuse("double")

    def test_24_etiquette_incoherente(self):
        self.agent.armoire["casiers"][0]["emotion"] = "tristesse"
        self.refuse("etiquette")

    def test_25_casier_depart_hors_armoire(self):
        self.agent.armoire["casier_depart"] = [3, 0]
        self.refuse("casier_depart")

    def test_26_intensite_inconnue(self):
        self.agent.armoire["casiers"][5]["intensite"] = "extreme"
        self.refuse("intensite")

    # dictionnaire
    def test_27_emotion_inconnue(self):
        self.agent.dico["entrees"][0]["emotion"] = "ennui"
        self.refuse("ennui")

    def test_28_meme_mot_dans_deux_entrees(self):
        mot = self.agent.dico["entrees"][0]["formes"][0]
        self.agent.dico["entrees"][-1]["formes"].append(mot)
        self.refuse(mot)

    # ligne de commande
    def test_29_arguments_manquants(self):
        self.refuse(arguments=["seulement_un"])


if __name__ == "__main__":
    unittest.main()
