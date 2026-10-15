"""Data layer for the Olist BI dashboard.

Downloads the Olist dataset from Kaggle and rebuilds the same star schema and
quality-checked definitions used in the Week 1 and Week 2 notebooks.
"""
import glob
import os

import numpy as np
import pandas as pd

DATASET = "olistbr/brazilian-ecommerce"
FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "translation": "product_category_name_translation.csv",
}


def configure_kaggle(secrets):
    """Pass Kaggle credentials from Streamlit secrets to the Kaggle tools."""
    token = secrets.get("KAGGLE_API_TOKEN")
    if token:
        os.environ["KAGGLE_API_TOKEN"] = token
        path = os.path.expanduser("~/.kaggle")
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "access_token"), "w") as f:
            f.write(token)
    if secrets.get("KAGGLE_USERNAME") and secrets.get("KAGGLE_KEY"):
        os.environ["KAGGLE_USERNAME"] = secrets["KAGGLE_USERNAME"]
        os.environ["KAGGLE_KEY"] = secrets["KAGGLE_KEY"]


def download():
    """Return the folder holding the CSVs (local override via OLIST_DATA_DIR)."""
    local = os.environ.get("OLIST_DATA_DIR")
    if local:
        return local
    import kagglehub
    return kagglehub.dataset_download(DATASET)


def _read(folder, name):
    hits = glob.glob(os.path.join(folder, "**", name), recursive=True)
    if not hits:
        raise FileNotFoundError(name)
    return pd.read_csv(hits[0], encoding="utf-8-sig")


def build_model(folder):
    raw = {k: _read(folder, f) for k, f in FILES.items()}

    # ---- orders and delivery metrics
    orders = raw["orders"].copy()
    for c in ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
              "order_delivered_customer_date", "order_estimated_delivery_date"]:
        orders[c] = pd.to_datetime(orders[c], errors="coerce")
    bad = orders["order_delivered_customer_date"] < orders["order_purchase_timestamp"]
    orders.loc[bad, "order_delivered_customer_date"] = pd.NaT
    delivered = orders["order_delivered_customer_date"].notna()
    orders["delivery_days"] = (orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"]).dt.total_seconds() / 86400
    orders["days_late"] = (orders["order_delivered_customer_date"].dt.normalize()
                           - orders["order_estimated_delivery_date"].dt.normalize()).dt.days
    orders["is_late"] = np.where(delivered, (orders["days_late"] > 0).astype(float), np.nan)

    # ---- items, reviews
    items = raw["items"].copy()
    items["item_total"] = items["price"] + items["freight_value"]
    items_by_order = items.groupby("order_id").agg(n_items=("order_item_id", "count"),
                                                   order_value=("item_total", "sum")).reset_index()
    reviews = raw["reviews"].copy()
    for c in ["review_creation_date", "review_answer_timestamp"]:
        reviews[c] = pd.to_datetime(reviews[c], errors="coerce")
    reviews = (reviews.sort_values("review_answer_timestamp").drop_duplicates("order_id", keep="last")
               [["order_id", "review_score", "review_creation_date"]])

    # ---- products with English categories
    products = raw["products"].copy()
    tr = dict(zip(raw["translation"]["product_category_name"], raw["translation"]["product_category_name_english"]))
    tr.setdefault("pc_gamer", "pc_gamer")
    tr.setdefault("portateis_cozinha_e_preparadores_de_alimentos", "portable_kitchen_and_food_preparers")
    products["product_category_name"] = products["product_category_name"].fillna("unknown")
    products["category"] = (products["product_category_name"].map(tr).fillna(products["product_category_name"])
                            .str.replace("_", " ").str.title())

    # ---- fact tables
    cust = raw["customers"][["customer_id", "customer_unique_id", "customer_state"]]
    fo = (orders.merge(cust, on="customer_id", how="left")
          .merge(items_by_order, on="order_id", how="left")
          .merge(reviews, on="order_id", how="left")
          .rename(columns={"customer_state": "state"}))
    fo["n_items"] = fo["n_items"].fillna(0).astype(int)
    fo["month"] = fo["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    fo["review_after_delivery"] = fo["review_creation_date"] >= fo["order_delivered_customer_date"].dt.normalize()

    foi = (items.merge(products[["product_id", "category"]], on="product_id", how="left")
           .merge(fo[["order_id", "order_status", "state", "month"]], on="order_id", how="left"))

    # main category per order (largest item value) so orders can be filtered by category
    main_cat = (foi.sort_values("item_total", ascending=False).drop_duplicates("order_id")
                .set_index("order_id")["category"])
    fo["main_category"] = fo["order_id"].map(main_cat)

    # integrity checks (same as Week 1)
    assert len(fo) == len(raw["orders"]) and len(foi) == len(raw["items"])
    assert np.isclose(foi["item_total"].sum(), fo["order_value"].sum())
    return {"orders": fo, "items": foi}


def customer_tables(fo):
    """Retention and RFM tables, using purchase DAYS (QC'd definition from Week 2.1)."""
    p = fo[~fo["order_status"].isin(["canceled", "unavailable"])].copy()
    p["order_value"] = p["order_value"].fillna(0)
    p["day"] = p["order_purchase_timestamp"].dt.normalize()
    first = p.groupby("customer_unique_id")["day"].min().rename("first_day")
    p = p.join(first, on="customer_unique_id")
    days = p.groupby("customer_unique_id")["day"].nunique()
    end = p["day"].max()

    # cohort retention (distinct customers returning on a later day, by month offset)
    p["cohort"] = p["first_day"].dt.to_period("M")
    p["offset"] = ((p["day"].dt.year - p["first_day"].dt.year) * 12 + (p["day"].dt.month - p["first_day"].dt.month))
    returning = p[p["day"] > p["first_day"]]
    size = p.groupby("cohort")["customer_unique_id"].nunique()
    counts = returning.groupby(["cohort", "offset"])["customer_unique_id"].nunique().unstack(fill_value=0)
    retention = counts.reindex(index=size.index, columns=range(0, 13), fill_value=0).div(size, axis=0) * 100
    retention = retention.loc[(retention.index >= pd.Period("2017-01", "M")) & (retention.index <= pd.Period("2018-06", "M"))]
    retention.index = retention.index.strftime("%Y-%m")

    # repeat windows
    seq = p.drop_duplicates(["customer_unique_id", "day"]).sort_values("day")
    seq["n"] = seq.groupby("customer_unique_id").cumcount() + 1
    second = seq[seq["n"] == 2].set_index("customer_unique_id")["day"]
    gap = (second - first.reindex(second.index)).dt.days
    windows = []
    for w in [30, 90, 180, 365]:
        elig = first[first <= end - pd.Timedelta(days=w)]
        windows.append({"window": f"{w} days", "repeat_rate": 100 * gap.reindex(elig.index).le(w).sum() / len(elig)})

    # RFM
    snap = end + pd.Timedelta(days=1)
    rfm = p.groupby("customer_unique_id").agg(last=("day", "max"), monetary=("order_value", "sum"))
    rfm["frequency"] = days
    rfm["recency"] = (snap - rfm["last"]).dt.days
    rfm["R"] = pd.qcut(rfm["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["M"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    F = rfm["frequency"].clip(upper=3)
    cond = [(F >= 2) & (rfm["R"] >= 4), F >= 2, (F == 1) & (rfm["R"] >= 4) & (rfm["M"] >= 4),
            (F == 1) & (rfm["R"] >= 4), (F == 1) & (rfm["R"] <= 2) & (rfm["M"] >= 4), (F == 1) & (rfm["R"] <= 2)]
    names = ["Champions", "Loyal (lapsing)", "New big spenders", "New customers", "Big spenders at risk", "Hibernating"]
    rfm["segment"] = np.select(cond, names, default="Needs attention")
    seg = rfm.groupby("segment").agg(customers=("monetary", "size"), revenue=("monetary", "sum"),
                                     avg_spend=("monetary", "mean"), avg_recency_days=("recency", "mean"))
    seg["customers_pct"] = 100 * seg["customers"] / seg["customers"].sum()
    seg["revenue_pct"] = 100 * seg["revenue"] / seg["revenue"].sum()

    return {
        "customers": int(days.size),
        "repeat_rate": float(100 * (days > 1).mean()),
        "median_gap": float(gap.median()) if len(gap) else float("nan"),
        "within_30": float(100 * (gap <= 30).mean()) if len(gap) else float("nan"),
        "retention": retention,
        "windows": pd.DataFrame(windows),
        "segments": seg.sort_values("revenue", ascending=False),
    }


TIMING_BINS = [-np.inf, -15, -8, -1, 0, 3, 7, 14, np.inf]
TIMING_LABELS = ["15+ days early", "8–14 days early", "1–7 days early", "On the day",
                 "1–3 days late", "4–7 days late", "8–14 days late", "15+ days late"]


def review_by_timing(fo, after_delivery_only=False):
    r = fo[(fo["order_status"] == "delivered") & fo["review_score"].notna() & fo["days_late"].notna()]
    if after_delivery_only:
        r = r[r["review_after_delivery"]]
    r = r.assign(timing=pd.cut(r["days_late"], bins=TIMING_BINS, labels=TIMING_LABELS))
    return (r.groupby("timing", observed=False)
            .agg(orders=("order_id", "count"), avg_review=("review_score", "mean"),
                 one_star_pct=("review_score", lambda s: 100 * (s == 1).mean() if len(s) else np.nan))
            .reset_index())
