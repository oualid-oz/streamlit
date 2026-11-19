# Mes parties d'échecs : lisez-moi

Ces onze fichiers sont mes propres parties, jouées de juillet 2023 à novembre 2026 sur Lichess et Chess.com, exportées de ChessXP.
Les adversaires sont remplacés par un hash (`adv_384393ffd8`). Ce hash protège peu : qui devine un pseudo peut le hacher et comparer, et chaque partie se retrouve sur la plateforme à sa date et à son Elo. Ces parties y sont publiques, je l'accepte.
Le moteur d'échecs a analysé les parties et jugé mes coups, c'est ce qui donne les erreurs et les précisions du fichier.
La question du jour : « je joue depuis 2023, je stagne, qu'est-ce que je devrais travailler ? »
Vous n'avez pas besoin de savoir jouer, seulement de savoir lire un tableau et de vous méfier des pièges ci-dessous.

## Les fichiers en un coup d'œil

| fichier | une ligne = | lignes |
|---|---|---|
| `parties.csv` | une partie | 3 023 |
| `coups_juges.csv` | un de mes coups que le moteur juge mauvais | 22 596 |
| `phases.csv` | une phase d'une partie (ouverture, milieu, finale) | 11 089 |
| `moments_critiques.csv` | un de mes coups qui fait perdre beaucoup | 4 278 |
| `elo.csv` | un point de la courbe de mon classement | 4 043 |
| `puzzles.csv` | une tentative de problème tactique | 726 |
| `puzzle_elo.csv` | l'évolution de mon classement aux problèmes | 503 |
| `entrainement_ouvertures.csv` | un coup travaillé pendant un entraînement d'ouvertures | 7 509 |
| `plans_du_jour.csv` | un plan d'entraînement du jour | 25 |
| `revues.csv` | une revue de partie écrite par le coach | 3 |
| `conseils.csv` | un conseil du carnet de coaching | 0 (en-tête seul) |

## Joindre les fichiers

Le lien entre les fichiers est `partie_id` (`P0001` à `P3023`, numérotée dans l'ordre des dates).
Elle est dans `parties`, `coups_juges`, `phases`, `moments_critiques` et `revues`.
Elle est aussi dans `elo` (vide pour l'historique et les valeurs actuelles) et dans `puzzles` (remplie une seule fois sur 726).
`entrainement_ouvertures`, `puzzle_elo`, `plans_du_jour` et `conseils` ne se rattachent à aucune partie.

```python
import pandas as pd

p = pd.read_csv("parties.csv")
c = pd.read_csv("coups_juges.csv")
tout = c.merge(p[["partie_id", "resultat", "cadence"]], on="partie_id")
```

Un `merge` sur `partie_id` répète les colonnes de `parties` sur chaque coup : comptez les parties avec `nunique()`, pas avec `len()`.

## Ce que j'ai corrigé avant de vous donner les fichiers

Chess.com ne garde pas mon Elo d'avant la partie, il garde celui d'après. Lichess garde celui d'avant, avec la variation.
Un modèle qui lit l'Elo d'après sur Chess.com « devine » le résultat : l'Elo monte quand je gagne et baisse quand je perds, il suffit de le comparer à la partie précédente.
Sur mes parties blitz Chess.com, la variation d'Elo et le résultat ont une corrélation de 0,98, et un modèle entraîné sur toutes mes parties avec l'écart d'Elo d'après la partie atteint une AUC de 0,71 qui triche : il ne prédit rien, il lit la réponse.
J'ai donc reconstruit l'Elo d'avant la partie pour Chess.com avant de vous donner les fichiers (détail dans `parties.csv`).
Les colonnes `elo_joueur` et `elo_adverse` sont maintenant des Elo **avant la partie** sur les deux plateformes, et `elo_joueur_apres` garde la valeur d'après si vous voulez la comparer.
De même, dans `entrainement_ouvertures.csv`, j'ai converti les évaluations de pions en centipions, pour que le nom des colonnes dise la vérité.

## Les pièges à connaître avant de calculer quoi que ce soit

- **L'évaluation est du point de vue des Blancs, en centipions.** Un centipion (cp) vaut un centième de pion. `+100` veut dire que les Blancs sont mieux d'à peu près un pion, `-100` que les Noirs le sont, quelle que soit la couleur que je jouais. C'est vrai dans `coups_juges.eval_cp`. Dans `moments_critiques`, c'est mon point de vue à moi (positif = bien pour moi). Dans `entrainement_ouvertures`, `eval_avant_cp` et `eval_apres_cp` sont aussi du point de vue des Blancs, mais `perte_eval_cp` est du mien.
- **`coups_juges` ne contient que mes coups jugés mauvais.** Ni les coups de l'adversaire, ni mes bons coups. On ne peut donc pas y recalculer une précision ou une part de bons coups, seulement compter mes fautes.
- **L'Elo FFE et FIDE est une valeur du jour, pas un historique.** Il y a trois lignes par fédération, relevées les 16 et 17 novembre 2026. L'historique de mon classement n'existe que pour Lichess et pour les parties elles-mêmes.
- **Un Elo n'est jamais comparable d'une plateforme ou d'une cadence à l'autre.** Mon Elo Chess.com en bullet (jusqu'à 2 084) n'a rien à voir avec celui de Chess.com en blitz (jusqu'à 1 616).
- **Les dates sont en UTC et sans fuseau écrit.** `2023-07-09 06:31:48` est une heure UTC (Paris = UTC+1 en hiver, UTC+2 en été). Pandas les lit comme des dates « naïves » : ne les mélangez pas avec une heure locale. Les colonnes qui ne contiennent qu'un jour (`2026-10-23`) n'ont pas d'heure.
- **La précision est vide quand la partie n'est pas analysée, ou quand la phase est trop courte pour la calculer.** Ici, les 3 023 parties sont analysées, donc `parties.precision_joueur` est toujours remplie. Dans `phases.csv`, elle manque pour la phase `opening_theory` (toujours) et pour quelques phases trop courtes.
- **Les phases se chevauchent.** `opening_theory` est le début de `opening` : ne les additionnez pas. Pour compter les fautes par phase, prenez `opening`, `middlegame` et `endgame`.
- **`conseils.csv` est vide.** Il n'a que ses douze colonnes d'en-tête : mon carnet de coaching n'a pas été exporté.
- **Cadence** : c'est la famille de durée de la partie. `bullet` pour un temps de base de 30 s à 2 min, `blitz` de 3 à 5 min, `rapid` de 10 à 15 min, `classical` pour une cadence longue (une seule partie, importée). Elle est vide pour 48 parties : les parties par correspondance (un coup par jour, `controle_temps` de la forme `1/259200`), 3 parties Lichess sans pendule (`controle_temps` vaut `0`) et les parties importées à la main.
- **`nb_coups` ne veut pas dire la même chose partout.** Dans `parties`, c'est le nombre de coups complets (les deux camps jouent un coup). Dans `phases`, c'est le nombre de demi-coups de la phase, à un près, sauf pour `opening_theory`, où ce sont des coups complets (7 pour 14 demi-coups).
- **Un demi-coup s'appelle `ply`.** Il se compte à partir de 0. Les Blancs jouent les `ply` pairs, les Noirs les `ply` impairs, et `numero_coup` vaut `ply // 2 + 1`.
- **Les chiffres extrêmes ne sont pas des erreurs de saisie.** Au-delà de ±1 000 cp, la position est déjà gagnée ou perdue, ou un mat est annoncé. La formule de chances de gain (voir `conseils.md`) coupe à ±1 000.

## `parties.csv`

3 023 lignes, une par partie, du 9 juillet 2023 au 15 novembre 2026.
Exemple de ligne, copié du fichier (`P0865`) : une partie Lichess en blitz 3 minutes + 2 secondes, jouée avec les noirs et perdue par mat.

| colonne | sens (unité) | exemple |
|---|---|---|
| `partie_id` | identifiant anonyme de la partie | `P0865` |
| `date_jeu` | début de la partie (UTC) | `2025-09-21 21:46:23` |
| `plateforme` | `chesscom`, `lichess` ou `imported` (3 parties ajoutées à la main) | `lichess` |
| `cadence` | `bullet`, `blitz`, `rapid`, `classical`, vide si pas de cadence | `blitz` |
| `controle_temps` | réglage de la pendule : secondes de base, `+` secondes d'incrément, ou `1/86400` pour un coup par jour | `180+2` |
| `temps_initial_s` | temps de base (secondes) | `180` |
| `increment_s` | secondes ajoutées après chaque coup | `2` |
| `couleur` | ma couleur : `white` ou `black` | `black` |
| `resultat` | de mon point de vue : `win`, `draw`, `lose` | `lose` |
| `fin_partie` | `checkmate` (mat), `resign` (abandon), `timeout` (temps), `draw` (nulle), `other` | `checkmate` |
| `elo_joueur` | mon Elo sur la plateforme pour cette cadence, **avant la partie** (reconstruit pour Chess.com, voir plus bas) | `1664` |
| `elo_adverse` | l'Elo de l'adversaire, **avant la partie** (approximation pour Chess.com) | `1677` |
| `variation_elo` | gain ou perte d'Elo de la partie, remplie pour 3 008 parties | `-7` |
| `elo_joueur_apres` | mon Elo juste après la partie (`elo_joueur + variation_elo`) | `1657` |
| `elo_avant_reconstruit` | `oui` si j'ai reconstruit l'Elo d'avant (Chess.com), `non` sinon (Lichess et parties importées) | `non` |
| `adversaire` | hash de l'adversaire, le même hash pour un même adversaire | `adv_4743b1a9bc` |
| `nb_coups` | nombre de coups complets | `26` |
| `ouverture_eco` | code ECO de l'ouverture (une lettre A à E, deux chiffres) | `C11` |
| `ouverture_nom` | nom de l'ouverture, variante comprise | `French Defense: Classical Variation, Steinitz Variation` |
| `ouverture_famille` | nom de la famille, sans la variante | `French Defense` |
| `variante` | `standard`, ou `fromPosition` si la partie part d'une position donnée (3 parties) | `standard` |
| `hors_ligne` | `oui` pour une partie jouée sur échiquier réel (1 partie) | `non` |
| `analysee` | `oui` si le moteur a analysé la partie (toujours `oui` ici) | `oui` |
| `precision_joueur` | précision de mes coups, de 0 à 100 | `80.7692` |
| `acpl_joueur` | perte moyenne par coup, en centipions (plus bas = mieux) | `103.2692` |
| `precision_adverse`, `acpl_adverse` | les mêmes mesures pour l'adversaire | `81.4815`, `57.7778` |
| `imprecisions_joueur`, `erreurs_joueur`, `gaffes_joueur` | combien de coups de chaque gravité j'ai joués | `1`, `1`, `3` |
| `imprecisions_adverse`, `erreurs_adverse`, `gaffes_adverse` | la même chose pour l'adversaire | `4`, `0`, `1` |
| `temps_total_blanc_s`, `temps_total_noir_s` | temps passé par les Blancs, par les Noirs (secondes) | `120`, `158` |
| `temps_moyen_blanc_s`, `temps_moyen_noir_s` | temps moyen par coup (secondes) | `4.4444`, `6.0769` |

Ce qu'il faut savoir :

- Les temps sont **par couleur**, pas par joueur : pour mon temps, choisissez la colonne selon `couleur`. Ils manquent pour 49 parties, dont les 3 importées.
- **Elo avant la partie.** Sur Lichess, `elo_joueur`, `elo_adverse` et `variation_elo` sont ceux que ChessXP a gardés, tels quels (`elo_avant_reconstruit = non`). Sur Chess.com (`elo_avant_reconstruit = oui`), la valeur gardée est celle d'après la partie. Je l'ai remplacée comme ceci : pour chaque plateforme et chaque cadence, je trie les parties par date. Mon Elo d'avant est l'Elo d'après de la partie précédente de la même série, et `variation_elo` est la différence entre les deux.
- **L'Elo adverse de Chess.com est une approximation.** L'adversaire gagne ce que je perds, donc son Elo d'avant vaut son Elo d'après plus ma variation (somme nulle). Ce n'est pas tout à fait exact, parce que les deux joueurs ne gagnent ou ne perdent pas toujours le même nombre de points, mais l'écart reste de quelques points.
- **La première partie de chaque série n'a pas d'Elo d'avant.** `elo_joueur`, `elo_adverse` et `variation_elo` sont vides pour la première partie de chaque série Chess.com (4 parties : bullet, blitz, rapid et correspondance). Gardez `elo_joueur_apres` si vous avez besoin d'une valeur pour toutes.
- **Les parties par correspondance sont moins fiables.** Plusieurs sont jouées en même temps et finissent dans un autre ordre que celui de leur début, donc l'Elo d'avant reconstruit est plus bruité (corrélation de 0,61 entre sa variation et le résultat, contre 0,98 en blitz).
- `variation_elo` est vide pour 15 parties (les 4 premières de série Chess.com, 8 parties Lichess sans variation, les 3 importées). `elo_joueur_apres` est vide pour 11 parties.
- `elo_joueur` est vide pour 7 parties : les 4 premières de série Chess.com et les 3 importées. `elo_adverse` est vide pour 10 : ces 7, plus 3 parties Lichess. Les parties par correspondance ont un Elo, mais pas de cadence.
- Les parties sans ouverture reconnue ont `ouverture_*` vide (5 parties).
- Comptez les victoires avec `resultat`, pas avec `fin_partie`. `fin_partie == "checkmate"` vaut aussi pour mes défaites.
- Un score vaut 1 pour une victoire, 0,5 pour une nulle, 0 pour une défaite.

## `coups_juges.csv`

22 596 lignes, une par coup **à moi** que le moteur a jugé imprécision, erreur ou gaffe (4 671 erreurs, 7 030 gaffes, 10 895 imprécisions), dans 2 938 parties sur 3 023.
Exemple (`P0001`) : au huitième coup, avec les blancs, j'ai joué `d3` alors que `d4` était meilleur.

| colonne | sens (unité) | exemple |
|---|---|---|
| `partie_id` | la partie (lien vers `parties`) | `P0001` |
| `ply` | demi-coup, compté depuis 0 | `14` |
| `numero_coup` | numéro du coup dans la partie | `8` |
| `couleur` | ma couleur dans cette partie | `white` |
| `coup` | le coup que j'ai joué, en notation algébrique (`Nf3` = cavalier en f3, `x` = capture, `+` = échec) | `d3` |
| `phase` | `opening`, `middlegame`, `endgame` | `opening` |
| `eval_cp` | évaluation de la position après mon coup, **point de vue des Blancs**, en cp | `-374` |
| `variation_eval_cp` | ce que mon coup m'a fait perdre, en cp, toujours positif | `92` |
| `meilleur_coup` | le coup que le moteur préférait (vide 2 198 fois) | `d4` |
| `jugement` | `inaccuracy` (imprécision), `mistake` (erreur), `blunder` (gaffe) | `inaccuracy` |
| `temps_restant_s` | temps qu'il me restait après le coup (secondes) | `10` |
| `temps_passe_s` | temps passé sur le coup (secondes) | vide ici, `2` ailleurs |
| `categorie` | `tactical` (une tactique est en jeu) ou `strategic` | `strategic` |
| `sous_type` | `allowed_tactic` (j'ai laissé une tactique à l'adversaire), `missed_tactic` (j'ai raté la mienne), vide si stratégique | `allowed_tactic` |
| `mecanisme` | ce qui se joue : `material`, `mate`, `promotion`, `positional` | `positional` |

Ce qu'il faut savoir :

- Seuls mes coups jugés mauvais sont là (voir les pièges plus haut). Une partie sans faute n'a aucune ligne.
- Le même nombre de centipions ne donne pas le même jugement : perdre 150 cp dans une position égale est une erreur, perdre 200 cp quand je suis déjà à +800 n'est rien. La gravité dépend des chances de gain, pas des centipions (voir `conseils.md`).
- `eval_cp` est d'abord à lire en changeant de signe si je joue les noirs : après un coup noir, un `eval_cp` positif veut dire que c'est mauvais pour moi.
- `temps_restant_s` et `temps_passe_s` manquent pour les parties sans pendule enregistrée (30 et 204 lignes).

## `phases.csv`

11 089 lignes. Une partie a deux à quatre lignes : `opening_theory`, `opening`, `middlegame` (si le milieu de jeu est atteint) et `endgame` (si la partie atteint la finale). 2 120 parties ont les quatre, 803 en ont trois, 100 en ont deux.
Exemple (`P0865`, ouverture) : les 18 premiers demi-coups, une imprécision de ma part.

| colonne | sens (unité) | exemple |
|---|---|---|
| `partie_id` | la partie | `P0865` |
| `phase` | `opening_theory` (la partie « théorique » du début), `opening`, `middlegame`, `endgame` | `opening` |
| `ply_debut`, `ply_fin` | premier et dernier demi-coup de la phase | `0`, `17` |
| `nb_coups` | nombre de **demi-coups** de la phase, à un près ; pour `opening_theory`, nombre de coups complets (7 pour 14 demi-coups) | `18` |
| `imprecisions_joueur`, `erreurs_joueur`, `gaffes_joueur` | mes fautes dans la phase | `1`, `0`, `0` |
| `imprecisions_adverse`, `erreurs_adverse`, `gaffes_adverse` | celles de l'adversaire | `1`, `0`, `0` |
| `precision_joueur`, `precision_adverse` | précision dans la phase, de 0 à 100 | `88.8889`, `88.8889` |
| `acpl_joueur`, `acpl_adverse` | perte moyenne par coup dans la phase (cp) | `9.2222`, `21.6667` |
| `temps_joueur_s`, `temps_adverse_s` | temps passé dans la phase (secondes) | `28`, `22` |
| `temps_moyen_joueur_s`, `temps_moyen_adverse_s` | temps moyen par coup (secondes) | `3.1111`, `2.4444` |
| `plies_theorie_suivis` | demi-coups joués selon la théorie des ouvertures (ligne `opening_theory` seulement) | `0` |
| `ply_premiere_deviation` | premier demi-coup hors théorie (ligne `opening_theory` seulement) | `12` |
| `type_finale` | genre de finale à l'entrée : `rook-endgame` (tours), `pawn-endgame` (pions), `queen-endgame`… (ligne `endgame` seulement) | vide ici |
| `eval_entree_finale` | évaluation à l'entrée de la finale (cp, ligne `endgame`) | `-744` |
| `type_finale_dominant` | genre de finale le plus fréquent de la partie | vide ici |
| `variation_eval_max`, `variation_eval_moy`, `eval_debut_ouverture`, `eval_fin_ouverture` | colonnes toujours vides dans cet export | vide |

Ce qu'il faut savoir :

- `nb_coups` compte ici des demi-coups, à un près du nombre de demi-coups entre `ply_debut` et `ply_fin`, alors que `parties.nb_coups` compte des coups complets. Exception : pour `opening_theory`, c'est un nombre de coups complets (7 pour 14 demi-coups), ne le comparez pas aux autres phases.
- Ne sommez pas les quatre phases : `opening_theory` est incluse dans `opening`.
- Les gaffes, erreurs et imprécisions par phase de `phases.csv` et de `coups_juges.csv` sont presque les mêmes (903 gaffes en ouverture dans `coups_juges`, 907 dans `phases`) : les limites des phases diffèrent un peu selon le fichier. Pour un chiffre à citer, prenez toujours la même source.
- Le point de vue de `eval_entree_finale` n'est pas vérifié : ne l'utilisez pas sans le contrôler d'abord sur une partie.

## `moments_critiques.csv`

4 278 lignes, dans 2 074 parties : une sélection de mes coups à forte perte (au moins 50 cp), avec la position avant le coup.
Exemple (`P0004`) : avec les noirs, j'ai joué `Nf5` alors que `cxd4` était meilleur ; je passe de +40 à -119.

| colonne | sens (unité) | exemple |
|---|---|---|
| `partie_id` | la partie | `P0004` |
| `date_jeu` | début de la partie (UTC) | `2023-07-14 18:16:53` |
| `phase` | `opening`, `middlegame`, `endgame` | `middlegame` |
| `ply` | demi-coup (depuis 0) | `15` |
| `numero_coup` | numéro du coup | `8` |
| `couleur` | ma couleur | `black` |
| `coup` | le coup que j'ai joué | `Nf5` |
| `meilleur_coup` | le meilleur coup selon le moteur (vide 141 fois) | `cxd4` |
| `fen_avant` | la position avant mon coup, au format FEN (une ligne de texte qui décrit toutes les pièces) | `r3kb1r/pp1bnppp/1qn1p3/2ppP3/P2P4/2P2N2/1P2BPPP/RNBQ1RK1 b kq - 4 8` |
| `eval_avant_cp` | évaluation avant mon coup, **de mon point de vue** (cp) | `40` |
| `eval_apres_cp` | évaluation après mon coup, de mon point de vue | `-119` |
| `perte_eval_cp` | `eval_avant_cp - eval_apres_cp`, toujours positif | `159` |
| `mate_avant`, `mate_apres` | si un mat était annoncé : nombre de coups avant le mat, signé (vide sinon) | vide ici |

Ce qu'il faut savoir :

- Les évaluations sont de mon point de vue, **à l'inverse de** `coups_juges.eval_cp` (Blancs). Si vous joignez les deux, pour mes coups noirs les signes sont opposés.
- Cette sélection n'est pas un doublon de `coups_juges` : seuls 4 271 des 4 278 moments y sont retrouvés (les 7 autres n'ont pas de ligne correspondante).
- `fen_avant` est la seule colonne qui permet de reconstituer la position (avec la bibliothèque `python-chess`) : c'est ce qui permet de repérer des motifs.

## `elo.csv`

4 043 lignes de trois sortes (colonne `origine`).
Exemple (`origine = historique`) : le 19 mars 2023, 1 605 en blitz sur Lichess.

| colonne | sens (unité) | exemple |
|---|---|---|
| `date` | jour, ou jour et heure (UTC) pour `partie` | `2023-03-19` |
| `partie_id` | la partie, seulement pour `origine = partie` | `P0001` |
| `source` | `lichess`, `chesscom`, `ffe`, `fide` | `lichess` |
| `cadence` | `blitz`, `bullet`, `rapid`, `classical` | `blitz` |
| `elo` | le classement | `1605` |
| `origine` | `partie` (l'Elo noté pendant une partie, 3 020 lignes), `historique` (la courbe de Lichess, 1 017 points), `actuel` (FFE et FIDE, 6 lignes) | `historique` |

Ce qu'il faut savoir :

- L'Elo FFE et FIDE est une seule valeur du jour (`actuel`), pas une courbe.
- Les valeurs `partie` sont l'Elo que ChessXP a noté pour la partie : avant la partie sur Lichess (`parties.elo_joueur`), **après** la partie sur Chess.com (`parties.elo_joueur_apres`). Ne les comptez pas deux fois, et ne les utilisez pas pour prédire le résultat d'une partie Chess.com.
- `cadence` est vide pour 46 lignes (parties par correspondance).
- Lichess `historique` s'arrête au 15 novembre 2026.

## `puzzles.csv`

726 lignes : une par tentative de problème tactique (« trouve le meilleur coup »), du 9 février au 15 novembre 2026.
Exemple : un problème de mat en un coup résolu en 8,4 secondes.

| colonne | sens (unité) | exemple |
|---|---|---|
| `date_essai` | moment de la tentative (UTC) | `2026-02-09 03:12:23` |
| `partie_id` | partie dont vient le problème, remplie une seule fois | vide ici |
| `source` | `lichess` (problème de la base Lichess) ou `game_analysis` (tiré d'une de mes parties) | `lichess` |
| `resolu` | `oui` ou `non` | `oui` |
| `mode` | `normal` ou `calculation` (je dois écrire toute la ligne avant de voir la réponse) | `normal` |
| `temps_ms` | durée de la tentative (millisecondes) | `8447` |
| `nb_coups_joues` | nombre de coups que j'ai joués | `1` |
| `nb_coups_avant_erreur` | nombre de coups corrects avant mon erreur, vide si résolu | vide ici |
| `ply_source`, `type_erreur` | pour le problème tiré de ma partie : le demi-coup et la gravité de ma faute | vide ici |
| `elo_puzzle` | difficulté du problème (même échelle qu'un Elo) | `1036` |
| `score_popularite` | popularité du problème, de 0 à 100 | `0` |
| `nb_parties_jouees` | nombre de fois que le problème a été joué dans la base | `1187` |
| `themes` | thèmes tactiques, séparés par des virgules (`mateIn1` = mat en 1 coup, `fork` = fourchette) | `oneMove, mateIn1, master, middlegame` |
| `ouvertures` | ouvertures liées au problème, vide le plus souvent | vide ici |

Ce qu'il faut savoir :

- 362 problèmes résolus sur 726 tentatives, soit un peu moins de la moitié. Un même problème peut avoir été tenté plusieurs fois, on ne peut pas le savoir (pas d'identifiant du problème).
- Le mode `calculation` n'apparaît qu'une fois.
- `temps_ms` va de 1,6 seconde à plus d'une heure (4 153 300 ms) : il y a des onglets restés ouverts, passez par la médiane.

## `puzzle_elo.csv`

503 lignes : mon classement aux problèmes après chaque tentative.
Exemple : de 1 200 à 1 227 après un problème de difficulté 1 330, résolu.

| colonne | sens (unité) | exemple |
|---|---|---|
| `date` | moment (UTC) | `2026-03-01 13:04:21` |
| `elo_avant`, `elo_apres` | mon classement aux problèmes avant et après | `1200`, `1227` |
| `variation_elo` | `elo_apres - elo_avant` | `27` |
| `elo_puzzle` | difficulté du problème | `1330` |
| `resolu` | `oui` ou `non` | `oui` |

Ce qu'il faut savoir : il y a moins de lignes que dans `puzzles.csv` (503 contre 726). Les deux fichiers ne se recouvrent pas ligne à ligne, ne les joignez pas.

## `entrainement_ouvertures.csv`

7 509 lignes, 189 séances (`S0001` à `S0189`), du 14 avril au 9 novembre 2026. Une ligne est un coup travaillé pendant une séance d'entraînement d'ouvertures : j'y rejoue une ligne théorique, et le moteur relève ma première erreur.
Exemple (`S0003`) : en jouant `Bc4` dans la Sicilienne Kalashnikov, j'ai perdu 29 centipions (0,29 pion) par rapport à `Bb5`.

| colonne | sens (unité) | exemple |
|---|---|---|
| `date_session` | moment du coup (UTC) | `2026-04-23 08:26:16` |
| `session` | identifiant de la séance | `S0003` |
| `ouverture_eco`, `ouverture_nom` | l'ouverture travaillée | `B32`, `Sicilian Defense: Kalashnikov Variation` |
| `couleur` | ma couleur | `white` |
| `coup` | le coup travaillé | `Bc4` |
| `numero_premiere_erreur` | numéro du coup de la première erreur de la ligne, répété sur chaque ligne, vide si pas d'erreur (824 lignes) | `3` |
| `numero_fin` | numéro du coup où la ligne s'arrête, vide 89 % du temps | vide ici |
| `coup_erreur`, `meilleur_coup` | mon coup d'erreur et le coup préférable | `Bc4`, `Bb5` |
| `eval_avant_cp`, `eval_apres_cp` | évaluation avant et après, **en centipions**, **point de vue des Blancs** (entiers, arrondis depuis une évaluation en pions de ChessXP) | `33`, `4` |
| `perte_eval_cp` | variation de l'évaluation **de mon point de vue**, en centipions : `eval_apres_cp - eval_avant_cp` avec les blancs, `eval_avant_cp - eval_apres_cp` avec les noirs. **Négatif quand je perds** (29 lignes positives sur 201 sont des gains) | `-29` |
| `jugement` | gravité, rempli pour 12 lignes seulement | vide ici |
| `analyse_terminee` | `oui` quand le moteur a fini d'analyser l'erreur | `oui` |

Ce qu'il faut savoir :

- Les colonnes `eval_*_cp` et `perte_eval_cp` sont en centipions (je les ai converties depuis les pions : `0.33` pion est devenu `33`). Le signe de `perte_eval_cp` est l'inverse de celui de `moments_critiques` : ici négatif quand je perds, là-bas positif.
- Les colonnes de l'erreur sont vides pour 7 306 lignes sur 7 509 : la plupart des lignes n'ont pas d'erreur relevée.
- Pour compter les séances, comptez `session` distinctes (189), pas les lignes.

## `plans_du_jour.csv`

25 lignes, un plan par jour du 23 octobre au 16 novembre 2026 : ce que ChessXP me conseille de travailler ce jour-là.
Exemple (23 octobre 2026) : le plan porte sur la Défense Française et la Défense Benoni avec les noirs, sur la Défense Scandinave avec les blancs, plus des problèmes sur le thème `sacrifice`.

| colonne | sens (unité) | exemple |
|---|---|---|
| `date_plan` | le jour du plan | `2026-10-23` |
| `periode_debut`, `periode_fin` | la période de parties prise en compte (30 jours) | `2026-09-24`, `2026-10-23` |
| `provisoire` | `oui` si le plan est provisoire (toujours `non`) | `non` |
| `nb_series` | nombre de séries supplémentaires (« continuer l'entraînement ») | `0` |
| `bonus_xp` | points bonus (toujours 0 ici) | `0` |
| `taches` | les tâches du jour, séparées par ` \| ` ; chaque tâche est une suite `clé=valeur` séparées par des virgules | `color=black, draws=0, games=29, group=later, label=Défense Française, ...` |
| `extras` | les tâches de rechange, même format | `color=white, draws=0, games=5, group=repair, label=Défense Caro-Kann, ...` |

Ce qu'il faut savoir :

- `taches` et `extras` sont du texte à découper (`split(" | ")` puis `split(", ")`) : ce n'est pas un tableau.
- Le champ `kind=` donne le type de tâche : `gm_openings` (jouer les ouvertures comme les grands maîtres), `puzzles` (problèmes sur un thème), `replay` (rejouer une partie), `endgames` (finales). Sans `kind`, c'est une tâche d'ouverture.
- `group` vaut `repair` (à réparer), `stabilize` (à stabiliser), `later` (plus tard) ou `protect` (à garder). `score_rank` est le nombre de parties multiplié par un poids : 4 pour `repair`, 3 pour `stabilize`, 2 pour `later`, 1 pour `protect`.
- `score` est mon score dans cette ouverture sur la période (1 = tout gagné), `weighted_accuracy` ma précision et `reference` la précision de référence (93).

## `revues.csv`

3 lignes : une revue écrite par le coach pour trois de mes parties (`P2972`, `P2994`, `P3009`), les 12 et 14 novembre 2026.
Exemple : « La partie se perd au coup 12 : la poussée [[e5]] perd un pion… »

| colonne | sens | exemple |
|---|---|---|
| `partie_id` | la partie | `P2972` |
| `date_revue` | moment de la revue (UTC) | `2026-11-14 21:30:27` |
| `source` | qui l'a écrite | `coach` |
| `resume` | résumé de la partie en quelques phrases | `La partie se perd au coup 12 : ...` |
| `lecons` | leçons à retenir, une par ` \| `, avec le demi-coup concerné | `ply=22, text=Avant une poussée qui ouvre le centre ...` |
| `coach` | le rapport du coach : thèmes, moments clés, recommandations, mis à plat en `clé=valeur` | `calculation=comment=La plupart de tes erreurs sont punies à 3 coups ou plus...` |

Ce qu'il faut savoir : dans le texte, `[[e5]]` désigne un coup et `[[ev:+49]]` une évaluation en centipions, des balises que l'interface remplace par un lien ou une pastille. Trois lignes ne suffisent pas à faire une statistique, c'est une illustration.

## `conseils.csv`

0 ligne. Les colonnes (`date_conseil`, `type`, `titre`, `texte`, `pourquoi`, `tags`, `periode_debut`, `periode_fin`, `statut`, `source`, `preuves`, `liens`) décrivent mon carnet de coaching, qui n'a pas été exporté. Un `pd.read_csv` donne un tableau vide : c'est normal, ce n'est pas un bug de lecture.
