# Robot réconfort - Projet 1 - HAI716I

https://github.com/cabylouis/POA-Projet-1

Équipe: CABY Louis, GUIONNIERE Martin

Un robot de service qui doit, pour chaque message d'un résident, lire l'émotion exprimée dans un dictionnaire, trouver l'objet de réconfort correspondant dans une armoire à casiers, puis le rapporter au résident. Le robot ne connaît pas les murs : il les découvre en se déplaçant, tient à jour une carte mentale et replanifie quand la réalité contredit son plan.

---

## 1. Prérequis

- Python 3.10+
- Aucune dépendance externe

---

## 2. Lancer le robot

```
python agent.py <carte.json> <scenario.json> <dossier_donnees> <trace_a_ecrire.json>
```

Exemple :

```
python agent.py cartes/appartement_01.json cartes/scenario_01.json donnees sortie/trace_01.json
```

| Argument | Contenu |
|---|---|
| `carte` | fichier JSON de carte (`robot-reconfort/carte/appartement_XX.json`) |
| `scenario` | fichier JSON de scénario (`robot-reconfort/carte/scenario_XX.json`) |
| `donnees` | dossier contenant `dictionnaire.json` et les fichiers d'armoire |
| `trace` | fichier JSON de trace à écrire (le dossier est créé au besoin) |

### Affichage pour la vidéo

```
python agent.py cartes/appartement_01.json cartes/scenario_01.json donnees sortie/trace_01.json --afficher --delai 0.15
```

`--afficher` redessine dans le terminal la carte mentale du robot à chaque pas : `?` pour une case encore inconnue, `.` pour une case libre, `#` pour un mur, `R` pour le robot, `A` pour l'armoire, `D` pour le dictionnaire, `P` pour une personne. On voit les cases apparaître au fil de la découverte. `--delai` règle la pause entre deux pas, en secondes.

### Codes de retour

| Code | Signification |
|---|---|
| `0` | succès, trace écrite |
| `1` | erreur inattendue |
| `2` | erreur de données (fichier absent, mal formé, incohérent) |
| `3` | erreur interne : action illégale ou budget de pas dépassé |

Quel que soit le code non nul, aucune trace n'est écrite et le message d'erreur est affiché sur la sortie d'erreur, sans trace d'exception.

---

## 3. Lancer les tests

Depuis la racine du projet :

```
python -m unittest discover -s tests -t tests
```

| Fichier | Ce qu'il vérifie |
|---|---|
| `tests_planification` | plus court chemin sur une grille écrite à la main, replanification après découverte d'un mur, direction des pas |
| `tests_dictionnaire` | un message par émotion, premier mot reconnu gagnant, message sans mot reconnu |
| `tests_armoire` | déplacements du sélecteur, bouclage colonne 7 ↔ 0, lignes non cycliques, ordre de visite de la règle de repli |
| `tests_validation` | un fichier cassé par catégorie de la section 5.6, lancé via le vrai programme |
| `tests_integration` | scénarios complets : repli, échecs, résident muré, cartes aléatoires, séparation agent/simulateur |
| `verificateur` | outil, pas un test : rejoue une trace contre la réalité |

Le vérificateur est écrit indépendamment du robot. Il relit la grille et le contenu des casiers et contrôle :
- chaque position et chaque casier annoncés,
- chaque perception,
- chaque `contenu_casier`,
- la légalité de chaque action,
- la règle de repli, recalculée par force brute,
- qu'aucun casier annoncé vide n'a été déclaré sans avoir été vu,
- chaque résident inaccessible, par un parcours en largeur sur la vraie grille.

---

## 4. Architecture

| Module | Rôle |
|---|---|
| `perception.py` | types partagés : `Perception`, `Resultat`, `Connaissances` (ce que le robot sait au départ) |
| `memoire.py` | carte mentale, casiers déjà vus, position et sélecteur suivis par le robot lui-même |
| `decision.py` | machine à états d'une demande ; choisit la prochaine action, sans rien exécuter |
| `actions.py` | exécute l'action dans le monde et la journalise |
| `planification.py` | plus court chemin par parcours en largeur, écrit à la main |
| `roue.py` | roue de Plutchik et liste ordonnée des casiers candidats |
| `selecteur.py` | géométrie du sélecteur : colonnes cycliques, lignes non cycliques, itinéraires |
| `lecture_dictionnaire.py` | règle 6.1 : le premier mot reconnu donne l'émotion |
| `simulateur.py` | le monde : répond aux perceptions et vérifie la légalité des actions |
| `validation.py` | toutes les validations de la section 5.6, avant toute simulation |
| `affichage.py` | dessin de la carte mentale dans le terminal |
| `agent.py` | point d'entrée et boucle principale |
| `reconfort_io.py` | lecture des fichiers et écriture de la trace (base fournie) |

L'agent ne lit jamais le champ `grille` ni le champ `objet` des casiers. Seule `simulateur.preparer_monde` y accède et construit deux objets :
- l'`Environnement`, qui détient la vérité terrain ;
- les `Connaissances`, c'est-à-dire ce que le robot a le droit de savoir au départ.

Un test automatique vérifie que les modules de l'agent ne citent jamais ces champs.

### La boucle principale

À chaque tour, `agent.py` enchaîne :

1. `environnement.percevoir()` : les quatre cases voisines, et le contenu du casier courant si le robot est devant l'armoire ;
2. `memoire.integrer(perception)` : mise à jour de la carte mentale et de la mémoire d'armoire ;
3. `decideur.decider()` : une `Action` à exécuter, ou une `Issue` si la demande est terminée ;
4. `actionneur.executer(...)` : journalisation (position et casier avant l'action), puis exécution ;
5. `decideur.apres_action(...)` : prise en compte du résultat (lecture du dictionnaire, objet pris, objet donné).

Un budget de pas par demande (40 × hauteur × largeur) empêche toute boucle infinie.

---

## 5. Règles de décision implémentées

- Lecture de l'émotion (6.1): Le message est mis en minuscules, sans accents, et découpé sur tout ce qui n'est pas une lettre. Le premier mot présent dans le dictionnaire donne l'émotion et l'intensité. Aucun mot reconnu : échec `emotion indeterminee`.
- Choix du casier (6.2): On considère les 15 casiers à distance ≤ 2 sur la roue, triés par distance croissante, écart d'intensité croissant, intensité la plus faible d'abord, puis sens horaire avant antihoraire. Le robot visite ces casiers dans cet ordre et prend le premier garni. Si les 15 sont vides : échec `armoire vide`.
- Étiquette `repli`: `aucun` si le casier exact est garni, `intensite` pour la même émotion avec une autre intensité, `voisine_1` ou `voisine_2` selon la distance sur la roue.
- Fouille honnête: Un casier n'est déclaré vide que si le robot l'a effectivement vu. Un casier simplement traversé par le sélecteur compte comme vu, et son contenu est journalisé dans la trace. Le robot ne prend jamais un casier garni croisé en chemin s'il y en a un plus prioritaire.
- Itinéraire du sélecteur: Parmi les itinéraires de longueur minimale, le robot choisit celui qui montre le plus de casiers candidats encore inconnus.
- Planification: Hypothèse optimiste, une case inconnue est supposée libre. Le robot replanifie à chaque pas sur sa carte mentale, et ne fait qu'un pas du chemin calculé.
- Résident inaccessible: C'est une preuve, pas une supposition : si le parcours en largeur ne trouve aucun chemin sur la carte mentale, il n'en existe aucun dans la réalité (la carte mentale a au moins autant de cases libres que la réalité).

---

## 6. Choix de conception

1. Vérification d'accessibilité avant `PRENDRE`: L'énoncé décrit l'ordre dictionnaire -> armoire -> résident. Mais le robot ne peut pas reposer un objet, et `PRENDRE` exige les mains vides. Un robot qui prend l'objet avant de découvrir qu'un résident est muré le garderait pour toujours. Le robot lit donc le dictionnaire, puis prouve que le résident est atteignable (chemin fait uniquement de cases vues libres, sinon il s'en approche), et seulement ensuite prend l'objet. Le coût est un trajet supplémentaire la première fois qu'on sert un résident encore jamais approché (74 pas pour la demande 1 de `appartement_01`, contre environ 34 dans l'annexe D).
2. Bord de la grille connu: Le bord est prérempli en murs dans la carte mentale (règle 3.1) et vérifié à la validation.
3. Motifs d'échec ajoutés: `dictionnaire inaccessible` et `armoire inaccessible`, absents de la liste de l'énoncé mais possibles sur une carte sans garantie.
4. Contenu de l'armoire constant: pas de stock en projet 1. Les casiers déjà vus restent en mémoire d'une demande à l'autre.
5. Chaînes de motifs exactes: Les motifs d'échec sont écrits exactement comme dans l'énoncé (`resident inaccessible`, `armoire vide`, `emotion indeterminee`) : minuscules, sans accents. La correction automatique les compare mot pour mot.

---

## 7. Ce qui marche

- Les demandes des scénarios et cartes fournies sont livrées, avec les bons objets et les bons casiers.
- Le robot découvre le mur en (6,7) depuis (6,6) et replanifie en remontant par la ligne 2, comme décrit dans l'annexe D.
- Règle de repli : casier exact, repli d'intensité, repli sur une voisine à distance 1 puis 2, armoire vide à distance <= 2.
- Échecs sans interruption du scénario : émotion indéterminée, armoire vide, résident muré.
- Validation des fichiers d'entrée : fichier absent, non UTF-8, JSON invalide, `format`/`version`, champs absents ou mal typés, grille non rectangulaire ou aux dimensions incohérentes, positions hors grille ou sur le mauvais symbole, identifiants de résidents dupliqués, scénario pour une autre carte, casiers hors bornes ou dupliqués ou mal étiquetés, mot présent dans deux entrées du dictionnaire.
- Vérification automatique de traces sur des cartes aléatoires.

## 8. Ce qui ne marche pas, ou mal

- Trajets plus longs que nécessaire: La phase de vérification de l'accessibilité double le premier trajet vers un résident. Les allers-retours entre dictionnaire, armoire et résident ne sont pas optimisés d'une demande à l'autre.
- Replanification complète à chaque pas: Le parcours en largeur est relancé en entier à chaque tour. C'est instantané sur les cartes de la taille de l'énoncé, mais ça évolue mal pour des cartes plus grandes.
- Itinéraire du sélecteur: Montrer le plus de casiers inconnus n'est pas optimal globalement, le robot peut repasser par des casiers déjà connus vides.

---

## 9. Arborescence

```
Projet 1/
    ├── actions.py
    ├── affichage.py
    ├── agent.py                point d'entrée
    ├── decision.py
    ├── lecture_dictionnaire.py
    ├── memoire.py
    ├── perception.py
    ├── planification.py
    ├── reconfort_io.py
    ├── README.md
    ├── rendu.json
    ├── roue.py
    ├── selecteur.py
    ├── simulateur.py
    ├── validation.py
    ├── cartes/
    │   ├── appartement_01.json
    │   ├── ...
    │   ├── appartement_05.json
    │   ├── scenario_01.json
    │   ├── ...
    │   └── scenario_05.json
    ├── donnees/                 
    │   ├── armoire_standard.json
    │   └── dictionnaire.json
    ├── tests/                   tests automatisés et vérificateur
    │   ├── tests_armoire.py
    │   ├── tests_dictionnaire.py
    │   ├── tests_integration.py
    │   ├── tests_planification.py
    │   ├── tests_validation.py
    │   ├── utils.py
    │   └── verificateur.py
    └── demo.mp4                 vidéo de démonstration
```
