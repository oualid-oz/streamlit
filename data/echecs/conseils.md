# Comment ChessXP transforme une évaluation du moteur en conseil

ChessXP est l'outil d'entraînement où j'ai analysé mes parties. Un moteur d'échecs (Stockfish) lui donne un seul nombre par position. Tout le reste, les gaffes, les phases, les motifs, le plan du jour, ce sont des règles écrites à la main par-dessus ce nombre. Voici ces règles, dans l'ordre où elles s'enchaînent. Vous n'avez pas besoin de jouer aux échecs pour les suivre.

## 1. Le moteur donne un nombre, en centipions

Le moteur évalue la position après chaque coup. L'évaluation se compte en centipions (cp), un centième de pion. `+100` veut dire que les Blancs sont mieux d'à peu près un pion, `-300` que les Noirs ont l'équivalent d'une pièce de plus. Elle est toujours donnée du point de vue des Blancs, quelle que soit ma couleur : si je joue les Noirs, un nombre positif est mauvais pour moi.

Quand un mat est en vue, le nombre devient très grand : un mat en n coups vaut `(21 - n) × 100` cp, avec n plafonné à 10.

## 2. Du centipion aux chances de gain

Cent centipions ne pèsent pas pareil selon la position. Être à +100 quand tout est égal compte beaucoup, être à +800 et passer à +700 ne change presque rien : la partie est déjà gagnée. ChessXP convertit donc le centipion en chances de gain, avec la formule de Lichess :

```
chances = 2 / (1 + exp(-0.00368208 × cp)) - 1
```

Pour une évaluation sans mat, le cp est d'abord ramené entre -1 000 et +1 000. Le résultat va de -1 (partie perdue) à +1 (partie gagnée), 0 est une position égale.

| évaluation | chances (de -1 à +1) | probabilité de gagner |
|---|---|---|
| 0 cp | 0 | 50,0 % |
| +100 cp | 0,18 | 59,1 % |
| +200 cp | 0,35 | 67,6 % |
| +300 cp | 0,50 | 75,1 % |
| +500 cp | 0,73 | 86,3 % |
| +800 cp | 0,90 | 95,0 % |
| +1 000 cp | 0,95 | 97,5 % |

La probabilité de gagner est `(chances + 1) / 2`.

## 3. Les seuils : imprécision, erreur, gaffe

Pour chacun de mes coups, ChessXP calcule les chances de gain avant le coup, puis après, de mon point de vue. La différence est la perte.

- une perte de 0,10 ou plus est une **imprécision** (5 points de probabilité de gagner)
- une perte de 0,20 ou plus est une **erreur** (10 points)
- une perte de 0,30 ou plus est une **gaffe** (15 points)

Deux exemples avec les chiffres du tableau. Dans une position égale, un coup qui me fait passer de 0 à -150 cp perd 0,27 de chances : c'est une erreur. Dans une position où je gagne largement, passer de +800 à +600 cp perd 0,098 de chances, même pas une imprécision, alors que la perte en centipions (200) est la même que pour une grosse erreur. Voilà pourquoi `coups_juges.csv` contient des gaffes de 164 cp et des imprécisions de plus de 1 000 cp.

## 4. Les grosses erreurs : 200 centipions ou plus

Une erreur ou une gaffe est dite **grosse** quand mon coup fait perdre au moins 200 cp d'évaluation, ou quand il touche à un mat. C'est le filtre qui sert aux rapports sur le milieu de partie (section 7).

ChessXP range aussi chaque faute dans une famille, d'après ce qui se passait sur l'échiquier :

- **pièce laissée en prise** : j'ai perdu du matériel que l'adversaire a pu prendre
- **gain raté** : une prise ou une combinaison gagnante était là et je ne l'ai pas jouée
- **mat raté** : un mat existait et je ne l'ai pas vu
- **mat permis** : mon coup donne un mat à l'adversaire
- **autre**, quand ce n'est aucun de ces cas

## 5. Comment une partie est découpée en phases

Une partie d'échecs se joue en trois temps : l'ouverture (on sort les pièces), le milieu de partie (on se bat) et la finale (il reste peu de pièces). ChessXP applique l'algorithme de Lichess, qui ne regarde que l'échiquier, jamais la numérotation des coups.

- Le **milieu de partie** commence à la première position qui remplit une de ces trois conditions : il reste 10 pièces ou moins (dames, tours, fous, cavaliers des deux camps, sans les pions ni les rois) ; ou un des deux camps a moins de 4 pièces sur sa rangée de départ ; ou un « score de mélange » dépasse 150. Ce dernier mesure à quel point les pièces des deux camps se sont mêlées au centre de l'échiquier.
- La **finale** commence à la première position où il reste 6 pièces ou moins (même comptage).
- Tout ce qui précède le milieu de partie est l'**ouverture**. Une ligne en plus, `opening_theory`, couvre le tout début de l'ouverture (au plus 14 demi-coups dans ces fichiers) et note jusqu'où j'ai suivi la théorie. Sa définition ne vient pas de l'algorithme de Lichess.

Une partie très courte n'a pas de milieu de partie, ni de finale : c'est pourquoi `phases.csv` n'a pas toujours quatre lignes par partie.

## 6. Les schémas d'erreur en ouverture

ChessXP regarde, pour chaque partie, **ma première faute en ouverture** (imprécision, erreur ou gaffe), et la classe d'après le type de coup. Quand plusieurs types s'appliquent, le premier de cette liste l'emporte :

1. **dame sortie trop tôt** : un coup de dame avant le coup numéro 10
2. **coup de roi**, roque compris
3. **échange** : je prends une pièce de valeur égale ou supérieure à celle qui prend
4. **pion de bord** : un pion qui part d'une des colonnes a, b, g ou h
5. **poussée de pion** : un pion qui arrive sur la quatrième rangée ou plus loin (la cinquième ou plus loin pour les Noirs, comptée du côté des Blancs)
6. **développement** : un fou ou un cavalier qui quitte sa case de départ
7. **repli** : une pièce qui recule vers sa rangée de départ
8. **autre**

Le rapport regroupe ensuite ces premières fautes par type et par couleur : combien de parties, quelle part du total, quelle perte moyenne en centipions, quelles ouvertures et quels coups reviennent le plus.

## 7. Les motifs du milieu de partie

Pour le milieu de partie, ChessXP prend mes grosses erreurs (section 4) et cherche pourquoi chacune a perdu. Il regarde la position après mon coup et le premier coup de la réfutation, c'est-à-dire la meilleure réponse de l'adversaire. Il pose des étiquettes, et regroupe les fautes par famille (section 4) et par étiquette :

- **une pièce à moi est en prise et pas défendue**
- **une pièce à moi est clouée** (elle ne peut pas bouger sans exposer mon roi)
- **mon roi va se mettre en échec** : je le déplace (sans roquer) sur une case que la réfutation attaque
- **la réfutation prend quelque chose**
- **la réfutation donne échec**
- **la réfutation est une fourchette** : une même pièce attaque deux de mes pièces qui valent chacune au moins un cavalier
- **la réfutation attaque ma dame**

Une faute peut porter plusieurs étiquettes et compte une fois sous chacune : les parts peuvent donc dépasser 100 %. Une faute sans étiquette est rangée sous « aucun motif ». Le même regroupement existe avec les thèmes des problèmes de Lichess (fourchette, clouage, mat en deux…), pour renvoyer vers des problèmes à travailler.

## 8. Les erreurs par famille d'ouvertures

ChessXP range chaque partie dans une famille d'ouvertures (la Défense Française, la Sicilienne… sans la variante) et liste les familles où j'ai des parties analysées, de la plus jouée à la moins jouée. Pour une famille, il remonte ensuite les lignes de coups où je refais les mêmes fautes : ce sont celles-là qu'on peut apprendre par cœur, alors qu'une faute isolée ne s'apprend pas.

## 9. Les moments clés du coach de partie

Pour la revue d'une partie, le coach ne regarde pas tous les coups. Il retient les coups jugés mauvais :

- les miens, les 20 qui ont fait perdre le plus
- ceux de l'adversaire, seulement ses erreurs et ses gaffes, les 6 plus lourdes (une partie se perd souvent après une faute de l'adversaire que je n'ai pas exploitée)

Pour chacun, il garde l'évaluation avant et après, le coup préféré par le moteur, la ligne qui réfute le coup (coupée à 8 demi-coups), et le nombre de coups avant que la meilleure ligne ne gagne du matériel pour de bon. Une position est dite **perdue** quand je suis à 300 cp ou plus en dessous. Le texte de la revue (`revues.csv`) est écrit à partir de ces faits.

## 10. Le plan du jour

Le plan du jour répond à « qu'est-ce que je travaille aujourd'hui ? ». Il part d'un tableau qui, pour chaque ouverture et chaque couleur, donne les parties jouées, le score et la précision, sur deux fenêtres : les 7 derniers jours et les 30 derniers jours. Chaque ligne reçoit un groupe qui dit quoi en faire, et un poids :

| groupe | sens | poids |
|---|---|---|
| `repair` | à réparer | 4 |
| `stabilize` | à stabiliser | 3 |
| `later` | à voir plus tard | 2 |
| `protect` | à garder en l'état | 1 |

Les poids se déduisent de `score_rank / games` dans `plans_du_jour.csv`. Le rang d'une ligne est son poids multiplié par le nombre de parties : une ouverture que je joue souvent et qui va mal passe en premier. Seules les lignes avec un groupe et un poids positif sont candidates.

La sélection prend, par défaut, **trois tâches**. Elle commence par la fenêtre la plus courte, trie par rang décroissant, puis par nombre de parties, puis par groupe d'ouvertures, et met les Blancs avant les Noirs en cas d'égalité. Elle laisse de côté les ouvertures déjà proposées les deux jours précédents, tant qu'il en reste d'autres. Les candidates qui n'ont pas été retenues deviennent des tâches de rechange, dix au plus. À côté des ouvertures, un plan peut contenir des problèmes sur un thème, des finales ou la reprise d'une partie.

## Ce que vous pouvez refaire avec ces fichiers

Les chances de gain et les seuils se recalculent depuis `coups_juges.csv` : l'évaluation après le coup est `eval_cp` (multipliée par -1 si `couleur` vaut `black`), l'évaluation avant est celle-ci plus `variation_eval_cp`, et le jugement retombe sur `jugement` pour 98 coups sur 100 (les 2 % d'écart viennent surtout des mats et des évaluations au-delà de ±1 000). Les grosses erreurs sont les lignes où `jugement` vaut `mistake` ou `blunder` et où, en plus, `variation_eval_cp` vaut au moins 200 ou `mecanisme` vaut `mate` ; les familles de fautes se lisent dans `sous_type` (laissée en prise ou gain raté) croisé avec `mecanisme`. Les fautes par phase se comptent avec `phase`, mais le découpage lui-même ne se refait pas, car il demande les positions (seul `moments_critiques.csv` en donne une, `fen_avant`, avec la bibliothèque `python-chess`). La première faute d'ouverture de chaque partie est la première ligne de `coups_juges` avec `phase` égale à `opening` ; on peut en trier une partie des types depuis le coup écrit (`coup` commence par `Q` avant le coup 10 pour une dame sortie, par `K` ou `O-O` pour un coup de roi, par `a`, `b`, `g` ou `h` pour un pion de bord, en respectant l'ordre de la section 6), mais l'échange, le développement et le repli demandent la position. Les motifs du milieu de partie se refont avec `fen_avant`, pour les 4 278 moments seulement. Le classement des familles d'ouvertures se refait avec `ouverture_famille`, `resultat` et `couleur` dans `parties.csv`. Les moments clés se retrouvent en triant mes coups d'une partie par `variation_eval_cp`, et une position « perdue » est une ligne de `moments_critiques` où `eval_apres_cp` est à -300 ou moins. Le plan du jour se lit dans `plans_du_jour.csv` (découpez `taches`), mais pas le tableau de départ, qui n'est pas dans les fichiers.

## Glossaire

- **Elo** : un nombre qui classe les joueurs, plus il est haut plus on joue bien. Il se compte par plateforme et par cadence, on ne compare pas des Elo de deux listes différentes. Mon premier Elo Chess.com en blitz était de 1 060.
- **cadence** : la vitesse de la partie. `bullet` pour moins de 3 minutes par joueur, `blitz` de 3 à 5 minutes, `rapid` de 10 à 15 minutes, `classical` pour une partie longue. Les parties par correspondance (un coup par jour) n'ont pas de cadence dans ces fichiers.
- **gaffe** : un coup qui fait perdre au moins 0,30 de chances de gain (15 points de probabilité). En dessous, `erreur` à partir de 0,20 et `imprécision` à partir de 0,10.
- **phase** : un des trois temps d'une partie, ouverture, milieu de partie, finale.
- **ACPL** : average centipawn loss, la perte moyenne par coup en centipions. Plus il est bas, plus mes coups sont proches de ceux du moteur.
- **précision** : une note de 0 à 100 qui résume la perte de chances de gain, coup après coup. Plus elle est haute, moins j'ai perdu.
- **fork**, fourchette : un seul coup d'une pièce qui en attaque deux à la fois, l'adversaire ne peut en sauver qu'une.
- **pin**, clouage : une pièce qui ne peut pas bouger parce qu'elle protège une pièce plus précieuse derrière elle, en général le roi.
- **mateIn2**, mat en deux : un thème de problème où les Blancs ou les Noirs peuvent forcer le mat en deux coups, quoi que fasse l'adversaire. On trouve aussi `mateIn1` et `mateIn3`.
