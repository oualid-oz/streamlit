# Cas 8 · Territoire du Loiret

[← les six cas](README.md) · [toutes les données](../../data/projets/LISEZMOI.md)

## Le contexte

Le Département du Loiret publie la population de ses communes, la liste des structures de santé qu'il soutient et les lieux de covoiturage. Ces trois jeux sont joints ici sur le code INSEE de la commune, avec le centre de chaque commune et sa distance à la structure de santé la plus proche. Un élu qui doit soutenir une maison de santé ou de nouveaux équipements veut savoir où ils serviront le plus d'habitants.

- **Qui utilise l'appli** : un élu départemental
- **La décision à éclairer** : où soutenir une maison de santé, ou ajouter des aires de covoiturage
- **Drill-down attendu** : arrondissement, canton, commune

## Les données

| | |
|---|---|
| Fichier | [`territoire_loiret.parquet`](../../data/projets/territoire_loiret.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/territoire_loiret.parquet)) |
| Lignes | 325 communes, 691 268 habitants en 2023 |
| Période | population 2014-2023; structures de santé mises à jour oct. 2025; covoiturage mis à jour janv. 2024 |
| Source | trois jeux du Département du Loiret sur data.gouv.fr : [population municipale](https://www.data.gouv.fr/datasets/population-municipale-des-communes-departements-du-loiret), [structures de santé](https://www.data.gouv.fr/datasets/structures-de-sante-departement-du-loiret), [lieux de covoiturage](https://www.data.gouv.fr/datasets/lieux-de-covoiturage-organisation-departement-du-loiret). Centres des communes : [geo.api.gouv.fr](https://geo.api.gouv.fr) |
| Licence | Licence Ouverte 2.0 (Etalab) : citer « Département du Loiret » |

```python
import pandas as pd
df = pd.read_parquet("data/projets/territoire_loiret.parquet")
```

| Colonne | Ce qu'elle contient |
|---|---|
| `code_insee, commune` | la commune |
| `arr, canton` | codes INSEE de l'arrondissement et du canton (la source ne donne pas le nom du canton) |
| `superficie_km2, densite_hab_km2` | surface et habitants par km² |
| `population_2014, population_2023` | population municipale INSEE |
| `lon, lat` | centre de la commune |
| `nb_structures_sante, nb_msp` | structures de santé dans la commune, dont maisons de santé pluriprofessionnelles |
| `nb_lieux_covoiturage, places_covoiturage` | aires de covoiturage et leurs places |
| `distance_soins_km` | distance à vol d'oiseau du centre de la commune à la structure de santé la plus proche |


## À savoir avant de commencer

- seules les 45 structures listées par le Département sont comptées : pas l'ensemble des médecins de la commune
- la distance est à vol d'oiseau, pas en voiture : dites-le dans l'appli
- 15 aires de covoiturage seulement : une commune à 0 n'est pas une anomalie
- le cas le plus court en lignes et le plus long en préparation si vous ajoutez une source : la jointure se fait sur `code_insee`, en texte (`"45234"`), pas en nombre

## Questions métier possibles

Des pistes, pas une liste à cocher : votre appli en soutient une ou deux, pour la décision ci-dessus.

1. Quelles communes sont à plus de 10 km d'une structure de santé, et combien d'habitants y vivent ?
2. Quelles communes ont gagné ou perdu des habitants depuis 2014 ?
3. Les communes qui grandissent sont-elles loin des soins ?
4. Combien d'habitants par structure de santé, canton par canton ?
5. Une maison de santé ajoutée dans une commune donnée, combien d'habitants rapproche-t-elle à moins de 10 km ?
6. Quels cantons n'ont aucune aire de covoiturage ?

## Pour aller plus loin

- **ML** : regrouper les communes qui se ressemblent (k-means sur la population, la distance aux soins et les équipements)
- **LLM** : une fiche commune pour un élu, à partir des indicateurs affichés

## Questions ouvertes sur les données

Des questions précises, à trancher avec le fichier, chiffres à l'appui. Les réponses ne sont pas données : c'est votre première exploration.

1. Quelles communes ont perdu des habitants depuis 2014 ?
2. Les communes à plus de 10 km des soins sont-elles petites ou moyennes ?
3. Combien d'habitants par structure de santé, arrondissement par arrondissement ?
4. Les aires de covoiturage sont-elles dans les communes denses ou rurales ?
5. Les communes qui gagnent des habitants sont-elles loin des soins ?
6. Où une seule nouvelle structure rapprocherait-elle le plus d'habitants ?
