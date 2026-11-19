# Cas 1 · OLD et véloroutes du Loiret

[← les cas](README.md) · [toutes les données](../../data/projets/LISEZMOI.md)

## D'où vient ce cas

Les cas 1 et 2 viennent du Département du Loiret. [Sandrine Gérard](https://www.linkedin.com/in/sandrine-g%C3%A9rard-562b8415b/), directrice au Département et chef de projet « travailler avec l'IA », m'a envoyé le catalogue de données GéoLoiret et deux pistes : croiser les OLD avec le tracé des véloroutes, « Collèges et Risques ». Le catalogue : [geoloiret.loiret-numerique.fr](https://geoloiret.loiret-numerique.fr/apps/referentiel/catalogue_donnees.htm).

Je lui ai montré une première carte : la zone OLD et les véloroutes qui la traversent. Sa réponse, en substance : ce qui compte pour le Département, c'est le linéaire concerné et les communes, la surface à traiter une fois retirée l'emprise de la voie, et le couvert forestier, pour avoir une première idée de l'intensité des travaux (coupes d'arbres, élagages sévères). La décision : prioriser les communes et les tronçons les plus exposés au feu, parce que la forêt y est dense.

## Le contexte

Dans les massifs classés à risque d'incendie, le code forestier impose de débroussailler : ce sont les obligations légales de débroussaillement (OLD). Elles concernent aussi les routes : « l'État et les collectivités territoriales […] propriétaires de voies ouvertes à la circulation publique […] procèdent à leurs frais au débroussaillement […] sur une bande dont la largeur est fixée par l'autorité administrative compétente de l'État et qui ne peut excéder 20 mètres de part et d'autre de l'emprise de ces voies, dans la traversée des bois et forêts et dans les zones situées à moins de 200 mètres de bois et forêts » ([code forestier, article L134-10](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000025246008)). Le Loiret a deux zones : la Sologne, et le massif de la forêt d'Orléans, ajouté par l'[arrêté ministériel du 13 avril 2026](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000053969373) (JO du 28/04/2026). Le Département gère des véloroutes qui traversent ces zones : la Loire à vélo, la Scandibérique, le canal d'Orléans, la V48 en projet.

- **Qui utilise l'appli** : les services du Département qui entretiennent les véloroutes
- **La décision à éclairer** : quelles communes et quels tronçons traiter en premier, et avec quelle intensité de travaux
- **Drill-down attendu** : itinéraire, commune, tronçon

## Les données

| | |
|---|---|
| Fichiers | [`old_veloroutes.parquet`](../../data/projets/old_veloroutes.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/old_veloroutes.parquet)), [`old_veloroutes.geojson`](../../data/projets/old_veloroutes.geojson) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/old_veloroutes.geojson)), [`old_communes.geojson`](../../data/projets/old_communes.geojson) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/old_communes.geojson)), [`old_zone.geojson`](../../data/projets/old_zone.geojson) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/old_zone.geojson)) |
| Lignes | 1 564 morceaux de tronçon (un tronçon × une commune) |
| Période | tracés de novembre 2025, zonage OLD de février 2026 |
| Source | GéoLoiret : [zonage OLD](https://open.isogeo.com/s/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/r/30f4e50565cd46b894a2a37c7973f3fa), [tracés des véloroutes](https://open.isogeo.com/s/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/r/194fd0fef6ac4f23abec83e726fee9d1), [bois classés à risque incendie](https://open.isogeo.com/s/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/r/f50797014a9d427db5a33c3eaa239e84) ; IGN, BD TOPO (végétation et eau) |
| Licence | zonage OLD et bois classés : Licence Ouverte 2.0 (« Source : DDT41 »). Tracés des véloroutes : usage libre avec la mention « Source : Département du Loiret - 2025 ». BD TOPO : IGN |

```python
import json, pandas as pd, plotly.express as px

df = pd.read_parquet("data/projets/old_veloroutes.parquet")
communes = json.load(open("data/projets/old_communes.geojson"))  # id = code INSEE
ha = df.groupby("code_insee", as_index=False)["ha_forte"].sum()
fig = px.choropleth_map(ha, geojson=communes, locations="code_insee", color="ha_forte", zoom=8,
                        center={"lat": 47.8, "lon": 2.2})
# les tracés : fig.update_layout(map_layers=[{"source": json.load(open("data/projets/old_veloroutes.geojson")), "type": "line"}])
```

| Colonne | Ce qu'elle contient |
|---|---|
| `id_ligne` | clé unique « tronçon-INSEE », la même que l'`id` du GeoJSON `old_veloroutes` |
| `troncon` | identifiant du tronçon dans GéoLoiret ; un tronçon coupé par une limite de commune a plusieurs lignes |
| `itineraire` | Loire à vélo, Scandibérique, les deux (tronc commun), Canal d'Orléans, V48 (en projet) |
| `gestionnaire` | Département du Loiret, Commune, État (VNF) ou « non renseigné » (le cas le plus fréquent) |
| `voie, revetement` | type de voie (voie verte, piste cyclable, route…), traduit des codes du schéma national (libellés non vérifiés) ; revêtement |
| `ouvert` | `True` si le tronçon est ouvert au public, `False` pour un projet |
| `commune, code_insee` | commune du morceau de tronçon (vide pour 7 morceaux hors Loiret) |
| `longueur_m, longueur_dans_old_m, part_dans_old` | longueur du morceau, longueur dans la zone OLD, et la part (0 à 1) |
| `longueur_bois_classe_m, part_bois_classe` | longueur sous un bois classé à risque d'incendie (dans la zone ou non) |
| `part_foret_fermee_ign` | part de la longueur dans la zone OLD à moins de 10 m d'une forêt fermée (BD TOPO) ; vide hors zone. Hypothèse : 10 m |
| `emprise_voie_hyp_m` | largeur supposée de la voie : 3 m voie verte et piste, 6 m route, 5 m circulation apaisée. **Hypothèse** : la couche n'a pas de largeur |
| `bande_hyp_m` | largeur supposée de la bande à débroussailler de chaque côté, depuis le bord de la voie : 10 m. **Hypothèse** : le code plafonne à 20 m, l'État fixe la largeur |
| `ha_bande_brute` | surface de la bande dans la zone, sans rien retirer (les recouvrements comptent deux fois) |
| `ha_a_traiter` | surface une fois retirées l'emprise des voies et l'eau, chaque m² compté une fois |
| `ha_forte, ha_moyenne, ha_legere, ha_courante` | la même surface par niveau d'intervention selon la végétation (forte : forêt fermée ; moyenne : bois, forêt ouverte, peupleraie, haie ; légère : lande ; courante : le reste). **Hypothèse** de la démo |
| `lat, lon` | milieu du morceau de tronçon |

Les trois GeoJSON (WGS 84) servent aux cartes : `old_zone` (les deux zones OLD : `zone_arretee` en Sologne, `zone_en_attente` en forêt d'Orléans), `old_veloroutes` (les tracés, `id` = `id_ligne`), `old_communes` (une commune par entité, `id` = code INSEE).

## À savoir avant de commencer

- les largeurs sont des **hypothèses** : bande de 10 m, emprise de 3 à 6 m. Une plaquette de la DDT du Loiret (janvier 2025) parle de 2,50 m de part et d'autre des voies ouvertes à la circulation motorisée ; une véloroute n'est pas motorisée. Faites-en un paramètre de l'appli et dites-le
- le fichier marque la zone de la forêt d'Orléans « en attente de l'arrêté ministériel » : l'arrêté du 13 avril 2026 l'a classée depuis
- une partie des kilomètres dans la zone n'est pas ouverte (la V48 est en projet) : séparez ce qui est à faire maintenant de ce qui le sera
- le gestionnaire est « non renseigné » pour la plupart des kilomètres dans la zone : qui paie n'est pas toujours dans la donnée
- deux sources de végétation : les bois classés (DDT) et la BD TOPO (IGN). Elles ne disent pas la même chose, comparez-les
- pour les cartes sans geopandas : `px.choropleth_map` avec un GeoJSON, et `map_layers` pour les tracés

## Questions métier possibles

Des pistes, pas une liste à cocher : votre appli en soutient une ou deux, pour la décision ci-dessus.

1. Quels linéaires et quelles communes sont concernés, et sur combien de kilomètres ?
2. Quelle surface reste à traiter une fois retirée l'emprise des véloroutes ?
3. Quel niveau d'intervention (coupes, élagage, débroussaillage) selon le couvert forestier ?
4. Quelles communes et quels tronçons traiter en premier, parce que la forêt y est dense ?
5. Combien coûterait le programme si l'on connaissait un coût à l'hectare par niveau d'intervention ?
6. Que change la largeur de bande retenue (2,5, 10 ou 20 m) sur le classement des communes ?

## Questions ouvertes sur les données

Des questions précises, à trancher avec le fichier, chiffres à l'appui. Les réponses ne sont pas données : c'est votre première exploration.

1. Combien de kilomètres sont dans la zone OLD, et combien sont vraiment ouverts au public ?
2. Quelles communes concentrent le plus d'hectares en forêt fermée ? Le classement change-t-il par kilomètres ?
3. De combien la surface baisse-t-elle quand on retire l'emprise des voies et l'eau, et où l'écart est-il le plus fort ?
4. Un tronçon sous un bois classé est-il aussi au bord d'une forêt fermée de l'IGN ?
5. Quelle part des kilomètres dans la zone a un gestionnaire « non renseigné » ?
6. Avec une bande de 5 ou de 20 m, quelles communes changent de rang ?

## Pour aller plus loin

- **ML** : classer les tronçons par niveau d'intervention à partir de leurs caractéristiques, ou regrouper les communes qui se ressemblent
- **LLM** : rédiger une fiche par commune pour les équipes de terrain, à partir des chiffres affichés
