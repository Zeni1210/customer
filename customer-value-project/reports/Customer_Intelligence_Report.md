# Decoding Customer Value: A SQL-Driven Retention Strategy
### Executive Summary & Retention Playbook

---

## Executive Summary

**The core question:** Is this brand building a genuinely loyal customer base, or is its growth reliant on continuous promotional activity?

**The answer: both, in roughly equal measure — and the two groups are identifiable, which is what makes this actionable.** Across 3,900 customers, we built two independently-tested definitions of loyalty (a behavioral one based on repeat-purchase habit, and an organic-value one that penalizes promo dependency) and found consistent evidence of a real, self-sustaining core customer base sitting alongside a distinct, promo-contingent segment.

**Four headline findings:**

1. **Value is sharply concentrated.** The top value quartile (975 customers) generates 51.5% of total customer value; the bottom quartile generates 5.3%. Customer *count* is evenly split across tiers — value is not.
2. **A "genuinely loyal" segment exists and is measurable.** 1,171 customers (30.0% of the base) show high spend, high repeat-purchase count, and below-average promo usage (25.5% vs. 43.0% base rate). They average $75.14 per purchase and 38.4 previous purchases — a real core, not a modeling artifact.
3. **A distinct, lower-value "Discount-Only" segment also exists.** 604 customers (15.5%) used a promo on every recorded purchase, average only 12.1 previous purchases, and hold a lifetime value proxy of $717 — about a quarter of the loyal segment's $2,852. Their basket size ($59.39) looks normal; their repeat behavior doesn't.
4. **A specific sub-segment is currently receiving discounts it doesn't need.** 253 customers (6.5% of base) used a promo *and* show the highest engagement score of any segment measured (79.0, vs. 19.4 for the truly dependent group). This is the clearest, lowest-risk opportunity to protect margin.

**Two data-quality findings that shaped this analysis and should be validated against real transaction data before this model informs live decisions:**

- `subscription_status` is perfectly confounded with gender in this dataset (100% of subscribers are male).
- `promo_code_used` is also perfectly confounded with gender (0% of female customers used a promo code). This means promo-dependency and organic-loyalty metrics currently overlap with gender in a way that reflects this dataset, not necessarily real customer behavior — both are excluded or explicitly caveated wherever they touch gender-sensitive conclusions below.

**Recommendation, in one line:** stop discounting the 253 customers who already buy without needing to, keep discounting the segment that actually depends on it, and reallocate acquisition spend toward the five states that already show the ideal customer profile at above-average concentration.

---

## Part A: Promotional Sunset Plan

### Segment to sunset: "Low Dependency" customers

**Definition (traceable):** customers where `used_promo = 1` and `engagement_score` (a 0.6/0.4 blend of previous-purchase count and annualized purchase frequency) falls in the top band — i.e., customers who redeemed a discount despite already showing top-tier repeat-purchase behavior.

**Size:** 253 customers (6.5% of the base), concentrated in the Gold and Platinum value tiers (210 of 253, or 83%).

**Why this segment, specifically:** their average previous-purchase count (40.5) is more than 3x the truly dependent segment's (12.1), and their engagement score (79.0) is the highest of any group in the dataset — higher even than customers who never used a promo at all (42.3). The evidence points to a group whose purchase decision was not contingent on the discount.

**What we are explicitly NOT touching:** the 604-customer "High Dependency" segment (avg. engagement 19.4, avg. previous purchases 12.1). Their behavior is consistent with genuine price sensitivity — removing their discount risks losing volume, which directly contradicts the brief's goal of protecting margin *without* losing volume. This segment needs a different lever (loyalty-program enrollment, smaller/graduated incentives, or acceptance as a lower-margin acquisition cohort), not a sunset.

### Rollout timeline (90-day phased pilot, with a held-out control)

| Phase | Weeks | Action |
|---|---|---|
| 1 | 1–4 | Stop proactively targeting this segment with promo emails/push offers. Codes remain redeemable if sought out — minimizes backlash risk while testing response. |
| 2 | 5–8 | Remove default/automatic promo application at checkout for this segment specifically. |
| 3 | 9–12 | Full monitoring window. Compare treated group against a **10% held-out control** (kept on standard promo treatment) to isolate the causal effect of removal from seasonal or macro noise. |

### Metric to track

Primary: **month-over-month purchase frequency of the treated group vs. the control group.** Secondary: gross margin recovered (see below).

**Guardrail:** if the treated group's purchase frequency drops more than 10% relative to the control group within the 90-day window, pause the rollout and reassess before expanding it to adjacent segments.

### Projected impact (illustrative — see caveat)

This dataset does not include actual discount depth (a specific % or $ off), only a binary flag, so a precise dollar figure isn't defensible from this data alone. Using a conservative, industry-typical 15% average discount depth against this segment's $57.75 average transaction value: **≈ $8.66 recovered per transaction, ×253 customers ≈ ~$2,190 recovered per purchase cycle**, scaling with repeat frequency. *Replace the 15% assumption with the brand's actual average discount depth before using this number in a real budget.*

---

## Part B: Ideal Customer Profile

**Segment:** the organically loyal group (1,171 customers, 30% of base) — high spend, high repeat-purchase count, low promo dependency.

| Attribute | Value |
|---|---|
| Average age | 44.2 |
| Average purchase amount | $75.14 |
| Average previous purchases | 38.4 |
| Average review rating | 3.80 / 5 |
| Top category | Clothing (44.8%), then Accessories (32.7%) |
| Payment method | No dominant preference (Credit Card leads at only 18.4%) — not a useful targeting lever |
| Top 5 states by concentration | Pennsylvania, Nevada, Illinois, Arizona, Alaska |

**A genuinely useful cross-check:** Pennsylvania, Arizona, and Alaska appear in *both* this top-5 list *and* the independently-derived "underlevered geography" list from the SQL analysis (states with above-average spend and organic loyalty, but a below-average customer count). That agreement across two separate analyses is a stronger acquisition signal than either alone — these aren't speculative expansion bets, they're markets that already contain a concentrated, proven customer type the brand hasn't fully reached.

**Actionable targeting recommendation:** prioritize acquisition spend in Pennsylvania, Arizona, and Alaska specifically, built around Clothing and Accessories as the entry categories, rather than a broad national campaign.

**Honest caveat on gender:** the loyal segment skews 58.9% male / 41.1% female, versus a 68/32 base rate — meaning women are *over-represented* in this segment relative to their share of the customer base. Given that promo usage is perfectly confounded with gender in this dataset (see Executive Summary), this skew is at least partly a mechanical artifact of how `loyal_b_flag` is constructed, not confirmed evidence that women are more loyal. **We recommend age, category, and geography as the reliable targeting variables here, and explicitly recommend against using gender as a targeting lever until this pattern is validated against real, non-confounded transaction data.**

---

## Limitations

- No timestamps in the source data — "loyalty" and "engagement" are behavioral proxies (repeat-purchase count and frequency label), not confirmed multi-year retention.
- `lifetime_value_proxy` = single-transaction basket size × previous-purchase count. It approximates, but does not equal, true cumulative revenue.
- Two variables (`subscription_status`, `promo_code_used`) are fully confounded with gender in this dataset; any finding touching either should be re-validated against real transaction data before informing live segmentation or marketing decisions.
