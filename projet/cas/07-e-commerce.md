# Cas 7 · E-commerce au Brésil

[← les six cas](README.md) · [toutes les données](../../data/projets/LISEZMOI.md)

## Le contexte

Olist est une place de marché brésilienne : des milliers de vendeurs y vendent à des clients de tout le pays, et Olist a publié deux ans de commandes, anonymisées. Ici, 96 470 commandes livrées entre 2016 et 2018, 2 970 vendeurs et 71 catégories, avec le délai de livraison, le retard éventuel et la note du client. Les retards abîment la note de toute la place de marché : il faut savoir sur quels vendeurs agir d'abord.

- **Qui utilise l'appli** : le directeur e-commerce de la place de marché
- **La décision à éclairer** : quels vendeurs et quelles catégories corriger en priorité
- **Drill-down attendu** : catégorie, vendeur, commande

## Les données

| | |
|---|---|
| Fichier | [`olist.parquet`](../../data/projets/olist.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/olist.parquet)), [`olist_commentaires_negatifs.parquet`](../../data/projets/olist_commentaires_negatifs.parquet) ([télécharger](https://github.com/jlkhermes38/awp-gabarit/raw/main/data/projets/olist_commentaires_negatifs.parquet)) |
| Lignes | 110 189 articles livrés (96 470 commandes) ; 10 890 avis négatifs |
| Période | 15/09/2016 → 29/08/2018 |
| Source | [Olist, Brazilian E-Commerce, sur Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (copie sans compte : Hugging Face `bulutttt/olist-raw-data`) |
| Licence | CC BY-NC-SA 4.0 : citer Olist, pas d'usage commercial, partager dans les mêmes conditions |

```python
import pandas as pd
df = pd.read_parquet("data/projets/olist.parquet")
```

| Colonne | Ce qu'elle contient |
|---|---|
| `order_id, order_item_id` | la commande, et le rang de l'article dans la commande |
| `order_purchase_timestamp` | date et heure de l'achat |
| `seller_id` | le vendeur (identifiant anonymisé) |
| `seller_state, customer_state` | État du vendeur et du client (sigle : SP = São Paulo, RJ = Rio de Janeiro…) |
| `categorie` | catégorie du produit, en anglais |
| `price, freight_value` | prix de l'article et frais de port, en reais (BRL) |
| `jours_livraison` | jours entre l'achat et la livraison |
| `retard` | `True` si livré après la date promise au client |
| `review_score` | note du client sur la commande, de 1 à 5 (vide pour 827 articles) |


## À savoir avant de commencer

- une ligne par article, pas par commande : pour compter des commandes, `df["order_id"].nunique()`
- la note est celle de la commande, répétée sur chacun de ses articles
- un vendeur en retard sur 3 commandes ne pèse pas comme un vendeur en retard sur des milliers : fixez un nombre minimum d'articles et dites-le
- le second fichier (`order_id`, `review_score`, `review_comment_message`) contient les avis notés 1 ou 2 qui ont un commentaire, en portugais
- licence non commerciale : suffisant pour un cours, pas pour un produit

## Questions métier possibles

Des pistes, pas une liste à cocher : votre appli en soutient une ou deux, pour la décision ci-dessus.

1. Les commandes en retard ont-elles une note plus basse ? De combien ?
2. Quels vendeurs cumulent retards et mauvaises notes, parmi ceux qui vendent beaucoup ?
3. Quelles catégories ont le plus de retards ?
4. Quels États sont les plus mal servis, en délai et en frais de port ?
5. Le délai de livraison s'est-il amélioré entre 2017 et 2018 ?
6. Les frais de port pèsent-ils plus lourd sur les petits achats ?
7. De quoi se plaignent les avis négatifs : le retard, le produit, l'article jamais reçu ?

## Pour aller plus loin

- **ML** : le risque qu'une commande arrive en retard, à l'achat
- **LLM** : classer les motifs des avis négatifs (en portugais) en quelques catégories

## Questions ouvertes sur les données

Des questions précises, à trancher avec le fichier, chiffres à l'appui. Les réponses ne sont pas données : c'est votre première exploration.

1. À partir de combien de jours de retard la note chute-t-elle ?
2. Quels États clients attendent le plus longtemps leur colis ?
3. Quelle part du prix représentent les frais de port, État par État ?
4. Les vendeurs de São Paulo livrent-ils plus vite que les autres ?
5. Les retards augmentent-ils en fin d'année (Black Friday, Noël) ?
6. Quelles catégories reçoivent le plus de notes 1 ?
