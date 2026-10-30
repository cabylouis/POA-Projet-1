"""Rejoue une trace contre la réalité.

Volontairement indépendant du code du robot : il relit la grille et les objets
et re-dérive la règle de repli par force brute, avec une autre écriture que roue.py.
Renvoie la liste des anomalies ; liste vide = trace conforme.
"""

from __future__ import annotations
from collections import deque

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from reconfort_io import normaliser
from simulateur import SYMBOLES

DIRECTIONS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "O": (0, -1)}


def casier_attendu(emotion, intensite, emotions, intensites, vide):
    """Premier casier (6.2) brute force"""

    n = len(emotions)
    e0, i0 = emotions.index(emotion), intensites.index(intensite)

    cases = []
    for emotion in range(n):
        distance = min((emotion - e0) % n, (e0 - emotion) % n)
        if distance > 2:
            continue

        for intensite in range(len(intensites)):
            sens = 0 if (emotion - e0) % n == distance else 1
            cases.append((distance, abs(intensite - i0), intensite, sens, (intensite, emotion)))
    cases.sort()

    for distance, _, _, _, casier in cases:
        if not vide(casier):
            return casier, distance
    return None, None


def accessible(carte, cible):
    """BFS sur la vraie grille depuis le depart"""

    grille = carte["grille"]
    depart = tuple(carte["depart_robot"])
    vus, file = {depart}, deque([depart])
    while file:
        current = file.popleft()
        if abs(current[0] - cible[0]) + abs(current[1] - cible[1]) == 1:
            return True
        for delta_lin, delta_col in DIRECTIONS.values():
            nx = (current[0] + delta_lin, current[1] + delta_col)
            if nx not in vus and SYMBOLES[grille[nx[0]][nx[1]]] == "libre":
                vus.add(nx)
                file.append(nx)
    return False

def est_adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

def verifier(carte, armoire, dico, scenario, trace):
    err = []
    grille = carte["grille"]
    armoire_pos = tuple(carte["armoire"]["position"])
    dictionnaire_pos = tuple(carte["dictionnaire"]["position"])
    residents_pos = {r["id"]: tuple(r["position"]) for r in carte["residents"]}
    objets = {(c["ligne"], c["colonne"]): c["objet"] for c in armoire["casiers"]}
    emotions, intensites = armoire["emotions"], armoire["intensites"]
    n_lignes, n_cols = len(intensites), len(emotions)

    grille = carte["grille"]
    def type_case(p):
        return SYMBOLES[grille[p[0]][p[1]]]

    pos = tuple(carte["depart_robot"])
    casier_select = tuple(armoire["casier_depart"])
    porte = None
    vus = {} # casier -> objet
    pas_par_demande = {}
    index = {f: (e["emotion"], e["intensite"]) for e in dico["entrees"] for f in e["formes"]}
    dernier_prendre = {}
    consulte = {}

    for pas in trace["pas"]:
        t = pas["t"]

        if tuple(pas["position"]) != pos:
            err.append(f"t={t}: position annoncée {pas['position']} != réelle {list(pos)}")

        if tuple(pas["casier"]) != casier_select:
            err.append(f"t={t}: casier annoncé {pas['casier']} != réel {list(casier_select)}")

        reel = {d: type_case((pos[0] + dl, pos[1] + dc)) for d, (dl, dc) in DIRECTIONS.items()}
        if pas["perception"] != reel:
            err.append(f"t={t}: perception falsifiee {pas['perception']} != {reel}")

        devant = est_adjacent(pos, armoire_pos)
        attendu = objets[casier_select] if devant else None
        if pas["contenu_casier"] != attendu:
            err.append(f"t={t}: contenu_casier {pas['contenu_casier']!r} != {attendu!r}")

        if devant:
            vus[casier_select] = objets[casier_select]

        action, arg, demande = pas["action"], pas["argument"], pas["demande"]
        pas_par_demande[demande] = pas_par_demande.get(demande, 0) + 1

        if action == "AVANCER":
            nxt = (pos[0] + DIRECTIONS[arg][0], pos[1] + DIRECTIONS[arg][1])
            if type_case(nxt) != "libre":
                err.append(f"t={t}: AVANCER {arg} vers {type_case(nxt)}")
            else:
                pos = nxt

        elif action == "CONSULTER":
            if not est_adjacent(pos, dictionnaire_pos):
                err.append(f"t={t}: CONSULTER hors adjacence")
            consulte[demande] = True

        elif action == "CHERCHER":
            if not devant:
                err.append(f"t={t}: CHERCHER hors adjacence")

            l, c = casier_select
            if arg == "N":
                l -= 1
            elif arg == "S":
                l += 1
            elif arg == "E":
                c = (c + 1) % n_cols
            elif arg == "O":
                c = (c - 1) % n_cols
            if not 0 <= l < n_lignes:
                err.append(f"t={t}: CHERCHER {arg} sort de l'armoire")
            else:
                casier_select = (l, c)

        elif action == "PRENDRE":
            if not devant:
                err.append(f"t={t}: PRENDRE hors adjacence")
            if porte is not None:
                err.append(f"t={t}: PRENDRE en portant deja {porte}")
            if objets[casier_select] is None:
                err.append(f"t={t}: PRENDRE casier vide")
            elif arg != objets[casier_select]:
                err.append(f"t={t}: PRENDRE {arg!r} != {objets[casier_select]!r}")

            porte = arg
            dernier_prendre[demande] = (casier_select, dict(vus))

        elif action == "DONNER":
            r = next((x for x in scenario["demandes"] if x["numero"] == demande), None)
            if r is None or not est_adjacent(pos, residents_pos[r["resident"]]):
                err.append(f"t={t}: DONNER hors adjacence du resident")
            if porte != arg:
                err.append(f"t={t}: DONNER {arg!r} alors qu'on porte {porte!r}")
            porte = None

    # livraisons
    livraisons = {l["demande"]: l for l in trace["livraisons"]}
    if [l["demande"] for l in trace["livraisons"]] != [d["numero"] for d in scenario["demandes"]]:
        err.append("livraisons : ordre ou nombre different du scenario")

    for demande in scenario["demandes"]:
        l = livraisons.get(demande["numero"])
        if l is None:
            continue

        if l["motif_echec"] == "dictionnaire inaccessible":
            if accessible(carte, dictionnaire_pos):
                err.append(f"demande {demande['numero']}: 'dictionnaire inaccessible' a tort")
            continue

        mots = normaliser(demande["message"])
        lu = next((index[m] for m in mots if m in index), None)
        if lu is None:
            if l["succes"] or l["motif_echec"] != "emotion indeterminee":
                err.append(f"demande {demande['numero']}: devait echouer 'emotion indeterminee'")
            continue

        if (l["emotion"], l["intensite"]) != lu:
            err.append(f"demande {demande['numero']}: emotion {l['emotion']}/{l['intensite']} != {lu}")

        casier, dist = casier_attendu(lu[0], lu[1], emotions, intensites, lambda c: objets[c] is None)
        if l["succes"]:
            if tuple(l["casier_choisi"]) != casier:
                err.append(f"demande {demande['numero']}: casier {l['casier_choisi']} != {list(casier)}")

            if l["objet"] != objets[casier]:
                err.append(f"demande {demande['numero']}: objet {l['objet']!r} != {objets[casier]!r}")

            emotion, intensite = emotions.index(lu[0]), intensites.index(lu[1])
            attendu_repli = ("aucun" if casier == (intensite, emotion) else "intensite" if dist == 0 else f"voisine_{dist}")
            if l["repli"] != attendu_repli:
                err.append(f"demande {demande['numero']}: repli {l['repli']} != {attendu_repli}")

            # tous les casiers plus prioritaires ont-ils été vus (avant le PRENDRE) ?
            n = len(emotions)
            select_prendre, vus_a_ce_moment = dernier_prendre.get(demande["numero"], (None, {}))
            for e in range(n):
                dd = min((e - emotion) % n, (emotion - e) % n)
                for i in range(n_lignes):
                    cle = (dd, abs(i - intensite), i, 0 if (e - emotion) % n == dd else 1)
                    cle_choisi = (dist, abs(casier[0] - intensite), casier[0],
                                  0 if (casier[1] - emotion) % n == dist else 1)
                    if dd <= 2 and cle < cle_choisi and (i, e) not in vus_a_ce_moment:
                        err.append(f"demande {demande['numero']}: casier {[i, e]} annonce vide mais jamais vu")
        else:
            motif = l["motif_echec"]
            if motif == "armoire vide":
                if casier is not None:
                    err.append(f"demande {demande['numero']}: 'armoire vide' a tort")
            elif motif == "resident inaccessible":
                if accessible(carte, residents_pos[demande["resident"]]):
                    err.append(f"demande {demande['numero']}: 'resident inaccessible' a tort")
            elif motif == "armoire inaccessible":
                if accessible(carte, armoire_pos):
                    err.append(f"demande {demande['numero']}: 'armoire inaccessible' a tort")
            else:
                err.append(f"demande {demande['numero']}: motif inattendu {motif!r}")

    for demande, l in livraisons.items():
        if l["pas_utilises"] != pas_par_demande.get(demande, 0):
            err.append(f"demande {demande}: pas_utilises incoherent")

    if porte is not None and trace["livraisons"] and all(l["succes"] for l in trace["livraisons"]):
        err.append("le robot garde un objet en main a la fin")

    return err
