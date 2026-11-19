# Cas 6 · Location courte durée à Lyon

[← les six cas](README.md) · [toutes les données](../../data/projets/LISEZMOI.md)

## Le contexte

Inside Airbnb relève les annonces publiques d'Airbnb ville par ville. Ici, Lyon au 19/09/2026 : 9 201 annonces dans les 9 arrondissements, avec le prix, la capacité, les notes et une estimation de l'occupation, plus un échantillon de 20 000 avis écrits par les voyageurs. Un propriétaire qui met son appartement en location veut savoir à quel prix le proposer.

- **Qui utilise l'appli** : un propriétaire qui met un appartement en location
- **La décision à éclairer** : à quel prix le proposer, selon le quartier et la capacité
- **Drill-down attendu** : arrondissement, type de logement, annonce

## Les données

| | |
|---|---|
| Fichier | [`airbnb_lyon.parquet`](../../data/projets/airbnb_lyon.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/airbnb_lyon.parquet)), [`airbnb_lyon_reviews.parquet`](../../data/projets/airbnb_lyon_reviews.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/airbnb_lyon_reviews.parquet)) |
| Lignes | 9 201 annonces ; 20 000 avis sur 4 082 annonces |
| Période | relevé du 19/09/2026 ; avis du 06/01/2012 au 18/09/2026 |
| Source | [Inside Airbnb, Lyon](https://insideairbnb.com/get-the-data/) |
| Licence | CC BY 4.0 : citer « Inside Airbnb » dans l'appli |

```python
import pandas as pd
df = pd.read_parquet("data/projets/airbnb_lyon.parquet")
```

| Colonne | Ce qu'elle contient |
|---|---|
| `id_annonce, titre` | l'annonce |
| `quartier` | l'arrondissement (1er à 9e) |
| `latitude, longitude` | position approximative : Airbnb la décale, jusqu'à 150 m environ |
| `property_type, room_type` | type de bien ; logement entier, chambre privée, chambre partagée ou chambre d'hôtel |
| `accommodates, bedrooms, beds` | capacité en voyageurs, chambres, lits |
| `prix_nuit` | prix par nuit, sans devise dans la source ; vide pour 4 132 annonces |
| `minimum_nights, availability_365` | durée minimale de séjour ; nuits disponibles sur les 365 prochains jours |
| `number_of_reviews, number_of_reviews_ltm` | nombre d'avis, en tout et sur les 12 derniers mois |
| `review_scores_rating, _location, _value` | notes des voyageurs, de 1 à 5 : globale, emplacement, rapport qualité-prix |
| `host_is_superhost, instant_bookable` | hôte « superhost » ; réservation sans validation |
| `estimated_occupancy_l365d, estimated_revenue_l365d` | nuits occupées et revenu sur un an, estimés par Inside Airbnb à partir des avis |
| `first_review, last_review, last_scraped` | premier et dernier avis ; date du relevé |


## À savoir avant de commencer

- prix_nuit renseigné pour 5069 annonces sur 9201; le fichier source écrit le prix avec un symbole $ sans préciser la devise : n'écrivez pas « euros » sans le vérifier, et dites combien d'annonces ont un prix
- l'occupation et le revenu sont des estimations d'Inside Airbnb, pas des chiffres d'Airbnb
- le second fichier contient le texte des avis (`listing_id`, `date`, `comments`) : les prénoms des hôtes y sont remplacés par [hôte], mais relisez avant d'envoyer du texte à un LLM, et n'affichez jamais l'auteur
- une annonce sans avis depuis un an n'est peut-être plus active : `last_review` aide à les écarter

## Questions métier possibles

Des pistes, pas une liste à cocher : votre appli en soutient une ou deux, pour la décision ci-dessus.

1. Quel prix médian par nuit, par arrondissement et par capacité ?
2. Logement entier ou chambre privée : quel écart de prix dans chaque arrondissement ?
3. Les superhosts sont-ils plus chers ? Mieux notés ?
4. Pour un deux-pièces de 4 voyageurs dans le 3e, quelle fourchette de prix et quelle occupation estimée ?
5. La note d'emplacement suit-elle le prix ?
6. Quelle part des annonces est réservable sans validation, et est-elle mieux occupée ?
7. De quoi parlent les avis d'un arrondissement : emplacement, propreté, bruit ?

## Pour aller plus loin

- **ML** : un prix conseillé selon l'arrondissement, la capacité et les avis
- **LLM** : résumer les avis d'un arrondissement (50 avis au plus, texte nettoyé avant l'envoi)

## Questions ouvertes sur les données

Des questions précises, à trancher avec le fichier, chiffres à l'appui. Les réponses ne sont pas données : c'est votre première exploration.

1. Le prix par voyageur baisse-t-il quand la capacité augmente ?
2. Les annonces sans prix ont-elles encore des avis récents ?
3. Combien de nuits par an une annonce est-elle occupée, selon l'arrondissement ?
4. La note d'emplacement suit-elle le prix ?
5. Les annonces réservables sans validation sont-elles mieux occupées ?
6. Quels mots reviennent dans les avis des annonces les moins bien notées ?
