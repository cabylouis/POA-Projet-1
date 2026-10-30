from simulateur import Environnement
from memoire import Memoire
from reconfort_io import Trace
from decision import Action
from perception import Perception, Resultat

class Actionneur:
    """ Exécute les actions du robot et met à jour sa mémoire. """

    def __init__(self, environnement: Environnement, memoire: Memoire, trace: Trace) -> None:
        """ Initialise l'actionneur avec l'environnement, la mémoire et la trace. """

        self.environnement = environnement
        self.memoire = memoire
        self.trace = trace

    def executer(self, action: Action, perception: Perception, demande: int) -> Resultat:
        """ Enregistre l'action, l'exécute et met à jour la mémoire du robot. """

        if perception.devant_armoire:
            contenu_casier = perception.contenu_casier
        else:
            contenu_casier = None

        self.trace.ajouter_pas(demande = demande, position = self.memoire.position, casier = self.memoire.selecteur,
                               action = action.nom, argument = action.argument, perception = perception.voisins,
                               contenu_casier = contenu_casier, commentaire = action.commentaire)

        resultat = self.environnement.executer(action.nom, action.argument)
        self.memoire.apres_action(action.nom, action.argument, resultat.ok)

        return resultat