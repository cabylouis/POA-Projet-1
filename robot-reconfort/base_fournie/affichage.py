from memoire import Memoire
from decision import Action
from perception import ARMOIRE, DICTIONNAIRE, LIBRE, MUR, RESIDENT

SYMBOLE = {MUR: "#", LIBRE: ".", ARMOIRE: "A", DICTIONNAIRE: "D", RESIDENT: "P"}

def rendre_grille(memoire: Memoire) -> str:
    """ Génère la représentation textuelle de la carte. """

    lignes = []

    for ligne in range(memoire.carte.hauteur):
        texte_ligne = ""

        for colonne in range(memoire.carte.largeur):
            case = (ligne, colonne)

            if case == memoire.position:
                texte_ligne += "R"
            else:
                type_case = memoire.carte.type_connu(case)
                texte_ligne += SYMBOLE.get(type_case, "?")

        lignes.append(texte_ligne)

    return "\n".join(lignes)

def rendre_texte(memoire: Memoire, numero: int, action: Action) -> str:
    """ Génère les informations textuelles sur l'action en cours. """

    argument = f" {action.argument}" if action.argument else ""
    objet_porte = memoire.objet_porte or "rien"

    lignes = [f"demande {numero} | {action.nom}{argument} | porte : {objet_porte} "f"| selecteur {list(memoire.selecteur)}"]

    if action.commentaire:
        lignes.append(f"  -> {action.commentaire}")

    return "\n".join(lignes)

def dessiner(memoire: Memoire, numero: int, action: Action) -> None:
    """ Affiche la carte et les informations de l'action en cours. """

    affichage = f"{rendre_grille(memoire)}\n{rendre_texte(memoire, numero, action)}"
    print("\033[H\033[J" + affichage, flush=True)