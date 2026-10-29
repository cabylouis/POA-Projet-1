from typing import Any
from reconfort_io import ErreurFichier


SYMBOLES_VALIDES = set("#.RADP")

def _erreur(chemin: Any, message: str) -> None:
    raise ErreurFichier(f"{chemin}: {message}")

def _est_entier(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _champ(obj: dict[str, Any], cle: str, type_attendu: type, chemin: Any, contexte: str = "") -> Any:

    nom = f"{contexte}{cle}"
    if cle not in obj.keys():
        _erreur(chemin, f"champ obligatoire absent: {nom}")

    valeur = obj[cle]

    if type_attendu is int:
        ok = _est_entier(valeur)
    else:
        ok = isinstance(valeur, type_attendu) and not (type_attendu is not bool and isinstance(valeur, bool))

    if not ok:
        _erreur(chemin, f"le champ {nom} doit être de type {type_attendu.__name__} et non {type(valeur).__name__}")

    return valeur

def _chaine_non_vide(obj: dict[str, Any], cle: str, chemin: Any, contexte: str = "") -> str:
    valeur = _champ(obj, cle, str, chemin, contexte)

    if not valeur.strip():
        _erreur(chemin, f"le champ {contexte}{cle} est vide")

    return valeur

def _position(valeur: Any, chemin: Any, nom: str) -> tuple[int, int]:
    if not isinstance(valeur, list) or len(valeur) != 2 or not all(_est_entier(x) for x in valeur):
        _erreur(chemin, f"{nom} doit etre un couple [ligne, colonne] d'entiers, trouvé {valeur}")

    return valeur[0], valeur[1]

def _liste_de_chaines_uniques(obj: dict[str, Any], cle: str, chemin: Any) -> list[str]:
    valeurs = _champ(obj, cle, list, chemin)

    if not valeurs:
        _erreur(chemin, f"la liste {cle} est vide")
    if not all(isinstance(v, str) and v for v in valeurs):
        _erreur(chemin, f"{cle} ne doit contenir que des chaines non vides")
    if len(set(valeurs)) != len(valeurs):
        _erreur(chemin, f"{cle} contient un doublon")

    return valeurs

# Carte
def valider_carte(carte: dict[str, Any], chemin: Any) -> None:
    _chaine_non_vide(carte, "nom", chemin)
    dims = _champ(carte, "dimensions", dict, chemin)
    hauteur = _champ(dims, "hauteur", int, chemin, "dimensions.")
    largeur = _champ(dims, "largeur", int, chemin, "dimensions.")
    
    if hauteur < 3 or largeur < 3:
        _erreur(chemin, f"dimensions trop petites : {hauteur}x{largeur}")

    grille = _champ(carte, "grille", list, chemin)

    if not all(isinstance(l, str) for l in grille):
        _erreur(chemin, "chaque ligne de 'grille' doit être une chaine")

    if len(grille) != hauteur:
        _erreur(chemin, f"dimensions incoherentes : hauteur annoncee {hauteur}, {len(grille)} lignes dans la grille")

    for i, ligne in enumerate(grille):
        if len(ligne) != len(grille[0]):
            _erreur(
                chemin,
                f"grille non rectangulaire : la ligne {i} fait {len(ligne)} caractères, la ligne 0 en fait {len(grille[0])}"
            )
        inconnus = set(ligne) - SYMBOLES_VALIDES
        if inconnus:
            _erreur(chemin, f"symbole inconnu {sorted(inconnus)} ligne {i}")

    if len(grille[0]) != largeur:
        _erreur(chemin, f"dimensions incohérentes : largeur annoncée {largeur}, {len(grille[0])} colonnes dans la grille")

    for i, ligne in enumerate(grille):
        bord = ligne if i in (0, hauteur - 1) else ligne[0] + ligne[-1]
        if set(bord) != {"#"}:
            _erreur(chemin, f"le bord de la grille doit être entièrement fait de murs (ligne {i})")

    def symbole(pos: tuple[int, int], nom: str, attendu: str) -> None:
        l, c = pos
        if not (0 <= l < hauteur and 0 <= c < largeur):
            _erreur(chemin, f"{nom} {list(pos)} est hors de la grille ({hauteur}x{largeur})")
        if grille[l][c] != attendu:
            _erreur(chemin, f"{nom} en {list(pos)} : la grille porte {grille[l][c]!r} a cet endroit, pas {attendu!r}")

    symbole(_position(carte.get("depart_robot"), chemin, "depart_robot"),"depart_robot", "R")
    arm = _champ(carte, "armoire", dict, chemin)

    symbole(_position(arm.get("position"), chemin, "armoire.position"),"armoire", "A")
    dico = _champ(carte, "dictionnaire", dict, chemin)

    symbole(_position(dico.get("position"), chemin, "dictionnaire.position"),"dictionnaire", "D")
    residents = _champ(carte, "residents", list, chemin)

    ids, positions = set(), set()
    for k, r in enumerate(residents):
        if not isinstance(r, dict):
            _erreur(chemin, f"residents[{k}] doit etre un objet")

        ctx = f"residents[{k}]."
        rid = _chaine_non_vide(r, "id", chemin, ctx)
        _chaine_non_vide(r, "nom", chemin, ctx)
        pos = _position(r.get("position"), chemin, f"{ctx}position")

        if rid in ids:
            _erreur(chemin, f"deux residents portent l'identifiant {rid!r}")
        ids.add(rid)

        if pos in positions:
            _erreur(chemin, f"deux residents sont en {list(pos)}")
        positions.add(pos)

        symbole(pos, f"resident {rid}", "P")

    compte = {s: sum(l.count(s) for l in grille) for s in "RADP"}
    for s, nom in (("R", "depart du robot"), ("A", "armoire"), ("D", "dictionnaire")):
        if compte[s] != 1:
            _erreur(chemin, f"la grille doit contenir exactement un {s!r} ({nom}), pas {compte[s]}")

    if compte["P"] != len(residents):
        _erreur(chemin, f"la grille contient {compte['P']} 'P' mais {len(residents)} residents sont declares")

# Dictionnaire
def valider_dictionnaire(d: dict[str, Any], chemin: Any) -> None:
    emotions = _liste_de_chaines_uniques(d, "emotions", chemin)
    intensites = _liste_de_chaines_uniques(d, "intensites", chemin)

    entrees = _champ(d, "entrees", list, chemin)
    vues: dict[str, int] = {}
    for k, e in enumerate(entrees):
        if not isinstance(e, dict):
            _erreur(chemin, f"entrees[{k}] doit etre un objet")

        ctx = f"entrees[{k}]."
        formes = _champ(e, "formes", list, chemin, ctx)
        if not formes or not all(isinstance(f, str) and f for f in formes):
            _erreur(chemin, f"{ctx}formes doit etre une liste de chaines non vides")

        emotion = _champ(e, "emotion", str, chemin, ctx)
        if emotion not in emotions:
            _erreur(chemin, f"emotion inconnue {emotion!r} dans entrees[{k}]")

        intensite = _champ(e, "intensite", str, chemin, ctx)
        if intensite not in intensites:
            _erreur(chemin, f"intensite inconnue {intensite!r} dans entrees[{k}]")

        for forme in set(formes):
            if forme in vues and vues[forme] != k:
                _erreur(chemin, f"le mot {forme!r} apparait dans deux entrees ({vues[forme]} et {k})")
            vues[forme] = k


# Armoire
def valider_armoire(a: dict[str, Any], chemin: Any) -> None:
    emotions = _liste_de_chaines_uniques(a, "emotions", chemin)
    intensites = _liste_de_chaines_uniques(a, "intensites", chemin)
    n_lignes, n_colonnes = len(intensites), len(emotions)

    def dans_armoire(pos: tuple[int, int], nom: str) -> None:
        if not (0 <= pos[0] < n_lignes and 0 <= pos[1] < n_colonnes):
            _erreur(chemin, f"{nom} {list(pos)} est hors de l'armoire ({n_lignes}x{n_colonnes})")

    dans_armoire(_position(a.get("casier_depart"), chemin, "casier_depart"), "casier_depart")
    casiers = _champ(a, "casiers", list, chemin)
    vus = set()
    for k, c in enumerate(casiers):
        if not isinstance(c, dict):
            _erreur(chemin, f"casiers[{k}] doit etre un objet")

        ctx = f"casiers[{k}]."
        ligne = _champ(c, "ligne", int, chemin, ctx)
        colonne = _champ(c, "colonne", int, chemin, ctx)
        emotion = _champ(c, "emotion", str, chemin, ctx)
        intensite = _champ(c, "intensite", str, chemin, ctx)

        if "objet" not in c:
            _erreur(chemin, f"champ obligatoire absent : {ctx}objet")

        if c["objet"] is not None and not isinstance(c["objet"], str):
            _erreur(chemin, f"{ctx}objet doit etre une chaine ou null")

        dans_armoire((ligne, colonne), f"casier {k}")
        if (ligne, colonne) in vus:
            _erreur(chemin, f"casier en double en {[ligne, colonne]}")

        vus.add((ligne, colonne))
        if emotion not in emotions:
            _erreur(chemin, f"emotion inconnue {emotion!r} dans le casier {[ligne, colonne]}")

        if intensite not in intensites:
            _erreur(chemin, f"intensite inconnue {intensite!r} dans le casier {[ligne, colonne]}")

        if emotions[colonne] != emotion or intensites[ligne] != intensite:
            _erreur(
                chemin,
                f"etiquette incoherente en {[ligne, colonne]} : {emotion}/{intensite} au lieu de {emotions[colonne]}/{intensites[ligne]}"
            )

    if len(vus) != n_lignes * n_colonnes:
        manquants = [(l, c) for l in range(n_lignes) for c in range(n_colonnes) if (l, c) not in vus]
        _erreur(chemin, f"casiers manquants : {[list(m) for m in manquants[:5]]}")

# Scenario
def valider_scenario(s: dict[str, Any], chemin: Any) -> None:
    _chaine_non_vide(s, "nom", chemin)
    _chaine_non_vide(s, "carte", chemin)

    armoire = _chaine_non_vide(s, "armoire", chemin)
    if "/" in armoire or "\\" in armoire or armoire in (".", ".."):
        _erreur(chemin, f"'armoire' doit etre un nom de fichier sans chemin, trouve {armoire!r}")

    demandes = _champ(s, "demandes", list, chemin)
    numeros = set()
    for k, d in enumerate(demandes):
        if not isinstance(d, dict):
            _erreur(chemin, f"demandes[{k}] doit etre un objet")

        ctx = f"demandes[{k}]."
        numero = _champ(d, "numero", int, chemin, ctx)
        _chaine_non_vide(d, "resident", chemin, ctx)
        _champ(d, "message", str, chemin, ctx)
        if numero in numeros:
            _erreur(chemin, f"numero de demande en double : {numero}")

        numeros.add(numero)

# Coherence entre fichiers
def valider_coherence(carte: dict[str, Any], dictionnaire: dict[str, Any], armoire: dict[str, Any], scenario: dict[str, Any], chemin_scenario: Any, chemin_dico: Any) -> None:
    if scenario["carte"] != carte["nom"]:
        _erreur(chemin_scenario, f"scenario prevu pour la carte {scenario['carte']!r}, mais la carte fournie s'appelle {carte['nom']!r}")

    ids = {r["id"] for r in carte["residents"]}
    for d in scenario["demandes"]:
        if d["resident"] not in ids:
            _erreur(chemin_scenario, f"la demande {d['numero']} s'adresse à {d['resident']!r}, absent de la carte")

    if dictionnaire["emotions"] != armoire["emotions"] or dictionnaire["intensites"] != armoire["intensites"]:
        _erreur(chemin_dico, "les emotions/intensites du dictionnaire different de celles de l'armoire (ordre compris)")