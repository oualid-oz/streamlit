# Cas 3 · Énergie en Centre-Val de Loire

[← les six cas](README.md) · [toutes les données](../../data/projets/LISEZMOI.md)

## Le contexte

La région Centre-Val de Loire produit bien plus d'électricité qu'elle n'en consomme, surtout grâce au nucléaire : le surplus part vers les régions voisines. RTE publie, par demi-heure, la consommation de la région et sa production filière par filière (éCO2mix). Une collectivité qui peut déplacer une partie de sa consommation (la recharge d'une flotte de véhicules électriques, le chauffage d'une piscine) a intérêt à savoir quand le réseau est le moins chargé.

- **Qui utilise l'appli** : l'acheteur d'énergie d'une collectivité
- **La décision à éclairer** : à quelles heures décaler les consommations qui peuvent l'être
- **Drill-down attendu** : année, mois, jour, demi-heure

## Les données

| | |
|---|---|
| Fichier | [`energie.parquet`](../../data/projets/energie.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/energie.parquet)) |
| Lignes | 52 603 demi-heures |
| Période | 01/09/2023 → 31/08/2026 |
| Source | [RTE, éCO2mix régional, données définitives](https://opendata.reseaux-energies.fr/explore/dataset/eco2mix-regional-cons-def/) |
| Licence | Licence Ouverte 2.0 (Etalab) : citer « RTE, éCO2mix » |

```python
import pandas as pd
df = pd.read_parquet("data/projets/energie.parquet")
```

| Colonne | Ce qu'elle contient |
|---|---|
| `date_heure` | début de la demi-heure, en UTC |
| `date` | le jour (heure de Paris) |
| `heure` | l'heure de Paris en décimal : 13.5 = 13 h 30 |
| `jour_semaine` | 0 = lundi … 6 = dimanche |
| `type_jour` | « semaine » ou « week-end » |
| `nature` | « Données définitives » ou « Données consolidées » (les mois les plus récents) |
| `consommation` | consommation de la région, en MW |
| `thermique, nucleaire, eolien, solaire, hydraulique, bioenergies` | production par filière, en MW |
| `pompage` | électricité consommée pour remonter l'eau des barrages, en MW |
| `ech_physiques` | solde des échanges avec les régions voisines, en MW. Négatif : la région exporte |


## À savoir avant de commencer

- `eolien` arrive en texte : convertissez-le (`pd.to_numeric(df["eolien"], errors="coerce")`) avant tout calcul
- MW est une puissance moyenne sur la demi-heure : une énergie en MWh, c'est MW × 0,5
- les dates sont en UTC dans `date_heure`, en heure de Paris dans `heure` : raisonnez en heure de Paris, c'est celle de l'utilisateur
- la question n'est pas seulement « y a-t-il assez d'électricité ? » : regardez aussi la production et les échanges avec les régions voisines
- Météo-France (températures) se joint sur la date si vous voulez expliquer la consommation

## Questions métier possibles

Des pistes, pas une liste à cocher : votre appli en soutient une ou deux, pour la décision ci-dessus.

1. À quelle heure la consommation est-elle la plus basse en semaine ? Et le week-end ?
2. De combien le pic d'hiver dépasse-t-il le pic d'été ?
3. Quelles demi-heures cumulent une faible consommation et une forte production solaire ou éolienne ?
4. Quelle part de la production vient des renouvelables, mois par mois ?
5. La consommation baisse-t-elle d'une année sur l'autre, à mois égal ?
6. Quand l'export vers les régions voisines est-il le plus faible ?
7. Pour recharger une flotte, quelle plage de 4 heures consécutives est la plus creuse, en semaine ?

## Pour aller plus loin

- **ML** : prévoir la consommation de demain selon l'heure, le jour et la température
- **LLM** : résumer la semaine filtrée en trois phrases pour un élu

## Questions ouvertes sur les données

Des questions précises, à trancher avec le fichier, chiffres à l'appui. Les réponses ne sont pas données : c'est votre première exploration.

1. Le creux de la nuit tombe-t-il à la même heure en hiver et en été ?
2. Le week-end, de combien la consommation baisse-t-elle, heure par heure ?
3. Quelles semaines de l'année ont le pic le plus haut ?
4. Certains midis, le solaire couvre-t-il une grande part de la consommation ?
5. À mois égal, consomme-t-on moins en 2026 qu'en 2024 ?
6. Quand l'export vers les régions voisines est-il le plus faible ?
