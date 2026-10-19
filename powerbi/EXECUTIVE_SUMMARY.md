# Executive summary: Olist e-commerce, 2017–2018

**Scope:** ~100,000 orders on Olist, Brazil's largest department-store marketplace · **Analysis:** Weeks 1–3 (Python), quality-checked in Week 2.1 · **Report:** Power BI (Week 4)

## The 3 things that matter

### 1. Missed delivery promises are the main cause of bad reviews
- Orders that arrive late average **2.27★**; orders that arrive on time or early average **4.29★**.
- **75%** of late-order reviews are written **before the parcel arrives**. Customers rate the wait, not the product.
- Even among reviews written after delivery, late orders still score lower (**3.53★ vs 4.29★**).
- Slower states get worse reviews (correlation **−0.84** across the 21 states with 300+ orders).

**Recommendations**
1. **Set honest delivery dates by region.** Base the promised date on each route's real delivery time, especially in the slowest states.
2. **Send the review request after delivery is confirmed**, not around the promised date.
3. **Warn customers before a delay.** A proactive "running late" message costs little and resets expectations.

### 2. Olist is a one-purchase business
- Only **2.2%** of customers came back on a different day.
- Those who do come back take a median of **74 days**, but **30%** return within 30 days.
- A late *first* order was linked to slightly lower return rates, but the difference was **not statistically significant** once customers who joined at the same time were compared. This report doesn't recommend acting on it.

**Recommendations**
4. **Build a second-purchase programme.** Send a well-timed nudge in the first 30–60 days, starting with *New big spenders* (high value, bought recently).
5. **Measure success as repeat rate.** Moving 2.2% to 3% would be a ~36% increase in returning customers.

### 3. Revenue is concentrated
- **SP, RJ and MG** bring in **62%** of revenue. Health & Beauty is the top category (**9.2%**).

**Recommendation**
6. **Protect the core, then expand.** Keep delivery reliable in the top 3 states first, then use honest delivery promises to grow in slower regions.

## Caveats
- This is public, anonymised data from 2016–2018. Use the patterns, not the exact numbers.
- Reviews and deliveries show a strong link, not proof that one causes the other. A test (for example, sending review requests after delivery to half of customers) would confirm it.
