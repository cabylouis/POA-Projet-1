import json
import time
import argparse
import sys
from pathlib import Path

import validation
from reconfort_io import (ErreurFichier, Trace, charger_armoire, charger_carte, charger_dictionnaire, charger_scenario)
from simulateur import preparer_monde, ActionIllegale
from memoire import Memoire
from decision import Decideur, Issue
from actions import Actionneur
from affichage import dessiner

PAS_MAX_PAR_DEMANDE_PAR_CASE = 40

class ErreurInterne(Exception):
    pass

def charger_et_valider(chemin_carte, chemin_scenario, dossier):
    """ Charge et valide la carte, le scénario, le dictionnaire et l'armoire.
    Vérifie également la cohérence des données entre ces fichiers.
    """

    carte = charger_carte(chemin_carte)
    validation.valider_carte(carte, chemin_carte)

    scenario = charger_scenario(chemin_scenario)
    validation.valider_scenario(scenario, chemin_scenario)

    dossier = Path(dossier)
    if not dossier.is_dir():
        raise ErreurFichier(f"dossier de donnees introuvable : {dossier}")

    chemin_dictionnaire = dossier / "dictionnaire.json"
    dictionnaire = charger_dictionnaire(chemin_dictionnaire)
    validation.valider_dictionnaire(dictionnaire, chemin_dictionnaire)

    chemin_armoire = dossier / f"{scenario['armoire']}.json"
    armoire = charger_armoire(chemin_armoire)
    validation.valider_armoire(armoire, chemin_armoire)

    validation.valider_coherence(carte, dictionnaire, armoire, scenario, chemin_scenario, chemin_dictionnaire)
    return carte, scenario, dictionnaire, armoire

def lire_equipe() -> list[str]:
    """ Lit les membres de l'équipe depuis rendu.json. """

    donnees_rendu = json.loads((Path(__file__).parent / "rendu.json").read_text(encoding = "utf-8"))
    equipe = donnees_rendu.get("equipe", [])

    if isinstance(equipe, list):
        membres = []

        for membre in equipe:
            membres.append(str(membre))

        return membres

    return []


def executer_scenario(carte: dict, scenario: dict, dictionnaire: dict, armoire: dict, equipe: list[str] | None,
                      afficher: bool = False, delai: float = 0.1) -> Trace:
    """ Exécute les demandes du scénario et enregistre les résultats.
    Initialise le monde, puis répète pour chaque demande les étapes de
    perception, de mémorisation, de décision et d'exécution des actions.
    """

    environnement, connaissances = preparer_monde(carte, armoire, dictionnaire)
    memoire = Memoire(connaissances)
    decideur = Decideur(memoire)
    trace = Trace(carte["nom"], scenario["nom"], equipe)
    actionneur = Actionneur(environnement, memoire, trace)

    budget = PAS_MAX_PAR_DEMANDE_PAR_CASE * connaissances.hauteur * connaissances.largeur

    for demande in scenario["demandes"]:
        numero, resident = demande["numero"], demande["resident"]
        environnement.accepter_demande(resident)
        decideur.nouvelle_demande(numero, resident, demande["message"])
        pas_demande = 0

        while True:
            perception = environnement.percevoir()
            memoire.integrer(perception)
            decision = decideur.decider()

            if isinstance(decision, Issue):
                trace.ajouter_livraison(numero, resident, decision.emotion, decision.intensite,
                    decision.casier_choisi, decision.repli, decision.objet, decision.succes, decision.motif_echec)
                break

            pas_demande += 1
            if pas_demande > budget:
                raise ErreurInterne(f"Demande {numero} : budget de pas dépassé")

            if decision is not None:
                if afficher:
                    dessiner(memoire, numero, decision)
                    time.sleep(delai)

                resultat = actionneur.executer(decision, perception, numero)  # ACTION
                decideur.apres_action(decision, resultat)

    return trace

def lire_arguments(argv: list[str]):
    """ Analyse les arguments fournis en ligne de commande. """

    parser = argparse.ArgumentParser(prog="agent.py")

    parser.add_argument("carte")
    parser.add_argument("scenario")
    parser.add_argument("donnees")
    parser.add_argument("trace")

    parser.add_argument("--afficher", action = "store_true")
    parser.add_argument("--delai", type = float)
    
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """ Lance le programme et renvoie un code de sortie.
    Charge les données, exécute le scénario, puis écrit et affiche
    le résumé de la trace.
    """

    args = lire_arguments(sys.argv[1:] if argv is None else argv)

    try:
        carte, scenario, dictionnaire, armoire = charger_et_valider(args.carte, args.scenario, args.donnees)
        trace = executer_scenario(carte, scenario, dictionnaire, armoire, lire_equipe(), args.afficher, args.delai)

    except ErreurFichier as err:
        print(f"ERREUR : {err}", file = sys.stderr)
        return 2
    except (ActionIllegale, ErreurInterne) as err:
        print(f"ERREUR INTERNE : {err}", file = sys.stderr)
        return 3
    except Exception as err:
        print(f"ERREUR INATTENDUE : {err}", file = sys.stderr)
        return 1

    trace.ecrire(args.trace)
    resume = trace.en_dictionnaire()["resume"]

    print(f"Trace ecrite : {args.trace} -- {resume['reussies']}/{resume['demandes']} demandes reussies, {resume['pas_total']} pas.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
