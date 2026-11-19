# Cas 5 · Immobilier autour d'Orléans

[← les six cas](README.md) · [toutes les données](../../data/projets/LISEZMOI.md)

## Le contexte

Chaque vente immobilière en France est enregistrée par l'administration fiscale et publiée : c'est DVF (demandes de valeurs foncières), qu'Etalab republie avec la position de chaque bien. Ici, les ventes d'un seul logement (maison ou appartement) dans le Loiret de 2021 à 2025. Un couple qui veut acheter se demande où chercher avec son budget, et si un prix demandé est raisonnable.

- **Qui utilise l'appli** : un couple qui cherche à acheter
- **La décision à éclairer** : dans quelle commune ou quel quartier chercher, pour quel budget
- **Drill-down attendu** : commune, section cadastrale, vente

## Les données

| | |
|---|---|
| Fichier | [`immobilier.parquet`](../../data/projets/immobilier.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/immobilier.parquet)) |
| Lignes | 46 022 ventes (32 820 maisons, 13 202 appartements), 325 communes |
| Période | 02/01/2021 → 31/12/2025 |
| Source | [DVF géolocalisées (Etalab)](https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/) |
| Licence | Licence Ouverte 2.0 (Etalab) : citer « DGFiP, DVF » |

```python
import pandas as pd
df = pd.read_parquet("data/projets/immobilier.parquet")
```

| Colonne | Ce qu'elle contient |
|---|---|
| `id_mutation, date_mutation, annee` | identifiant et date de la vente |
| `valeur_fonciere` | prix de vente, en euros (terrain compris pour une maison) |
| `type` | « Maison » ou « Appartement » |
| `surface_reelle_bati` | surface habitable, en m² |
| `nombre_pieces_principales` | nombre de pièces |
| `prix_m2` | valeur_fonciere / surface_reelle_bati |
| `surface_terrain` | surface du terrain, en m² |
| `code_commune, nom_commune, code_postal` | la commune |
| `section` | section cadastrale : un quartier, à l'échelle de quelques rues |
| `longitude, latitude` | position du bien |


## À savoir avant de commencer

- filtres déjà appliqués : ventes d'un seul logement (une mutation = une ligne), prix 10 k-2 M euros, 9-400 m2, 300-8000 euros/m2. Décidez les vôtres et dites-les dans l'appli
- DVF ne dit rien de l'état du bien, de l'étage ni du DPE : deux biens au même prix au m² ne se valent pas forcément
- comparez des médianes, pas des moyennes : quelques ventes chères tirent la moyenne vers le haut
- une commune avec cinq ventes ne donne pas un prix fiable : affichez le nombre de ventes à côté du prix
- les adresses ont été retirées : la section cadastrale est le niveau le plus fin

## Questions métier possibles

Des pistes, pas une liste à cocher : votre appli en soutient une ou deux, pour la décision ci-dessus.

1. Quel prix médian au m² par commune, maison contre appartement ?
2. Avec 250 000 €, quelles communes proposent une maison d'au moins 100 m² ?
3. Les prix ont-ils baissé depuis la hausse des taux en 2022, et où ?
4. Où se vend-il le plus de logements (un marché où l'on trouve vite) ?
5. Dans Orléans, quel écart de prix entre les sections cadastrales ?
6. Un prix demandé est-il au-dessus ou au-dessous des ventes comparables (même commune, même type, surface proche) ?
7. Combien coûte une pièce de plus, à surface égale ?

## Pour aller plus loin

- **ML** : estimer le prix d'un bien selon la surface, le type et la commune : un formulaire « et si ? »
- **LLM** : expliquer en clair l'écart entre un prix demandé et les ventes comparables

## Questions ouvertes sur les données

Des questions précises, à trancher avec le fichier, chiffres à l'appui. Les réponses ne sont pas données : c'est votre première exploration.

1. De combien le prix au m² a-t-il bougé entre 2021 et 2025, commune par commune ?
2. Les petites surfaces sont-elles plus chères au m² ?
3. Dans quelles communes une maison se vend-elle sous 1 500 €/m² ?
4. Le nombre de ventes par an baisse-t-il depuis 2022 ?
5. À surface égale, un grand terrain fait-il monter le prix d'une maison ?
6. Dans Orléans, quelles sections cadastrales sont les plus chères ?
