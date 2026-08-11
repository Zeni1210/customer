-- ===========================================================================
-- Segmentation & Analysis Queries
-- Project: Decoding Customer Value - A SQL-Driven Retention Strategy
-- Table: customers  (loaded by scripts/02_load_to_sql.py)
--
-- Each query below is preceded by a QUERY marker comment that the runner
-- script (03_run_sql_queries.py) parses to split this file apart. Keep
-- that marker line intact if you add your own queries.
-- ===========================================================================

-- === QUERY: q1_loyalty_segments ===
-- Key Question 1: Who are the genuinely loyal customers vs. those who only
-- buy when there is a discount?
-- Builds a named segment straight from the engineered fields and profiles
-- each one on spend, tenure, and satisfaction.
SELECT
    CASE
        WHEN loyal_b_flag = 1 THEN 'Genuinely Loyal (Organic)'
        WHEN used_promo = 1 AND promo_dependency_tier = 'High Dependency'
            THEN 'Discount-Only Buyer'
        WHEN used_promo = 1 THEN 'Promo-Assisted Repeat Buyer'
        ELSE 'Low Engagement / Occasional'
    END AS customer_segment,
    COUNT(*) AS customer_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customers), 1) AS pct_of_base,
    ROUND(AVG(purchase_amount), 2) AS avg_purchase_amount,
    ROUND(AVG(previous_purchases), 1) AS avg_previous_purchases,
    ROUND(AVG(lifetime_value_proxy), 0) AS avg_lifetime_value_proxy,
    ROUND(AVG(review_rating), 2) AS avg_review_rating,
    ROUND(100.0 * AVG(used_promo), 1) AS promo_usage_pct
FROM customers
GROUP BY customer_segment
ORDER BY avg_lifetime_value_proxy DESC;


-- === QUERY: q2_value_tier_profile ===
-- Key Question 2 / Scope: What separates high-value customers from
-- low-value ones, and which profiles show the strongest repeat-purchase
-- behavior?
SELECT
    value_tier,
    COUNT(*) AS customer_count,
    ROUND(AVG(engagement_score), 1) AS avg_engagement_score,
    ROUND(AVG(purchases_per_year), 1) AS avg_purchases_per_year,
    ROUND(AVG(previous_purchases), 1) AS avg_previous_purchases,
    ROUND(100.0 * AVG(used_promo), 1) AS promo_usage_pct,
    ROUND(AVG(review_rating), 2) AS avg_review_rating
FROM customers
GROUP BY value_tier
ORDER BY
    CASE value_tier
        WHEN 'Bronze' THEN 1 WHEN 'Silver' THEN 2
        WHEN 'Gold' THEN 3 WHEN 'Platinum' THEN 4
    END;


-- === QUERY: q3_category_season_tenure ===
-- Scope: Which seasons and categories are associated with lower-tenure
-- customers versus those with high previous-purchase counts?
SELECT
    category,
    season,
    COUNT(*) AS customer_count,
    ROUND(AVG(previous_purchases), 1) AS avg_previous_purchases,
    ROUND(AVG(engagement_score), 1) AS avg_engagement_score
FROM customers
GROUP BY category, season
ORDER BY avg_previous_purchases DESC;


-- === QUERY: q4_geo_demand_type ===
-- Key Question 3 / Scope: Which geographies signal organic demand versus
-- discount-driven volume, and which are commercially underlevered
-- (strong quality of demand, but a small customer base -- an acquisition
-- opportunity rather than a retention one)?
WITH location_stats AS (
    SELECT
        location,
        COUNT(*) AS customer_count,
        ROUND(AVG(purchase_amount), 2) AS avg_purchase_amount,
        ROUND(AVG(lifetime_value_proxy), 2) AS avg_ltv_proxy,
        ROUND(100.0 * AVG(used_promo), 1) AS promo_usage_pct,
        ROUND(100.0 * AVG(loyal_b_flag), 1) AS organic_loyal_pct
    FROM customers
    GROUP BY location
),
overall AS (
    SELECT
        AVG(customer_count) AS avg_count,
        AVG(avg_ltv_proxy) AS avg_ltv,
        AVG(organic_loyal_pct) AS avg_loyal_pct
    FROM location_stats
)
SELECT
    ls.location,
    ls.customer_count,
    ls.avg_purchase_amount,
    ls.avg_ltv_proxy,
    ls.promo_usage_pct,
    ls.organic_loyal_pct,
    CASE
        WHEN ls.avg_ltv_proxy > o.avg_ltv
             AND ls.organic_loyal_pct > o.avg_loyal_pct
             AND ls.customer_count < o.avg_count
            THEN 'Underlevered (high quality, small base)'
        WHEN ls.promo_usage_pct > 50 AND ls.organic_loyal_pct < o.avg_loyal_pct
            THEN 'Discount-Driven'
        ELSE 'Core / Average'
    END AS geo_demand_type
FROM location_stats ls, overall o
ORDER BY ls.avg_ltv_proxy DESC;


-- === QUERY: q5_age_gender_value ===
-- Key Question 3 (demographics half): commercially underlevered
-- demographic groups, by age band and gender.
SELECT
    CASE
        WHEN age < 25 THEN '18-24'
        WHEN age < 35 THEN '25-34'
        WHEN age < 45 THEN '35-44'
        WHEN age < 55 THEN '45-54'
        WHEN age < 65 THEN '55-64'
        ELSE '65+'
    END AS age_band,
    gender,
    COUNT(*) AS customer_count,
    ROUND(AVG(lifetime_value_proxy), 0) AS avg_lifetime_value_proxy,
    ROUND(100.0 * AVG(loyal_b_flag), 1) AS organic_loyal_pct,
    ROUND(100.0 * AVG(used_promo), 1) AS promo_usage_pct
FROM customers
GROUP BY age_band, gender
ORDER BY age_band, gender;


-- === QUERY: q6_promo_sunset_matrix ===
-- Key Question 4 groundwork: which segments could have promotions safely
-- sunset (high value, low dependency) versus which are promo-reliant and
-- would risk losing volume if discounts were pulled.
SELECT
    value_tier,
    promo_dependency_tier,
    COUNT(*) AS customer_count,
    ROUND(AVG(purchase_amount), 2) AS avg_purchase_amount,
    ROUND(AVG(lifetime_value_proxy), 0) AS avg_lifetime_value_proxy
FROM customers
GROUP BY value_tier, promo_dependency_tier
ORDER BY
    CASE value_tier
        WHEN 'Bronze' THEN 1 WHEN 'Silver' THEN 2
        WHEN 'Gold' THEN 3 WHEN 'Platinum' THEN 4
    END,
    CASE promo_dependency_tier
        WHEN 'No Promo Use' THEN 1 WHEN 'Low Dependency' THEN 2
        WHEN 'Moderate Dependency' THEN 3 WHEN 'High Dependency' THEN 4
    END;


-- === QUERY: q7_ideal_customer_profile ===
-- Key Question 5: What does the brand's ideal customer profile look like?
-- Profiles ONLY the organically-loyal segment (loyal_b_flag = 1) across
-- the demographic and behavioral fields a marketing team would target on.
SELECT
    'Overall Loyal-B Segment' AS profile_cut,
    COUNT(*) AS customer_count,
    ROUND(AVG(age), 1) AS avg_age,
    ROUND(AVG(purchase_amount), 2) AS avg_purchase_amount,
    ROUND(AVG(previous_purchases), 1) AS avg_previous_purchases,
    ROUND(AVG(review_rating), 2) AS avg_review_rating
FROM customers
WHERE loyal_b_flag = 1;

-- Top categories within the ideal-customer segment
SELECT
    category,
    COUNT(*) AS customer_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customers WHERE loyal_b_flag = 1), 1) AS pct_of_segment
FROM customers
WHERE loyal_b_flag = 1
GROUP BY category
ORDER BY customer_count DESC;

-- Top payment methods within the ideal-customer segment
SELECT
    payment_method,
    COUNT(*) AS customer_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customers WHERE loyal_b_flag = 1), 1) AS pct_of_segment
FROM customers
WHERE loyal_b_flag = 1
GROUP BY payment_method
ORDER BY customer_count DESC;

-- Top locations within the ideal-customer segment
SELECT
    location,
    COUNT(*) AS customer_count
FROM customers
WHERE loyal_b_flag = 1
GROUP BY location
ORDER BY customer_count DESC
LIMIT 10;


-- === QUERY: q8_category_funnel ===
-- Power BI "Category funnel" panel: which categories skew toward
-- low-previous-purchase (entry-point) customers versus high-previous-
-- purchase (retention) customers.
SELECT
    category,
    COUNT(*) AS customer_count,
    ROUND(AVG(previous_purchases), 1) AS avg_previous_purchases,
    SUM(CASE WHEN previous_purchases <= 13 THEN 1 ELSE 0 END) AS low_tenure_customers,
    SUM(CASE WHEN previous_purchases >= 38 THEN 1 ELSE 0 END) AS high_tenure_customers
FROM customers
GROUP BY category
ORDER BY avg_previous_purchases DESC;