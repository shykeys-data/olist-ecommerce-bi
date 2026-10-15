"""Olist E-Commerce BI dashboard (Week 3).

Run locally:  streamlit run dashboard/app.py
Needs Kaggle credentials in .streamlit/secrets.toml as KAGGLE_API_TOKEN
(or KAGGLE_USERNAME + KAGGLE_KEY).
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data

BLUE, RED, LIGHT = "#2E6FDB", "#C2410C", "#A9C4F5"
REPO = "https://github.com/shykeys-data/olist-ecommerce-bi"

st.set_page_config(page_title="Olist E-Commerce BI", page_icon="📦", layout="wide")


# ---------------------------------------------------------------- data
@st.cache_data(show_spinner="Downloading ~100k orders from Kaggle and building the model…", ttl=60 * 60 * 24)
def load():
    try:
        secrets = dict(st.secrets)
    except Exception:          # no secrets file (e.g. running locally with OLIST_DATA_DIR)
        secrets = {}
    data.configure_kaggle(secrets)
    model = data.build_model(data.download())
    return model["orders"], model["items"], data.customer_tables(model["orders"])


try:
    orders, items, cust = load()
except Exception as e:  # show a readable message instead of a stack trace
    st.error("Couldn't load the data from Kaggle. Check the KAGGLE_API_TOKEN secret.")
    st.exception(e)
    st.stop()


def chart(fig, height=380):
    fig.update_layout(template="simple_white", height=height, margin=dict(l=10, r=10, t=50, b=10),
                      legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------- sidebar filters
st.sidebar.title("Filters")
months = sorted(orders.loc[(orders["month"] >= "2017-01-01") & (orders["month"] <= "2018-08-01"), "month"].unique())
months = [pd.Timestamp(m) for m in months]
start, end = st.sidebar.select_slider("Purchase month", options=months, value=(months[0], months[-1]),
                                      format_func=lambda m: m.strftime("%b %Y"))
states = sorted(orders["state"].dropna().unique())
pick_states = st.sidebar.multiselect("Customer state", states, placeholder="All states")
cats = orders.loc[orders["order_status"] == "delivered", "main_category"].value_counts().index.tolist()
pick_cats = st.sidebar.multiselect("Product category", cats, placeholder="All categories")
st.sidebar.caption("Jan 2017 – Aug 2018 is the complete period. Earlier and later months have very few orders.")
st.sidebar.markdown(f"[📂 Code & notebooks]({REPO})")


def apply_filters(df, cat_col):
    m = (df["month"] >= start) & (df["month"] <= end)
    if pick_states:
        m &= df["state"].isin(pick_states)
    if pick_cats:
        m &= df[cat_col].isin(pick_cats)
    return df[m]


fo = apply_filters(orders, "main_category")
fi = apply_filters(items, "category")
delivered = fo[fo["order_status"] == "delivered"]
delivered_items = fi[fi["order_status"] == "delivered"]

# ---------------------------------------------------------------- header
st.title("📦 Olist E-Commerce BI")
st.caption("~100k real orders from Brazil's largest marketplace (2016–2018) · Python · pandas · Plotly · Streamlit · "
           f"by Oluwaseyi ([@shykeys-data]({REPO}))")

if delivered.empty:
    st.warning("No delivered orders match these filters. Try widening them.")
    st.stop()

# ---------------------------------------------------------------- KPI row
k = st.columns(5)
k[0].metric("Revenue (delivered)", f"R$ {delivered['order_value'].sum() / 1e6:,.2f}M")
k[1].metric("Delivered orders", f"{len(delivered):,}")
k[2].metric("Average order value", f"R$ {delivered['order_value'].mean():,.2f}")
k[3].metric("Delivered late", f"{100 * delivered['is_late'].mean():.1f}%")
k[4].metric("Average review", f"{delivered['review_score'].mean():.2f} ★")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Overview", "🚚 Delivery & reviews", "🔁 Customers",
                                        "🗺️ Regions & categories", "ℹ️ About the data"])

# ---------------------------------------------------------------- 1. overview
with tab1:
    monthly = (delivered.groupby("month")
               .agg(revenue=("order_value", "sum"), orders=("order_id", "count"),
                    late_pct=("is_late", lambda s: 100 * s.mean()), avg_review=("review_score", "mean"))
               .reset_index())
    fig = px.bar(monthly, x="month", y="revenue", title="Monthly revenue (delivered orders)",
                 labels={"month": "", "revenue": "Revenue (R$)"}, hover_data={"orders": ":,"})
    fig.update_traces(marker_color=BLUE)
    fig.update_yaxes(tickformat=",.0f")
    chart(fig)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.line(monthly, x="month", y="late_pct", markers=True, title="Late deliveries (%)",
                      labels={"month": "", "late_pct": "% delivered late"})
        fig.update_traces(line_color=RED)
        chart(fig, 320)
    with c2:
        fig = px.line(monthly, x="month", y="avg_review", markers=True, title="Average review score",
                      labels={"month": "", "avg_review": "Average review (1–5)"})
        fig.update_traces(line_color=BLUE)
        chart(fig, 320)
    st.info("When the late-delivery line spikes (Nov 2017 – Mar 2018), the review line dips. The next tab shows why.")

# ---------------------------------------------------------------- 2. delivery & reviews
with tab2:
    after_only = st.toggle("Only count reviews written after the parcel arrived", value=False,
                           help="Olist asks for a review around the promised date, so many late orders are rated "
                                "while the customer is still waiting.")
    timing = data.review_by_timing(fo, after_delivery_only=after_only)
    timing["side"] = ["Early / on time"] * 4 + ["Late"] * 4
    fig = px.bar(timing, x="timing", y="avg_review", color="side", text=timing["avg_review"].round(2),
                 color_discrete_map={"Early / on time": BLUE, "Late": RED},
                 title="Average review by delivery timing (left = arrived earlier, right = arrived later)",
                 labels={"timing": "", "avg_review": "Average review (1–5)", "side": ""},
                 hover_data={"orders": ":,", "one_star_pct": ":.1f"})
    fig.update_traces(textposition="outside")
    fig.update_yaxes(range=[0, 5.3])
    chart(fig, 420)

    late = fo[(fo["order_status"] == "delivered") & (fo["is_late"] == 1) & fo["review_score"].notna()]
    if len(late):
        before = 100 * (~late["review_after_delivery"]).mean()
        st.metric("Late-order reviews written before the parcel arrived", f"{before:.0f}%")
        st.caption("Customers often aren't rating the product. They're rating the wait.")

    by_state = (delivered.groupby("state")
                .agg(orders=("order_id", "count"), avg_delivery_days=("delivery_days", "mean"),
                     avg_review=("review_score", "mean"), late_pct=("is_late", lambda s: 100 * s.mean()))
                .reset_index())
    big = by_state[by_state["orders"] >= 300]
    if len(big) >= 3:
        fig = px.scatter(big, x="avg_delivery_days", y="avg_review", size="orders", text="state",
                         title="Slower states get worse reviews (states with 300+ orders)",
                         labels={"avg_delivery_days": "Average delivery time (days)", "avg_review": "Average review"})
        fig.update_traces(marker_color=BLUE, textposition="top center")
        chart(fig, 440)

# ---------------------------------------------------------------- 3. customers (full dataset)
with tab3:
    st.caption("This tab always uses the full dataset. Retention needs every customer's full history, so the sidebar filters don't apply here.")
    c = st.columns(4)
    c[0].metric("Customers", f"{cust['customers']:,}")
    c[1].metric("Came back on another day", f"{cust['repeat_rate']:.1f}%")
    c[2].metric("Median days to 2nd purchase", f"{cust['median_gap']:.0f}")
    c[3].metric("Repeat buyers back within 30 days", f"{cust['within_30']:.0f}%")

    heat = cust["retention"].drop(columns=[0])
    fig = px.imshow(heat, color_continuous_scale="Blues", aspect="auto", text_auto=".1f",
                    labels=dict(x="Months after first purchase", y="First purchase month", color="% returned"),
                    title="Cohort retention: % of each month's new customers who came back")
    chart(fig, 560)

    w = cust["windows"]
    fig = px.bar(w, x="window", y="repeat_rate", text=w["repeat_rate"].round(1).astype(str) + "%",
                 title="Share of customers who bought again within…", labels={"window": "", "repeat_rate": "%"})
    fig.update_traces(marker_color=BLUE, textposition="outside")
    chart(fig, 340)

    seg = cust["segments"].reset_index()
    long = seg.melt(id_vars="segment", value_vars=["customers_pct", "revenue_pct"], var_name="measure", value_name="pct")
    long["measure"] = long["measure"].map({"customers_pct": "Share of customers", "revenue_pct": "Share of revenue"})
    fig = px.bar(long, x="pct", y="segment", color="measure", barmode="group", orientation="h",
                 color_discrete_map={"Share of customers": LIGHT, "Share of revenue": BLUE},
                 title="RFM segments: who brings in the money", labels={"pct": "%", "segment": "", "measure": ""})
    fig.update_yaxes(categoryorder="total ascending")
    chart(fig, 440)
    actions = {"Champions": "VIP perks, referral programme", "Loyal (lapsing)": "Personal win-back offer",
               "New big spenders": "Fast 2nd-purchase nudge, cross-sell", "New customers": "Onboarding, first-repeat discount",
               "Needs attention": "Reminder with recommendations", "Big spenders at risk": "Targeted win-back on their category",
               "Hibernating": "Low-cost reactivation only"}
    seg["suggested action"] = seg["segment"].map(actions)
    st.dataframe(seg[["segment", "customers", "customers_pct", "revenue_pct", "avg_spend", "avg_recency_days", "suggested action"]]
                 .round(1), hide_index=True, use_container_width=True)

# ---------------------------------------------------------------- 4. regions & categories
with tab4:
    c1, c2 = st.columns(2)
    with c1:
        st_rev = delivered.groupby("state")["order_value"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(st_rev.sort_values("order_value"), x="order_value", y="state", orientation="h",
                     title="Top 10 states by revenue", labels={"order_value": "Revenue (R$)", "state": ""})
        fig.update_traces(marker_color=BLUE)
        fig.update_xaxes(tickformat=",.0f")
        chart(fig, 420)
    with c2:
        cat_rev = delivered_items.groupby("category")["item_total"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(cat_rev.sort_values("item_total"), x="item_total", y="category", orientation="h",
                     title="Top 10 categories by revenue", labels={"item_total": "Revenue (R$)", "category": ""})
        fig.update_traces(marker_color=BLUE)
        fig.update_xaxes(tickformat=",.0f")
        chart(fig, 420)
    st.dataframe(by_state.sort_values("orders", ascending=False).round(2), hide_index=True, use_container_width=True)

# ---------------------------------------------------------------- 5. about
with tab5:
    st.markdown(f"""
**Data:** [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
(Kaggle, CC BY-NC-SA 4.0), downloaded live and cached for 24 hours.

**Definitions**
- **Revenue:** product price + freight for delivered orders.
- **Late:** delivered after the estimated delivery date (compared by calendar day).
- **Repeat customer:** bought again on a *different day*. Same-day split orders don't count (Week 2.1 quality check).
- **Category filter:** an order is assigned to the category of its most valuable item.

**Quality checks behind these numbers:** a 14-check validation of the data model (Week 1) and a 7-check stress test of
the findings (Week 2.1), covering split orders, equal observation windows, cohort timing, review timing, effect sizes,
small-sample bias and reconciliation.

**Code and notebooks:** [{REPO}]({REPO})
""")
