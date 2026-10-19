# Week 4: Power BI build guide

This guide builds a 4-page executive report in **Power BI Desktop** on the same star schema used in Weeks 1–3.
Time needed: about 2–3 hours the first time.

**You need:** Power BI Desktop (free from the Microsoft Store), plus `olist_powerbi.zip` from
[`notebooks/03_powerbi_export.ipynb`](../notebooks/03_powerbi_export.ipynb). Download these 2 files from this folder too:
[`measures.dax`](measures.dax) and [`olist_theme.json`](olist_theme.json).

---

## Step 1: Load the data
1. Unzip `olist_powerbi.zip` into a folder, for example `Documents\olist_powerbi`.
2. In Power BI Desktop: **Home → Get data → Text/CSV**. Pick `fact_orders.csv`, check **File origin = 65001: Unicode (UTF-8)**, then **Load**.
3. Repeat for the other 6 CSVs.
4. In **Table view**, check these column types (Column tools → Data type):

| Table | Column | Type |
|---|---|---|
| fact_orders | purchase_date | Date |
| fact_orders | order_value, delivery_days | Decimal number |
| fact_orders | is_late, review_after_delivery, review_score, days_late | Decimal number |
| dim_date | date, month_start | Date |
| dim_customer | first_purchase, last_purchase, cohort_month | Date |
| dim_customer | monetary | Decimal number |
| retention_cohort | months_after | Whole number |

## Step 2: Mark the date table
Select `dim_date` → **Table tools → Mark as date table** → pick `date`. Time-based measures like *Revenue MoM %* need this.

## Step 3: Relationships (Model view)
Power BI may guess some relationships. Delete any that aren't in this list, then drag to create these 5:

| From (one side) | To (many side) | Filter direction |
|---|---|---|
| dim_date[date] | fact_orders[purchase_date] | Single |
| dim_customer[customer_unique_id] | fact_orders[customer_unique_id] | Single |
| fact_orders[order_id] | fact_order_items[order_id] | Single |
| dim_segment[segment] | dim_customer[segment] | Single |
| dim_timing[delivery_timing] | fact_orders[delivery_timing] | Single |

`retention_cohort` stays on its own.

```
 dim_date ──┐                       ┌── dim_customer ── dim_segment
            ├──► fact_orders ◄──────┘
 dim_timing ┘        │
                     ▼
              fact_order_items
```

## Step 4: Sort columns and hide keys
- `dim_timing[delivery_timing]` → **Column tools → Sort by column → timing_order**
- `dim_segment[segment]` → **Sort by column → segment_order**
- `dim_date[month_name]` → **Sort by column → month_number**
- Right-click every ID column (order_id, customer_unique_id, product_id, seller_id) in the fact tables → **Hide in report view**.

## Step 5: Measures
1. **Home → Enter data**, name the table `_Measures`, click **Load**.
2. Select `_Measures`, then **Modeling → New measure**. Paste one measure from `measures.dax` at a time (the `Name =` line and everything under it), then press Enter.
3. Formats (Measure tools): **Revenue, Revenue Prev Month, Average Order Value, Category Revenue, Customer Revenue, Average Spend per Customer** → Currency, R$, 0–2 decimals. **All `%` measures, Revenue Share, Top 3 States Revenue Share, Customer Share and Segment Revenue Share** → Percentage, 1 decimal. **Average Review** → 2 decimals.
4. Delete the default `Column1` in `_Measures`. The table moves to the top with a calculator icon.

## Step 6: Theme
**View → Themes → Browse for themes** → `olist_theme.json`. Blue = good/early, orange = late/bad, same as the dashboard.

---

## Step 7: Build the 4 pages
Canvas: 16:9. Each page gets a title text box at the top that states **the finding, not the topic** (for example "Late deliveries drag ratings from 4.3★ to under 2★", not "Delivery").

### Page 1: Executive overview
| Visual | Fields |
|---|---|
| 5 **Cards** across the top | Revenue · Delivered Orders · Average Order Value · Late % · Average Review |
| **Slicer** (Between) | dim_date[date]. Set it to 1 Jan 2017 – 31 Aug 2018 (the complete period) |
| **Slicers** (Dropdown) | fact_orders[customer_state] · fact_orders[main_category] |
| **Column chart** | X: dim_date[month_start] · Y: Revenue · Tooltip: Revenue MoM % |
| **Line chart** | X: dim_date[month_start] · Y: Late % · Secondary Y: Average Review |
| **Text box** | "Late deliveries spiked Nov 2017 – Mar 2018, and ratings dipped at the same time." |

Turn off the date hierarchy on month_start (click the arrow next to the field and pick `month_start`) so it shows months, not Year/Quarter.

### Page 2: Delivery & customer experience
| Visual | Fields |
|---|---|
| **Clustered column chart** | X: dim_timing[delivery_timing] · Y: Average Review · Legend: dim_timing[timing_side] · Data labels on |
| **Card** | Late Reviews Before Arrival % (label: "of late-order reviews written before the parcel arrived") |
| **Card** | One-Star % |
| **Scatter chart** | Values: fact_orders[customer_state] · X: Average Delivery Days · Y: Average Review · Size: Delivered Orders. Visual-level filter: **Delivered Orders ≥ 300** |
| **Text box** | "Customers often rate the wait, not the product." |

### Page 3: Customers & retention
| Visual | Fields |
|---|---|
| 3 **Cards** | Customers · Repeat Rate · Average Spend per Customer |
| **Matrix** (heatmap) | Rows: retention_cohort[cohort_month] · Columns: months_after · Values: Sum of pct_returned. Then **Format → Cell elements → Background color → On** (white to blue) |
| **Clustered bar chart** | Y: dim_segment[segment] · X: Customer Share and Segment Revenue Share |
| **Table** | dim_segment[segment] · Customers · Segment Revenue Share · dim_segment[suggested_action] |
| **Text box** | "This page uses all customers. Retention needs each customer's full history, so the date slicer doesn't apply." |

The date slicer on Page 1 won't affect this page: the relationship runs from customers to orders, not the other way. That's intended.

### Page 4: Executive summary & recommendations
Text boxes in 3 columns, each with a big number, what it means, and what to do. See `EXECUTIVE_SUMMARY.md` for the wording. Add the 3 key cards (Late Reviews Before Arrival %, Repeat Rate, Top 3 States Revenue Share) next to their recommendations.

---

## Step 8: Check the numbers (QC before sharing)
With the date slicer cleared (all dates) on Page 1, the cards should match the notebook's last check cell:

| Measure | Expected (all dates) |
|---|---|
| Revenue | the notebook's "Revenue (delivered)" |
| Delivered Orders | the notebook's "Delivered orders" |
| Average Order Value | the notebook's "Average order value" |
| Late % | 6.8% |
| Average Review | 4.16 |
| Customers (Page 3) | 94,990 |
| Repeat Rate (Page 3) | 2.2% |

With the slicer on Jan 2017 – Aug 2018, Revenue should be about **R$ 15.37M**, the same as the live dashboard.
If a number is off, the usual cause is a wrong data type (Step 1) or a missing relationship (Step 3).

## Step 9: Save and share
1. **File → Save as** `olist_executive_report.pbix`.
2. **File → Export → Export to PDF** for a shareable copy.
3. Take a screenshot of each page (Windows: `Win + Shift + S`) for LinkedIn.
4. Upload the `.pbix`, the PDF and the screenshots to this repo's `powerbi/` folder.

> Publishing to the Power BI web service needs a work or school Microsoft account. That isn't required here: the `.pbix`, PDF and screenshots are enough for the portfolio.
