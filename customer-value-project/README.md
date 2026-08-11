# Decoding Customer Value: A SQL-Driven Retention Strategy

A full-pipeline customer intelligence project for a D2C fashion brand: Python feature engineering → SQL segmentation → Power BI dashboard → data-backed retention playbook. Built for the Consulting & Analytics Club, IIT Guwahati (Summer Projects '26).

## The problem

The brand had transactional data on 3,900 customers but no loyalty score, no churn label, and no timestamps — every concept used here (loyalty, value tier, promo dependency) had to be *defined and tested from the raw variables*, not assumed. The core question: **is this brand building a genuinely loyal customer base, or is it reliant on continuous promotional activity — and what should it do either way?**

## Approach

| Phase | What it does |
|---|---|
| **1. Python (pandas)** | Cleans the raw data and engineers customer-level features: promo dependency score, value tier, satisfaction tier, and two independently-tested loyalty definitions |
| **2. SQL (SQLite)** | Loads the cleaned data into a real database and runs 8 segmentation queries answering all 5 key business questions in the brief |
| **3. Power BI** | A published 4-panel dashboard — customer value pyramid, promo dependency vs. engagement, geographic opportunity map, and category funnel |
| **4. Retention Playbook** | A written report translating the analysis into a named promotional sunset plan and an ideal customer profile, with quantified projected impact |

## Key findings

- **Value is sharply concentrated, customer count isn't.** All four value tiers hold roughly equal customer counts (~975 each), but the top tier alone generates 51.5% of total customer value vs. 5.3% for the bottom tier.
- **A measurable "genuinely loyal" segment exists** — 1,171 customers (30% of the base) with high spend, high repeat-purchase count, and below-average promo usage (25.5% vs. 43.0% baseline).
- **253 customers are being discounted despite not needing it** — they show the highest engagement score of any segment (79.0) yet still receive promos. This is the specific, low-risk target for the promotional sunset plan.
- **Two critical data-quality findings shaped the whole analysis:** `subscription_status` and `promo_code_used` are both perfectly confounded with gender in this dataset (e.g., 0% of female customers ever used a promo code). Rather than ignore this, the loyalty-scoring logic was validated *within* the unconfounded subgroup (r = 0.886) before being trusted — full detail in the report.

Full findings, methodology, and the two-definition loyalty test are in [`reports/Customer_Intelligence_Report.md`](reports/Customer_Intelligence_Report.md).

## Dashboard

![Founder Dashboard](assets/dashboard_screenshot.png)

*Built and published in Power BI Service (browser-based — Power BI Desktop isn't available on macOS).*

## Tech stack

Python (pandas, numpy) · SQLite · SQL (CTEs, window-style aggregation) · Power BI Service · DAX (aggregate measures)

## Repo structure

```
customer-value-project/
├── data/
│   ├── Dataset.csv              # raw source data
│   └── customers_clean.csv      # cleaned + feature-engineered output of Phase 1
├── scripts/
│   ├── 01_clean_and_engineer.py
│   ├── 02_load_to_sql.py
│   └── 03_run_sql_queries.py
├── sql/
│   └── segmentation_queries.sql # 8 named, documented queries
├── outputs/                     # CSV export of every query result
├── reports/
│   └── Customer_Intelligence_Report.md
├── assets/
│   └── dashboard_screenshot.png
├── customer_intelligence.db     # SQLite database (generated)
├── requirements.txt
└── README.md
```

## How to run it

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python scripts/01_clean_and_engineer.py   # clean + engineer features
python scripts/02_load_to_sql.py          # load into SQLite
python scripts/03_run_sql_queries.py      # run all 8 segmentation queries
```

The dashboard was built directly in Power BI Service on top of `data/customers_clean.csv`.
