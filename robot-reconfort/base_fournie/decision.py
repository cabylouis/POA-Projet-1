from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


from lecture_emotion import lire
from memoire import Memoire
from perception import Resultat
from planification import direction_entre, plus_court_chemin
from roue import Candidat, candidats
from selecteur import casiers_traverses, plus_court_chemins



Case = Tuple[int, int]


class Phase(Enum):
    DICTIONNAIRE = "dictionnaire"
    VERIFICATION = "verification"
    ARMOIRE = "armoire"
    LIVRAISON = "livraison"


@dataclass
class Action:
    nom: str
    argument: Optional[str] = None
    commentaire: Optional[str] = None


@dataclass
class Issue:
    """data fin demande pour trace"""
    succes: bool
    motif_echec: Optional[str] = None
    emotion: Optional[str] = None
    intensite: Optional[str] = None
    casier_choisi: Optional[Case] = None
    repli: str = "aucun"
    objet: Optional[str] = None


ARRIVE, AVANCE, BLOQUE = "arrive", "avance", "bloque"


def _adjacentes(a: Case, b: Case) -> bool:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


class Decideur:
    def __init__(self, memoire: Memoire) -> None:
        self.m = memoire
        self._reinitialiser(0, "", "")

    # cycle de vie d'une demande

    def _reinitialiser(self, numero: int, resident: str, message: str) -> None:
        self.numero = numero
        self.resident = resident
        self.message = message
        self.phase = Phase.DICTIONNAIRE
        self.emotion: Optional[str] = None
        self.intensite: Optional[str] = None
        self.liste: list[Candidat] = []
        self.choix: Optional[Candidat] = None
        self.objet: Optional[str] = None
        self._issue: Optional[Issue] = None
        self._plan: Optional[Tuple[Case, list[Case]]] = None

    def nouvelle_demande(self, numero: int, resident: str, message: str) -> None:
        self._reinitialiser(numero, resident, message)

    # point d'entree

    def decider(self):
        """Action ou Issue (demande terminée)."""
        if self._issue is not None:
            return self._issue
        while True:
            if self.phase is Phase.DICTIONNAIRE:
                etat, action = self._aller_adjacent(self.m.k.dictionnaire, "vers le dictionnaire")
                if etat == BLOQUE:
                    return self._echec("dictionnaire inaccessible")
                return Action("CONSULTER") if etat == ARRIVE else action

            if self.phase is Phase.VERIFICATION:
                if self._resident_prouve_accessible():
                    self.phase = Phase.ARMOIRE
                    continue
                etat, action = self._aller_adjacent(
                    self.m.k.residents[self.resident],
                    f"verification : {self.resident} est-il atteignable ?"
                )
                if etat == BLOQUE:
                    return self._echec("resident inaccessible")
                if etat == ARRIVE:
                    self.phase = Phase.ARMOIRE
                    continue
                return action

            if self.phase is Phase.ARMOIRE:
                return self._decider_armoire()

            return self._decider_livraison()

    def apres_action(self, action: Action, resultat: Resultat) -> None:
        if not resultat.ok:
            return
        if action.nom == "CONSULTER":
            lu = lire(self.message, resultat.donnees)
            if lu is None:
                self._issue = Issue(False, "emotion indeterminee")
                return
            self.emotion, self.intensite = lu
            k = self.m.k
            self.liste = candidats(
                k.emotions.index(self.emotion),
                k.intensites.index(self.intensite),
                len(k.emotions),
                len(k.intensites)
            )
            self.phase = Phase.VERIFICATION
        elif action.nom == "PRENDRE":
            self.objet = action.argument
            self.phase = Phase.LIVRAISON
        elif action.nom == "DONNER":
            self._issue = Issue(
                True, None, self.emotion, self.intensite,
                self.choix.casier, self.choix.repli, self.objet
            )

    # navigation

    def _aller_adjacent(self, cible: Case, raison: str):
        """replanifie à chaque tour vers case adjacente à cible"""
        carte, pos = self.m.carte, self.m.position
        arrivees = carte.cases_d_acces(cible)
        chemin = plus_court_chemin(pos, arrivees, carte.traversable_optimiste)
        if chemin is None:
            return BLOQUE, None
        if len(chemin) == 1:
            self._plan = None
            return ARRIVE, None
        commentaire = raison
        if self._plan is not None and self._plan[0] == cible:
            if len(chemin) != len(self._plan[1]) - 1:
                commentaire = f"replanification ({raison})"
        self._plan = (cible, chemin)
        return AVANCE, Action("AVANCER", direction_entre(chemin[0], chemin[1]), commentaire)

    def _resident_prouve_accessible(self) -> bool:
        carte = self.m.carte
        pos_resident = self.m.k.residents[self.resident]
        arrivees = carte.cases_d_acces(pos_resident, certaines=True)
        return plus_court_chemin(self.m.position, arrivees, carte.libre_connue) is not None

    # armoire

    def _prochain_casier(self) -> Optional[Candidat]:
        """Premier candidat ordre 6.2"""
        for c in self.liste:
            if not self.m.armoire.est_vu(c.casier):
                return c
            if self.m.armoire.objet(c.casier) is not None:
                return c
        return None

    def _decider_armoire(self):
        etat, action = self._aller_adjacent(self.m.k.armoire, "vers l'armoire")
        if etat == BLOQUE:
            return self._echec("armoire inaccessible")
        if etat == AVANCE:
            return action
        cible = self._prochain_casier()
        if cible is None:
            return self._echec("armoire vide")
        m = self.m
        if m.selecteur == cible.casier:
            objet = m.armoire.objet(cible.casier)
            if objet is None:
                raise RuntimeError("selecteur sur un casier non percu")
            self.choix = cible
            return Action("PRENDRE", objet,
                          f"casier {list(cible.casier)} : repli {cible.repli}")
        route = self._meilleur_itineraire(cible)
        return Action("CHERCHER", route[0],
                      f"fouille : cap sur {list(cible.casier)}")

    def _meilleur_itineraire(self, cible: Candidat) -> list[str]:
        """annexe C.4"""
        m = self.m
        utiles = {c.casier for c in self.liste if not m.armoire.est_vu(c.casier)}
        meilleure, meilleur_score = None, -1
        for route in plus_court_chemins(m.selecteur, cible.casier, m.n_colonnes):
            vus = casiers_traverses(m.selecteur, route, m.n_lignes, m.n_colonnes)
            score = len(utiles.intersection(vus))
            if score > meilleur_score:
                meilleure, meilleur_score = route, score
        return meilleure

    # livraison

    def _decider_livraison(self):
        etat, action = self._aller_adjacent(
            self.m.k.residents[self.resident], f"vers {self.resident}")
        if etat == BLOQUE:
            return self._echec("resident inaccessible")
        if etat == AVANCE:
            return action
        return Action("DONNER", self.objet, f"pour {self.resident}")

    def _echec(self, motif: str) -> Issue:
        self._issue = Issue(False, motif, self.emotion, self.intensite)
        return self._issue
