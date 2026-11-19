"""Cas E-commerce (repli): Olist, une ligne par article de commande livrée.

Olist is published on Kaggle (login required). The same files, byte for byte (same names and
sizes), are on the Hugging Face mirror used below, which needs no login.
"""

import plotly.express as px
from common import BLUE, VERMILLION, fr, read_csv, record, save_figure, save_parquet, style

MIRROR = "https://huggingface.co/datasets/bulutttt/olist-raw-data/resolve/main"
SOURCE = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"


def load(name, **kwargs):
    return read_csv(f"{MIRROR}/olist_{name}_dataset.csv", **kwargs)


orders = load(
    "orders",
    parse_dates=[
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
)
items = load("order_items")
products = load("products")
sellers = load("sellers")
customers = load("customers")
reviews = load("order_reviews")
translation = read_csv(f"{MIRROR}/product_category_name_translation.csv")
print("sanity:", len(orders), "orders,", len(items), "items,", len(sellers), "sellers")

# Delivered orders only: only they have a real delivery date to compare with the promise.
orders = orders[orders["order_status"] == "delivered"].dropna(
    subset=["order_delivered_customer_date"]
)
orders = orders.assign(
    retard=orders["order_delivered_customer_date"] > orders["order_estimated_delivery_date"],
    jours_livraison=(
        orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"]
    ).dt.days,
)
note = reviews.groupby("order_id", as_index=False)["review_score"].mean()  # some orders have 2

df = (
    items.merge(orders, on="order_id")
    .merge(customers[["customer_id", "customer_state"]], on="customer_id")
    .merge(sellers[["seller_id", "seller_state"]], on="seller_id", how="left")
    .merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
    .merge(translation, on="product_category_name", how="left")
    .merge(note, on="order_id", how="left")
)
df = df.rename(columns={"product_category_name_english": "categorie"})[
    [
        "order_id", "order_item_id", "order_purchase_timestamp", "seller_id", "seller_state",
        "customer_state", "categorie", "price", "freight_value", "jours_livraison", "retard",
        "review_score",
    ]
].sort_values("order_purchase_timestamp").reset_index(drop=True)  # fmt: skip
path = save_parquet(df, "olist")

# Negative comments (score 1-2) for the LLM idea: classify the reasons.
negatifs = reviews[(reviews["review_score"] <= 2) & reviews["review_comment_message"].notna()]
negatifs = negatifs[["order_id", "review_score", "review_comment_message"]]
negatifs_path = save_parquet(negatifs.reset_index(drop=True), "olist_commentaires_negatifs")

# Starter figure: share of late orders for the 10 sellers with the most late deliveries (>=100 items).
par_vendeur = (
    df.groupby("seller_id")
    .agg(articles=("retard", "size"), part_retard=("retard", "mean"))
    .query("articles >= 100")
    .sort_values("part_retard", ascending=False)
    .head(10)
    .iloc[::-1]
    .reset_index()
)
par_vendeur["part_retard"] *= 100
par_vendeur["vendeur"] = par_vendeur["seller_id"].str[:8]
top = par_vendeur.iloc[-1]
title = (
    f"Le vendeur le plus en retard livre {top['part_retard']:.0f} % de ses articles hors délai, "
    f"contre {100 * df['retard'].mean():.0f} % pour l'ensemble "
    f"(n = {fr(len(df))} articles livrés, "
    f"{df['order_purchase_timestamp'].dt.year.min()}-{df['order_purchase_timestamp'].dt.year.max()})"
)
fig = px.bar(
    par_vendeur,
    x="part_retard",
    y="vendeur",
    orientation="h",
    text=par_vendeur["part_retard"].round(0).astype(int).astype(str) + " %",
    labels={
        "part_retard": "Articles livrés après la date promise, %",
        "vendeur": "Vendeur (8 premiers caractères)",
    },
)
fig.update_traces(marker_color=[BLUE] * (len(par_vendeur) - 1) + [VERMILLION])
fig.update_yaxes(type="category")
save_figure(style(fig, title), "olist")
record(
    "olist", df, path, "order_purchase_timestamp", SOURCE,
    "Creative Commons BY-NC-SA 4.0 (licence Olist sur Kaggle)", title,
    note="miroir sans login: Hugging Face bulutttt/olist-raw-data (fichiers identiques à Kaggle "
    "en noms et en tailles); retard = livré après la date estimée; seulement commandes livrées",
    comments_file={"file": negatifs_path.name, "rows": len(negatifs),
                       "columns": list(negatifs.columns),
                       "size_mb": round(negatifs_path.stat().st_size / 1e6, 2)},
)  # fmt: skip
print(df.shape, negatifs.shape, title)
