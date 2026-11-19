# Cas 2 · Collèges et risques dans le Loiret

[← les cas](README.md) · [toutes les données](../../data/projets/LISEZMOI.md)

## D'où vient ce cas

Les cas 1 et 2 viennent du Département du Loiret. [Sandrine Gérard](https://www.linkedin.com/in/sandrine-g%C3%A9rard-562b8415b/), directrice au Département et chef de projet « travailler avec l'IA », m'a envoyé le catalogue de données GéoLoiret et deux pistes : croiser les OLD avec le tracé des véloroutes, « Collèges et Risques ». Le catalogue : [geoloiret.loiret-numerique.fr](https://geoloiret.loiret-numerique.fr/apps/referentiel/catalogue_donnees.htm).

## Le contexte

Le Département a la charge des collèges : « Il en assure la construction, la reconstruction, l'extension, les grosses réparations, l'équipement et le fonctionnement » ([code de l'éducation, L213-2](https://www.legifrance.gouv.fr/codes/id/LEGISCTA000006166574)). Il en possède 58, publics, qui accueillent des milliers d'élèves chaque jour. Or le Loiret a ses risques : argiles qui gonflent et se rétractent sous les bâtiments, cavités souterraines, crues de la Loire et de ses affluents, sites industriels, axes de transport de matières dangereuses, centrales nucléaires proches. Les arrêtés de catastrophe naturelle (CatNat) disent ce qui a déjà coûté, commune par commune. La question : quels collèges regarder en premier.

- **Qui utilise l'appli** : la direction du Département chargée des bâtiments et des collèges, et les élus qui votent les crédits de travaux
- **La décision à éclairer** : quels collèges examiner en priorité pour la prévention (diagnostic, travaux), en pesant l'exposition et le nombre d'élèves
- **Drill-down attendu** : type de risque, commune, collège

## Les données

| | |
|---|---|
| Fichiers | [`colleges_risques.parquet`](../../data/projets/colleges_risques.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/colleges_risques.parquet)), [`colleges.parquet`](../../data/projets/colleges.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/colleges.parquet)), [`risques_communes.parquet`](../../data/projets/risques_communes.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/risques_communes.parquet)), [`risques_catnat.parquet`](../../data/projets/risques_catnat.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/risques_catnat.parquet)), [`colleges_secteurs.geojson`](../../data/projets/colleges_secteurs.geojson) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/colleges_secteurs.geojson)), [`risques_communes.geojson`](../../data/projets/risques_communes.geojson) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/risques_communes.geojson)) |
| Lignes | `colleges_risques` : 70 collèges, une ligne chacun. En appui : `colleges` (70 collèges × 10 rentrées), `risques_communes` (325 communes), `risques_catnat` (2 065 décisions CatNat) |
| Période | rentrée 2025 pour les collèges ; arrêtés CatNat de 1983 à 2025 ; couches GéoLoiret de 2024 à 2026 |
| Source | GéoLoiret, [catalogue](https://geoloiret.loiret-numerique.fr/apps/referentiel/catalogue_donnees.htm) : collèges et secteurs, argiles, cavités, mouvements de terrain (BRGM), périmètres des PPRI (DDT45), repères de crues, installations classées (ICPE), transport de matières dangereuses (TMD), centrales nucléaires ; ministère de l'Éducation nationale, [data.education.gouv.fr](https://data.education.gouv.fr) : effectifs, indice de position sociale, brevet ; Géorisques, [arrêtés CatNat (GASPAR)](https://files.georisques.fr/GASPAR/gaspar.zip) |
| Licence | Licence Ouverte 2.0. Mentions : « Source : BRGM / DDT45 / Département du Loiret, année », « Géorisques, GASPAR », « ministère de l'Éducation nationale » |

```python
import json, pandas as pd, plotly.express as px

cr = pd.read_parquet("data/projets/colleges_risques.parquet")    # un collège par ligne
histo = pd.read_parquet("data/projets/colleges.parquet")       # 10 rentrées par collège
communes = pd.read_parquet("data/projets/risques_communes.parquet")
catnat = pd.read_parquet("data/projets/risques_catnat.parquet")
publics = cr[cr["statut"] == "public"]   # le Département possède les collèges publics
fig = px.scatter_map(publics, lat="lat", lon="lon", size="effectif_total", color="argiles_classe", hover_name="nom", zoom=8)
```

### `colleges_risques.parquet`, un collège par ligne

| Colonne | Ce qu'elle contient |
|---|---|
| `uai, nom, commune, code_insee, statut` | le collège ; `public` ou `privé` (le Département possède les publics) |
| `lat, lon, secteur_id` | position ; secteur de recrutement dans `colleges_secteurs.geojson` (vide pour les privés) |
| `effectif_total, ips` | élèves et indice de position sociale à la rentrée 2025 |
| `argiles_classe` | aléa retrait-gonflement des argiles au point du collège : fort, moyen, faible, non cartographié |
| `dans_ppri, ppri` | le collège est-il dans un périmètre de plan de prévention du risque inondation (PPRI), et lequel |
| `nb_cavites_500m, nb_mouvements_terrain_500m` | cavités souterraines et mouvements de terrain recensés à moins de 500 m |
| `distance_icpe_km, nb_icpe_1km` | distance à l'installation classée la plus proche ; installations à moins de 1 km |
| `distance_seveso_km` | distance au site Seveso le plus proche |
| `distance_tmd_m, type_tmd_proche, dans_zone_tmd_500m` | distance à l'axe de transport de matières dangereuses le plus proche, son type (autoroute, route, voie ferrée), et si le collège est dans sa zone de 500 m |
| `distance_centrale_km, centrale_proche` | distance à la centrale nucléaire la plus proche, et son nom |
| `distance_repere_crue_km` | distance au repère de crue le plus proche |
| `nb_catnat, nb_catnat_inondations, nb_catnat_secheresse, nb_catnat_mouvement_terrain` | arrêtés de catastrophe naturelle de la commune du collège, en tout et par péril |
| `annee_dicrim` | année du document d'information communal sur les risques de la commune (vide si aucun) |

Les rayons (500 m, 1 km) sont des choix du script, pas des seuils officiels.

### En appui

- `colleges.parquet` : l'historique des 70 collèges sur 10 rentrées (effectifs par niveau, IPS, brevet), pour voir lesquels se remplissent.
- `risques_communes.parquet` : les 325 communes, avec leur exposition (parts d'aléa argiles, PPRI, cavités, ICPE, Seveso, TMD) et leurs arrêtés CatNat par péril.
- `risques_catnat.parquet` : une ligne par arrêté × commune × péril (`peril`, `date_debut`, `date_fin`, `date_arrete`, `date_jo`).
- `colleges_secteurs.geojson` (`properties.secteur_id`) et `risques_communes.geojson` (`id` = code INSEE) pour les cartes.

## À savoir avant de commencer

- un aléa n'est pas un risque, et un périmètre de PPRI n'est pas la zone inondable : `dans_ppri` ne dit pas que le bâtiment est inondé
- l'exposition est mesurée en un point, dont la précision est inconnue : une distance de quelques mètres ne veut rien dire
- « non cartographié » pour les argiles peut vouloir dire que la couche est incomplète, pas que l'argile est absente
- la couche ICPE compte aussi des élevages, des carrières et des éoliennes : `nb_icpe_1km` n'est pas un risque industriel
- un arrêté CatNat suppose que le maire l'ait demandé : les comptes disent la procédure autant que la catastrophe
- le Département possède les collèges publics : filtrez sur `statut` avant de classer
- un score qui additionne des risques différents doit être justifié : dites lesquels vous retenez, et pourquoi

## Questions métier possibles

Des pistes, pas une liste à cocher : votre appli en soutient une ou deux, pour la décision ci-dessus.

1. Quels collèges publics examiner en priorité, et sur quel risque ?
2. Combien d'élèves sont dans un collège exposé, à un risque ou à plusieurs ?
3. Les collèges qui gagnent des élèves sont-ils aussi exposés ?
4. Quel diagnostic demander pour quel collège (sol, inondation, industriel) ?
5. Comment montrer à un élu la différence entre un risque exposé (aléa, périmètre) et un risque vécu (arrêtés CatNat) ?
6. Les collèges les plus exposés accueillent-ils des publics plus fragiles ?

## Questions ouvertes sur les données

Des questions précises, à trancher avec le fichier, chiffres à l'appui. Les réponses ne sont pas données : c'est votre première exploration.

1. Quels collèges publics cumulent le plus de facteurs d'exposition ? Comment justifier un score ou une règle de classement ?
2. Combien d'élèves sont dans un collège situé dans un périmètre de PPRI, et leur commune a-t-elle beaucoup d'arrêtés d'inondation ?
3. Le classement change-t-il si l'on double ou réduit le rayon des cavités ou des mouvements de terrain ?
4. L'exposition aux risques est-elle liée à l'indice de position sociale des collèges ?
5. Quels collèges sont proches d'un axe TMD ou d'un site Seveso, et lesquels cumulent avec un risque naturel ?
6. Quels collèges exposés sont dans une commune sans DICRIM ?

## Pour aller plus loin

- **ML** : regrouper les collèges par profil de risque (k-means sur les variables d'exposition), ou prévoir les effectifs pour peser l'exposition par le nombre d'élèves
- **LLM** : une fiche risques par collège pour un élu, à partir des indicateurs affichés
