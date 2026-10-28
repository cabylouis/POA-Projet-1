from enum import Enum

from perception import Resultat
from planification import direction_entre
from planification import plus_court_chemin
from memoire import Memoire
from roue import Candidat, candidats
from selecteur import casiers_traverses, plus_court_chemins
from lecture_emotion import lire

Case = tuple[int, int]

class Phase(Enum):
    """ Phases successives du traitement d'une demande.

        DICTIONNAIRE : Consultation du dictionnaire émotionnel.
        VERIFICATION : Vérification de l'accessibilité du résident.
        ARMOIRE : Recherche et récupération d'un objet.
        LIVRAISON : Déplacement vers le résident et remise de l'objet.
        """

    DICTIONNAIRE = "dictionnaire"
    VERIFICATION = "verification"
    ARMOIRE = "armoire"
    LIVRAISON = "livraison"

class Etat(Enum):
    """ Résultat d'une tentative de déplacement vers une cible.

        ARRIVE : Le robot se trouve déjà sur une case d'accès.
        AVANCE : Un déplacement est nécessaire.
        BLOQUE : Aucun chemin n'a été trouvé.
        """

    ARRIVE = "arrive"
    AVANCE = "avance"
    BLOQUE = "bloque"

class Action:
    """ Représente une action à exécuter par le simulateur.

        Attributs:
            nom: Nom de l'action à exécuter.
            argument: Argument éventuel de l'action.
            commentaire: Explication du choix de l'action.
        """

    def __init__(self, nom: str, argument: str | None = None, commentaire: str | None = None) -> None:
        self.nom = nom
        self.argument = argument
        self.commentaire = commentaire

class Issue:
    """ Représente le résultat final du traitement d'une demande.

        Attributs:
            succes: Indique si la demande a été satisfaite.
            motif_echec: Raison de l'échec éventuel.
            emotion: Émotion identifiée dans la demande.
            intensite: Intensité de l'émotion identifiée.
            casier_choisi: Position du casier sélectionné.
            repli: Stratégie de repli éventuellement utilisée.
            objet: Objet sélectionné ou livré.
        """

    def __init__(self, succes: bool, motif_echec: str | None = None, emotion: str | None = None, intensite: str | None = None,
                 casier_choisi: Case | None = None, repli: str = "aucun", objet: str | None = None) -> None:
        self.succes = succes
        self.motif_echec = motif_echec
        self.emotion = emotion
        self.intensite = intensite
        self.casier_choisi = casier_choisi
        self.repli = repli
        self.objet = objet

class Decideur:
    """ Coordonne le traitement d'une demande de réconfort en déterminant
    les actions à effectuer selon la phase courante, l'état du monde et
    les informations mémorisées.
    """

    def __init__(self, memoire: Memoire) -> None:
        """ Initialise le décideur avec la mémoire du monde et initialise
        les variables nécessaires au traitement d'une demande.
        """

        self.memoire = memoire
        self.reinitialiser(0, "", "")

    def reinitialiser(self, numero: int, resident: str, message: str) -> None:
        """ Réinitialise l'état du décideur pour commencer une nouvelle demande. """

        self.numero = numero
        self.resident = resident
        self.message = message

        self.phase = Phase.DICTIONNAIRE
        self.emotion: str | None = None
        self.intensite: str | None = None

        self.liste: list[Candidat] = []
        self.choix: Candidat | None = None

        self.objet: str | None = None
        self.issue: Issue | None = None
        self.plan: tuple[Case, list[Case]] | None = None

    def nouvelle_demande(self, numero: int, resident: str, message: str) -> None:
        """ Démarre le traitement d'une nouvelle demande en réinitialisant le décideur. """

        self.reinitialiser(numero, resident, message)

    def decider(self) -> Issue | Action | None:
        """ Détermine la prochaine action à exécuter en fonction de la phase courante. """

        if self.issue is not None:
            return self.issue

        while True:
            if self.phase == Phase.DICTIONNAIRE:
                etat,action = self.aller_adjacent(self.memoire.k.dictionnaire, "Vers le dictionnaire")

                if etat == Etat.ARRIVE:
                    return Action("CONSULTER")

                if etat == Etat.BLOQUE:
                    return self.echec("Dictionnaire inaccessible")

                return action

            if self.phase == Phase.VERIFICATION:
                if self.resident_accessible():
                    self.phase = Phase.ARMOIRE
                    continue

                etat, action = self.aller_adjacent(self.memoire.k.residents[self.resident], f"verification : {self.resident} est-il atteignable ?")
                if etat == Etat.BLOQUE:
                    return self.echec("Resident inaccessible")

                if etat == Etat.ARRIVE:
                    self.phase = Phase.ARMOIRE
                    continue

                return action

            if self.phase == Phase.ARMOIRE:
                return self.decider_armoire()

            return self.decider_livraison()

    def apres_action(self, action: Action, resultat: Resultat) -> None:
        """ Met à jour l'état du décideur après l'exécution d'une action.
        Si l'action a échoué, aucune modification n'est effectuée et sinon
        traite le résultat selon le type d'action.
        """

        if not resultat.ok:
            return

        if action.nom == "CONSULTER":
            if resultat.donnees is None:
                self.issue = Issue(False, "Données invalides")
                return

            lu = lire(self.message, resultat.donnees)

            if lu is None:
                self.issue = Issue(False, "Emotion indéterminée")
                return

            self.emotion, self.intensite = lu

            self.liste = candidats(self.memoire.k.emotions.index(self.emotion), self.memoire.k.intensites.index(self.intensite), len(self.memoire.k.emotions), len(self.memoire.k.intensites))
            self.phase = Phase.VERIFICATION

        elif action.nom == "PRENDRE":
            self.objet = action.argument
            self.phase = Phase.LIVRAISON

        elif action.nom == "DONNER":
            if self.choix is None:
                raise Exception("Aucun candidat sélectionné lors de la livraison")

            self.issue = Issue(True, None, self.emotion, self.intensite, self.choix.casier(), self.choix.repli, self.objet)


    def aller_adjacent(self, cible: Case, raison: str) -> tuple[Etat, Action | None]:
        """ Calcule un chemin vers une case d'accès à la cible et détermine
        si le robot est arrivé, peut avancer ou est bloqué.
        """

        carte, pos = self.memoire.carte, self.memoire.position
        arrivees = carte.cases_d_acces(cible)
        chemin = plus_court_chemin(pos, arrivees, carte.traversable_optimiste)

        if chemin is None:
            return Etat.BLOQUE, None

        if len(chemin) == 1:
            self.plan = None
            return Etat.ARRIVE, None

        commentaire = raison

        if self.plan is not None and self.plan[0] == cible:
            if len(chemin) != len(self.plan[1]) - 1:
                commentaire = f"Re-planification ({raison})"

        self.plan = (cible, chemin)
        return Etat.AVANCE, Action("AVANCER", direction_entre(chemin[0], chemin[1]), commentaire)

    def resident_accessible(self) -> bool:
        """ Vérifie si le résident courant est accessible depuis la position
         du robot en utilisant les cases libres connues.
         """

        pos_resident = self.memoire.k.residents[self.resident]
        arrivees = self.memoire.carte.cases_d_acces(pos_resident, certaines = True)

        return plus_court_chemin(self.memoire.position, arrivees, self.memoire.carte.libre_connue) is not None

    def decider_armoire(self) -> Issue | Action | None:
        """ Détermine la prochaine action à effectuer pour sélectionner
        et récupérer un objet dans l'armoire.
        """

        etat, action = self.aller_adjacent(self.memoire.k.armoire, f"Vers l'armoire")

        if etat == Etat.BLOQUE:
            return self.echec("Armoire inaccessible")

        if etat == Etat.AVANCE:
            return action

        cible = self.prochain_casier()
        if cible is None:
            return self.echec("Armoire vide")

        if self.memoire.selecteur == cible.casier():
            objet = self.memoire.armoire.objet(cible.casier())

            if objet is None:
                raise Exception("Sélecteur sur un casier non perçu")

            self.choix = cible
            return Action("PRENDRE", objet, f"Casier {list(cible.casier())} : Repli {cible.repli}")

        route = self.meilleur_itineraire(cible)
        if route is None:
            raise Exception("Pas d'itinéraire")

        return Action("CHERCHER", route[0], f"Fouille : Vers {list(cible.casier())}")

    def prochain_casier(self) -> Candidat | None:
        """ Recherche le prochain candidat à examiner ou à récupérer
        dans la liste des candidats.
        """

        for casier in self.liste:
            if not self.memoire.armoire.est_vu(casier.casier()):
                return casier

            if self.memoire.armoire.objet(casier.casier()) is not None:
                return casier

        return None

    def meilleur_itineraire(self, cible: Candidat) -> list[str] | None:
        """ Sélectionne un itinéraire vers le casier cible en privilégiant
        les trajets permettant de traverser le plus de casiers encore inconnus.

        Voir Annexe C.4
        """

        utiles = set()

        for casier in self.liste:
            if not self.memoire.armoire.est_vu(casier.casier()):
                utiles.add(casier.casier())

        routes = plus_court_chemins(self.memoire.selecteur, cible.casier(), self.memoire.n_colonnes)
        meilleur, meilleur_score = None, -1

        for route in routes:
            vus = casiers_traverses(self.memoire.selecteur, route, self.memoire.n_lignes, self.memoire.n_colonnes)
            score = len(utiles.intersection(vus))

            if score > meilleur_score:
                meilleur, meilleur_score = route, score

        return meilleur

    def decider_livraison(self) -> Issue | Action | None:
        """ Détermine les actions nécessaires pour rejoindre le résident courant
        et lui remettre l'objet transporté.
        """

        etat, action = self.aller_adjacent(self.memoire.k.residents[self.resident], f"Vers {self.resident}")

        if etat == Etat.BLOQUE:
            return self.echec("Resident inaccessible")

        if etat == Etat.AVANCE:
            return action

        return Action("DONNER", self.objet, f"Pour {self.resident}")

    def echec(self, motif: str) -> Issue | None:
        """ Enregistre l'échec de la demande avec son motif et les informations
        émotionnelles disponibles, puis retourne l'issue correspondante.
        """

        self.issue = Issue(False, motif, self.emotion, self.intensite)
        return self.issue
