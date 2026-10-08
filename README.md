# Olist E-Commerce BI: Python Business Intelligence Project

An end-to-end BI project on **~100,000 real orders** from Olist, Brazil's largest department-store marketplace. It takes the data from raw CSV files to a validated star schema, KPIs, customer analysis and an interactive dashboard, using only Python.

**Tools:** Python · pandas · SQL (DuckDB) · Plotly · Streamlit · Google Colab

---

## Business questions
1. How is revenue growing, and which categories and regions drive it?
2. How many customers come back, and which customer segments are the most valuable?
3. Is delivery performance hurting customer satisfaction?
4. What should the business do about it?

## Project roadmap

| Week | Stage | Status |
|---|---|---|
| 1 | Data pipeline & star schema | ✅ Done |
| 2 | KPIs, cohort retention, RFM segmentation | ✅ Done |
| 3 | Interactive Streamlit dashboard (live link) | 🔜 Next |
| 4 | Executive summary & recommendations | ⏳ Planned |

## Week 1: Data pipeline & star schema
📓 [`notebooks/01_data_pipeline_star_schema.ipynb`](notebooks/01_data_pipeline_star_schema.ipynb)

Turned **9 linked raw tables** into a clean **star schema**:

```
                 dim_date
                    │
 dim_customer ── fact_orders ── fact_order_items ── dim_product
                                       │
                                   dim_seller
```

**Data-quality issues found and fixed:**
- **Duplicate and repeat reviews**: kept one review per order (the latest)
- **GPS points outside Brazil**: removed, then averaged to one point per zip code
- **Customer ID changes with every order**: modelled customers on `customer_unique_id`, so repeat buyers aren't miscounted as new ones
- **Missing and untranslated product categories**: filled in and translated to English
- **Misspelled column names** in the source (`lenght`): standardised

**Automated validation:** 14 checks confirm that every table has one row per key, no rows were lost, revenue reconciles to the cent, and every foreign key matches its dimension.

**Week 1 headline numbers:**

| Metric | Value |
|---|---|
| Orders | 99,441 |
| Real customers | 96,096 |
| Sellers / Products | 3,095 / 32,951 |
| Revenue, delivered orders | R$ 15.42M |
| Average order value | R$ 159.83 |
| Delivered late | 6.8% |
| Average review score | 4.16 / 5 |
| Customers who ordered more than once | **3.1%** |

## Week 2: KPIs, retention & customer segments
📓 [`notebooks/02_kpis_retention_segments.ipynb`](notebooks/02_kpis_retention_segments.ipynb)

**What I did:** a monthly KPI layer in SQL, cohort retention analysis, RFM segmentation into 7 action-ready segments, and hypothesis tests (Mann-Whitney U, chi-square) on delivery performance.

**Key findings (after quality checks):**
- **Olist is a one-time-purchase business:** only **2.2%** of customers came back on a different day. (28% of apparent "repeat" customers had just split one shopping trip into several orders the same day.)
- **Real repeat buyers take time:** median **74 days** to a 2nd purchase; **30%** return within 30 days.
- **Missing the promised date is what triggers 1-star reviews:** late orders average **2.27★ vs 4.29★** on time, but **75%** of late-order reviews were written *before the parcel arrived*. Among reviews written after delivery, the gap is smaller but still clear: **3.53★ vs 4.29★** (effect size r = 0.30, p < 0.001).
- **Late first order vs coming back:** customers with a late first order returned less (**1.57% vs 2.02%** within 180 days), but the difference is **not statistically significant** once cohort timing is controlled for (Mantel-Haenszel OR = 0.81, p = 0.12).
- **Slower states get worse reviews:** across the 21 states with 300+ orders, delivery time and average review are strongly linked (Spearman r = **−0.84**, p < 0.001).
- **Revenue is concentrated:** SP, RJ and MG make up **62%** of revenue; Health & Beauty is the top category (9.2%).

**Quality checks:** 7 checks (split orders, equal observation windows, cohort timing, review timing, effect sizes, small-state bias, reconciliation) — all reconciliation checks pass, and two original findings were revised.

## How to run
1. Open the notebook in Google Colab.
2. Add your Kaggle credentials in **Secrets** (🔑) as `KAGGLE_API_TOKEN`.
3. Click **Runtime → Run all**. The data downloads automatically.

## Data source
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) on Kaggle (CC BY-NC-SA 4.0). The raw data is not stored in this repo; the notebook downloads it.

---
👤 **Oluwaseyi**: Community Manager & Business Development, building data and BI skills · [LinkedIn](https://www.linkedin.com/in/oluwaseyi-o-601915b5/)
