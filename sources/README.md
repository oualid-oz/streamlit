# D'où viennent les données du projet

Les scripts qui ont construit `data/projets/`. Pour le projet, vous n'en avez pas besoin : les fichiers sont déjà dans le dépôt. Ils servent à retrouver la source exacte d'une colonne, à refaire un fichier plus récent, ou à voir comment un jeu brut devient le Parquet que vous lisez.

```bash
uv run --with geopandas --with kaleido --with openpyxl --with python-calamine python sources/build_territoire_loiret.py
```

Chaque script télécharge sa source, réécrit ses fichiers dans `data/projets/`, met à jour `summary.json` et dépose un aperçu PNG dans `sources/figures/` (non versionné). Seules les couches GéoLoiret lues par `old_data.py` sont gardées en cache, dans `sources/data/cache/`.

| Cas | Script | Fichiers produits |
|---|---|---|
| 1 · OLD et véloroutes | `build_old_veloroutes.py`, qui s'appuie sur `old_data.py` | `old_veloroutes.parquet`, `old_veloroutes.geojson`, `old_communes.geojson`, `old_zone.geojson` |
| 2 · Collèges et risques | `build_colleges.py`, `build_risques.py`, puis `build_colleges_risques.py` | `colleges.parquet`, `colleges_secteurs.geojson`, `risques_communes.parquet`, `risques_communes.geojson`, `risques_catnat.parquet`, `colleges_risques.parquet` |
| 3 · Énergie | `build_energie.py` | `energie.parquet` |
| 4 · Sécurité routière | `build_securite_routiere.py` | `securite_routiere.parquet` |
| 5 · Immobilier | `build_immobilier.py` | `immobilier.parquet` |
| 6 · Location courte durée | `build_airbnb_lyon.py` | `airbnb_lyon.parquet`, `airbnb_lyon_reviews.parquet` |
| 7 · E-commerce | `build_olist.py` | `olist.parquet`, `olist_commentaires_negatifs.parquet` |
| 8 · Territoire du Loiret | `build_territoire_loiret.py` | `territoire_loiret.parquet` |

## Les sources du Département du Loiret

Le catalogue : [GéoLoiret](https://geoloiret.loiret-numerique.fr/apps/referentiel/catalogue_donnees.htm). Une couche `FeatureServer` se lit sans compte : ajoutez `/query?where=1=1&outFields=*&outSR=4326&f=geojson` à son adresse pour du GeoJSON en WGS 84, 2 000 entités au plus par appel. Les archives `.zip` sont des shapefiles en Lambert-93. Licence Ouverte 2.0, citez « Source : Département du Loiret », et la DDT pour le zonage des OLD.

### Cas 1, OLD et véloroutes (`old_data.py`)

| Couche | Adresse exacte |
|---|---|
| Tracés des véloroutes | [VELOROUTE/FeatureServer/4](https://geoloiret.loiret-numerique.fr/ags25/rest/services/I_7_Reseaux_Transports/VELOROUTE/FeatureServer/4) |
| Relevés de terrain, végétation | [VELOROUTE_TERRAIN/FeatureServer/5](https://geoloiret.loiret-numerique.fr/ags25/rest/services/I_7_Reseaux_Transports/VELOROUTE_TERRAIN/FeatureServer/5) |
| Bois classés à risque incendie | [FORET_BOIS_CLASSES_RISQUE_INCENDIE/FeatureServer/44](https://geoloiret.loiret-numerique.fr/ags25/rest/services/III_12_Zones_a_risque_naturel/FORET_BOIS_CLASSES_RISQUE_INCENDIE/FeatureServer/44) |
| Limites des communes (BD TOPO) | [LIMITES_ADMINISTRATIVES45/FeatureServer/3](https://geoloiret.loiret-numerique.fr/ags25/rest/services/V-BDTOPO/LIMITES_ADMINISTRATIVES45/FeatureServer/3) |
| Chemins ruraux (PDIPR) | [I_7_PDIPR_CR.zip](https://open.isogeo.com/apiquery/hostedRessources/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/986a15aa66d84e5cb28b39b0d90f0c77/67306b43bfcd4e52959a88e8c1c30dc2.bin/I_7_PDIPR_CR.zip) |
| Boucles cyclotouristiques | [PDIPR_Cyclo_Boucles.zip](https://open.isogeo.com/apiquery/hostedRessources/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/e64979de600b4075b488b5247acb9ea3/0c83ce3b69da44f6835512400e5e4148.bin/PDIPR_Cyclo_Boucles.zip) |
| Itinéraires de randonnée (PDIPR) | [PDIPR_ITINERAIRES.zip](https://open.isogeo.com/apiquery/hostedRessources/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/475640b269fe4cd58cb2ac445b2777ff/696297c710fa461cad579903993501d0.bin/PDIPR_ITINERAIRES.zip) |
| Zonage des OLD (DDT, sans service en ligne) | [`sources/data/old/ZIOLD_DEBROUSSAILLEMENT.shp`](data/old/), copie du fichier du catalogue |
| Végétation de la BD TOPO (IGN) | [WFS de la Géoplateforme](https://data.geopf.fr/wfs/ows), jusqu'à 40 m des voies |

### Cas 2, collèges (`build_colleges.py`)

| Couche | Adresse exacte |
|---|---|
| Collèges publics et privés | [ETABLISSEMENTS_SCOLAIRES/FeatureServer/4](https://geoloiret.loiret-numerique.fr/ags25/rest/services/III_2_Batiment/ETABLISSEMENTS_SCOLAIRES/FeatureServer/4) |
| Secteurs des collèges | [SECTORISATION_EDUCATION/FeatureServer/3](https://geoloiret.loiret-numerique.fr/ags25/rest/services/III_11_Zones_Gestion/SECTORISATION_EDUCATION/FeatureServer/3) |
| Effectifs par collège | [data.education.gouv.fr, fr-en-college-effectifs-niveau-sexe-lv](https://data.education.gouv.fr/explore/dataset/fr-en-college-effectifs-niveau-sexe-lv/) |
| Indice de position sociale (IPS) | [fr-en-ips_colleges](https://data.education.gouv.fr/explore/dataset/fr-en-ips_colleges/), [ap2022](https://data.education.gouv.fr/explore/dataset/fr-en-ips-colleges-ap2022/), [ap2023](https://data.education.gouv.fr/explore/dataset/fr-en-ips-colleges-ap2023/) |
| Résultats au brevet | [fr-en-dnb-par-etablissement](https://data.education.gouv.fr/explore/dataset/fr-en-dnb-par-etablissement/) |
| Valeur ajoutée des collèges | [fr-en-indicateurs-valeur-ajoutee-colleges](https://data.education.gouv.fr/explore/dataset/fr-en-indicateurs-valeur-ajoutee-colleges/) |

### Cas 2, risques (`build_risques.py` et `build_colleges_risques.py`)

| Couche | Adresse exacte |
|---|---|
| Retrait-gonflement des argiles | [GEORISQUE_RETRAIT_GONFLEMENT_ARGILE.zip](https://open.isogeo.com/apiquery/hostedRessources/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/f6fcc6e9ffee4c58b291574a6225526e/8a927e45dba04b2fbb7a0bc1ffd9237d.bin/GEORISQUE_RETRAIT_GONFLEMENT_ARGILE.zip) |
| Cavités souterraines | [GEORISQUE_CAVITES_SOUTERRAINES.zip](https://open.isogeo.com/apiquery/hostedRessources/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/e51058e7f85440198ccb037487bc3338/c0eedfb2663746fd9bd42bf6ef0736be.bin/GEORISQUE_CAVITES_SOUTERRAINES.zip) |
| Mouvements de terrain | [GEORISQUE_MOUVEMENTS_TERRAIN.zip](https://open.isogeo.com/apiquery/hostedRessources/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/6e3cbd9602b54de0a560a0236df55035/69a86b24f3b04e17a2704813c9310549.bin/GEORISQUE_MOUVEMENTS_TERRAIN.zip) |
| Repères de crues | [CD45_REPERES_CRUES.zip](https://open.isogeo.com/apiquery/hostedRessources/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/f20adecdaadc4a0897c43d29a90fa29a/8713e72b09c54b6881a72059b7623519.bin/CD45_REPERES_CRUES.zip) |
| Périmètres des PPRI | [DDT_PERIMETRE_PPRIS_CD45/FeatureServer/46](https://geoloiret.loiret-numerique.fr/ags25/rest/services/III_12_Zones_a_risque_naturel/DDT_PERIMETRE_PPRIS_CD45/FeatureServer/46) |
| Installations classées (ICPE) | [NSTALLATION_INDUSTRIELLE_ICPE/FeatureServer/5](https://geoloiret.loiret-numerique.fr/ags25/rest/services/III_8_Lieux_Production_Sites_Indus/NSTALLATION_INDUSTRIELLE_ICPE/FeatureServer/5) |
| Transport de matières dangereuses, réseau et zones de 500 m | [RESEAU_ROUTIER_TMD/FeatureServer/1](https://geoloiret.loiret-numerique.fr/ags25/rest/services/I_7_Reseaux_Transports/RESEAU_ROUTIER_TMD/FeatureServer/1), [/2](https://geoloiret.loiret-numerique.fr/ags25/rest/services/I_7_Reseaux_Transports/RESEAU_ROUTIER_TMD/FeatureServer/2) |
| Centrales nucléaires | [CENTRALES_NUCLEAIRES/FeatureServer/0](https://geoloiret.loiret-numerique.fr/ags25/rest/services/III_2_Batiment/CENTRALES_NUCLEAIRES/FeatureServer/0) |
| Arrêtés CatNat (Géorisques, GASPAR) | [gaspar.zip](https://files.georisques.fr/GASPAR/gaspar.zip), [fiche data.gouv.fr](https://www.data.gouv.fr/datasets/base-nationale-de-gestion-assistee-des-procedures-administratives-relatives-aux-risques-gaspar) |
| Communes du Loiret, si le cache GéoLoiret manque | [geo.api.gouv.fr](https://geo.api.gouv.fr/departements/45/communes) |

### Cas 8, territoire (`build_territoire_loiret.py`)

| Couche | Adresse exacte |
|---|---|
| Population municipale des communes | [data.gouv.fr](https://www.data.gouv.fr/datasets/65b1a75befcf2cf78c5aa480/) |
| Structures de santé | [data.gouv.fr](https://www.data.gouv.fr/datasets/67c24e4de01c99c2b8a31a1f/) |
| Lieux de covoiturage | [data.gouv.fr](https://www.data.gouv.fr/datasets/65a64a1be69e4163fc89ca45/) |
| Centre de chaque commune | [geo.api.gouv.fr](https://geo.api.gouv.fr/departements/45/communes?fields=code,centre) |
