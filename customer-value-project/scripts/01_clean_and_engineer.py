"""
Phase 1 - Data Cleaning & Feature Engineering
Project: Decoding Customer Value - A SQL-Driven Retention Strategy
"""

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# 1. LOAD
# ---------------------------------------------------------------------------
RAW_PATH = "data/Dataset.csv"
OUT_PATH = "data/customers_clean.csv"

df = pd.read_csv(RAW_PATH)
print(f"Loaded {len(df):,} rows, {df.shape[1]} columns from {RAW_PATH}")

# ---------------------------------------------------------------------------
# 2. STANDARDIZE COLUMN NAMES (snake_case, no spaces -> SQL-friendly)
# ---------------------------------------------------------------------------
df = df.rename(columns={
    "Customer ID": "customer_id",
    "Age": "age",
    "Gender": "gender",
    "Item Purchased": "item_purchased",
    "Category": "category",
    "Purchase Amount (USD)": "purchase_amount",
    "Location": "location",
    "Size": "size",
    "Color": "color",
    "Season": "season",
    "Review Rating": "review_rating",
    "Subscription Status": "subscription_status",
    "Shipping Type": "shipping_type",
    "Discount Applied": "discount_applied",
    "Promo Code Used": "promo_code_used",
    "Previous Purchases": "previous_purchases",
    "Payment Method": "payment_method",
    "Frequency of Purchases": "frequency_of_purchases",
})

# ---------------------------------------------------------------------------
# 3. DATA QUALITY CHECKS + CLEANING DECISIONS
#    Every decision here is printed to the terminal so it ends up in your
#    report as a documented, traceable choice -- not a silent transformation.
# ---------------------------------------------------------------------------
print("\n--- DATA QUALITY REPORT ---")

# 3a. Duplicate rows / duplicate customers
dupe_rows = df.duplicated().sum()
dupe_ids = df["customer_id"].duplicated().sum()
print(f"Duplicate rows: {dupe_rows} | Duplicate customer_id: {dupe_ids}")
df = df.drop_duplicates(subset="customer_id", keep="first")

# 3b. Strip whitespace from text columns (defensive, even if already clean)
text_cols = [
    "gender", "item_purchased", "category", "location", "size", "color",
    "season", "subscription_status", "shipping_type", "discount_applied",
    "promo_code_used", "payment_method", "frequency_of_purchases",
]
for c in text_cols:
    df[c] = df[c].astype(str).str.strip()

# 3c. Missing review ratings -> preserve missingness as its own signal
#     instead of silently imputing. We flag it, THEN impute with the
#     median so downstream numeric features never break on NaN.
missing_reviews = df["review_rating"].isna().sum()
print(f"Missing review_rating: {missing_reviews} ({missing_reviews/len(df):.1%}) "
      f"-> flagged with review_missing, then median-imputed")
df["review_missing"] = df["review_rating"].isna().astype(int)
median_rating = df["review_rating"].median()
df["review_rating"] = df["review_rating"].fillna(median_rating)

# 3d. discount_applied vs promo_code_used are 100% identical in this dataset
#     (verified: every row where one is "Yes" the other is "Yes" too).
#     Keeping both would double-count the same signal in any score, so we
#     collapse them into one canonical binary flag and keep the originals
#     only for traceability.
identical = (df["discount_applied"] == df["promo_code_used"]).mean()
print(f"discount_applied == promo_code_used in {identical:.1%} of rows "
      f"-> collapsed into a single 'used_promo' flag")
df["used_promo"] = (df["promo_code_used"].str.lower() == "yes").astype(int)

# 3e. Range sanity checks (fail loudly if the data ever changes on you)
assert df["age"].between(0, 100).all(), "age out of expected range"
assert df["purchase_amount"].gt(0).all(), "non-positive purchase_amount found"
assert df["previous_purchases"].ge(0).all(), "negative previous_purchases found"
print("Range checks passed: age, purchase_amount, previous_purchases all valid")

# 3f. IMPORTANT DATA-QUALITY FINDING: subscription_status is perfectly
#     confounded with gender in this dataset (every subscriber is Male,
#     every Female is a non-subscriber). Using subscription_status as a
#     "declared loyalty" signal would silently encode gender bias into the
#     loyalty model, so we deliberately EXCLUDE it from both loyalty
#     definitions below. We keep the column so it can still be reported on
#     the dashboard, just not used as a scoring input.
sub_gender_check = pd.crosstab(df["subscription_status"], df["gender"])
print("\nSubscription Status x Gender (confound check):")
print(sub_gender_check)
print("-> subscription_status is fully confounded with gender in this data; "
      "excluded from loyalty scoring to avoid encoding gender bias.")

# 3g. SECOND, MORE CONSEQUENTIAL CONFOUND: promo/discount usage is ALSO
#     fully confounded with gender. Every recorded promo user is Male;
#     zero Female customers used a promo code. Because
#     promo_dependency_score and loyalty_score_b (built below) are both
#     derived from used_promo, the "genuinely loyal" segment and
#     Definition B inherit a gender skew that reflects this dataset
#     property, not necessarily real behavior. We keep the metrics as
#     computed -- the underlying scoring LOGIC still holds up when tested
#     within the male subgroup alone (see report) -- but this confound
#     MUST be disclosed wherever loyalty_score_b / promo-dependency
#     figures are reported.
promo_gender_check = pd.crosstab(df["gender"], df["used_promo"], normalize="index") * 100
print("\nGender x used_promo, % within gender (confound check):")
print(promo_gender_check.round(1))
print("-> promo usage is fully confounded with gender (0% of Female customers "
      "used a promo). Any promo-dependency or loyalty-B metric must disclose this.")

# ---------------------------------------------------------------------------
# 4. FEATURE ENGINEERING
# ---------------------------------------------------------------------------
print("\n--- FEATURE ENGINEERING ---")

# 4a. Annualized purchase frequency: turns the categorical cadence label
#     into an approximate number of purchases/year so it can be compared
#     numerically. NOTE: 'Bi-Weekly'/'Fortnightly' and 'Quarterly'/
#     'Every 3 Months' are treated as the same cadence on purpose -- they
#     describe the same real-world frequency under different labels.
FREQ_TO_ANNUAL = {
    "Weekly": 52,
    "Bi-Weekly": 26,
    "Fortnightly": 26,
    "Monthly": 12,
    "Every 3 Months": 4,
    "Quarterly": 4,
    "Annually": 1,
}
df["purchases_per_year"] = df["frequency_of_purchases"].map(FREQ_TO_ANNUAL)
assert df["purchases_per_year"].isna().sum() == 0, "unmapped frequency label found"

# 4b. Engagement score (0-100): blends HOW MANY times a customer has
#     historically bought (previous_purchases, weight 0.6) with HOW OFTEN
#     they typically buy (purchases_per_year, weight 0.4). Repeat count is
#     weighted higher because it's a direct historical count, while the
#     cadence label is closer to a self-reported habit.
def minmax_100(s):
    return (s - s.min()) / (s.max() - s.min()) * 100

df["engagement_score"] = (
    0.6 * minmax_100(df["previous_purchases"])
    + 0.4 * minmax_100(df["purchases_per_year"])
).round(1)

# 4c. Promo dependency score (0-100): captures "how much does this
#     customer's purchase look driven by a discount, net of how engaged
#     they otherwise are." A promo user who is highly engaged elsewhere
#     scores LOW (they'd likely buy anyway); a promo user with low
#     engagement scores HIGH (classic bargain-hunter pattern). Customers
#     who never used a promo score exactly 0 -- there is nothing to be
#     "dependent" on.
df["promo_dependency_score"] = (
    df["used_promo"] * (100 - df["engagement_score"])
).round(1)


def dependency_tier(row):
    if row["used_promo"] == 0:
        return "No Promo Use"
    if row["promo_dependency_score"] >= 66:
        return "High Dependency"
    if row["promo_dependency_score"] >= 33:
        return "Moderate Dependency"
    return "Low Dependency"


df["promo_dependency_tier"] = df.apply(dependency_tier, axis=1)

# 4d. Value tier: lifetime_value_proxy approximates cumulative revenue as
#     (single-purchase basket size) x (historical repeat count). It is a
#     proxy, not true LTV, because we only have one transaction snapshot
#     per customer -- this limitation is stated explicitly in the report.
df["lifetime_value_proxy"] = df["purchase_amount"] * df["previous_purchases"]
df["value_tier"] = pd.qcut(
    df["lifetime_value_proxy"], q=4, labels=["Bronze", "Silver", "Gold", "Platinum"]
)

# 4e. Satisfaction flag/tier: cut points (3.3 / 4.1) are the 33rd/66th
#     percentile of review_rating in THIS dataset, not arbitrary numbers.
q33, q66 = df["review_rating"].quantile([0.33, 0.66])
print(f"\nSatisfaction cut points (data-driven, 33rd/66th pct): "
      f"{q33:.2f} / {q66:.2f}")


def satisfaction_tier(r):
    if r >= q66:
        return "Satisfied"
    if r >= q33:
        return "Neutral"
    return "Dissatisfied"


df["satisfaction_tier"] = df["review_rating"].apply(satisfaction_tier)
df["high_satisfaction"] = (df["satisfaction_tier"] == "Satisfied").astype(int)

# 4f. LOYALTY -- the brief requires TWO competing, traceable definitions,
#     tested against revenue, with a clear argued choice. Neither uses
#     subscription_status (see confound finding above).
#
#     Definition A - "Behavioral Loyalty": purely about repeat-purchase
#     habit. It IS the engagement_score. High score = buys often & a lot.
df["loyalty_score_a"] = df["engagement_score"]

#     Definition B - "Organic Value Loyalty": spend-based, but penalized
#     for promo dependency -- i.e. rewards customers who spend well
#     WITHOUT needing a discount to do it (genuine brand pull).
norm_value = minmax_100(df["lifetime_value_proxy"])
df["loyalty_score_b"] = (norm_value - 0.5 * df["promo_dependency_score"]).clip(lower=0)
df["loyalty_score_b"] = minmax_100(df["loyalty_score_b"]).round(1)
df["loyalty_score_a"] = df["loyalty_score_a"].round(1)

# top-30% flags for each definition
thresh_a = df["loyalty_score_a"].quantile(0.70)
thresh_b = df["loyalty_score_b"].quantile(0.70)
df["loyal_a_flag"] = (df["loyalty_score_a"] >= thresh_a).astype(int)
df["loyal_b_flag"] = (df["loyalty_score_b"] >= thresh_b).astype(int)

# ---------------------------------------------------------------------------
# 5. TEST THE TWO LOYALTY DEFINITIONS AGAINST REVENUE
#    This is the "test both, argue for one" requirement from the brief.
# ---------------------------------------------------------------------------
print("\n--- LOYALTY DEFINITION COMPARISON ---")
corr_a = df["loyalty_score_a"].corr(df["lifetime_value_proxy"])
corr_b = df["loyalty_score_b"].corr(df["lifetime_value_proxy"])
print(f"Correlation with lifetime_value_proxy -> Definition A: {corr_a:.3f} "
      f"| Definition B: {corr_b:.3f}")

avg_value_loyal_a = df.loc[df["loyal_a_flag"] == 1, "lifetime_value_proxy"].mean()
avg_value_loyal_b = df.loc[df["loyal_b_flag"] == 1, "lifetime_value_proxy"].mean()
avg_value_overall = df["lifetime_value_proxy"].mean()
print(f"Avg lifetime_value_proxy -> overall: {avg_value_overall:.0f} | "
      f"Loyal-A group: {avg_value_loyal_a:.0f} | Loyal-B group: {avg_value_loyal_b:.0f}")

pct_promo_loyal_a = df.loc[df["loyal_a_flag"] == 1, "used_promo"].mean()
pct_promo_loyal_b = df.loc[df["loyal_b_flag"] == 1, "used_promo"].mean()
print(f"% who used a promo -> Loyal-A group: {pct_promo_loyal_a:.1%} | "
      f"Loyal-B group: {pct_promo_loyal_b:.1%} | overall: {df['used_promo'].mean():.1%}")

overlap = ((df["loyal_a_flag"] == 1) & (df["loyal_b_flag"] == 1)).sum()
print(f"Customers flagged loyal by BOTH definitions: {overlap} "
      f"(A total: {df['loyal_a_flag'].sum()}, B total: {df['loyal_b_flag'].sum()})")

# ---------------------------------------------------------------------------
# 6. SAVE
# ---------------------------------------------------------------------------
df.to_csv(OUT_PATH, index=False)
print(f"\nSaved cleaned + engineered dataset -> {OUT_PATH}  "
      f"({df.shape[0]:,} rows, {df.shape[1]} columns)")