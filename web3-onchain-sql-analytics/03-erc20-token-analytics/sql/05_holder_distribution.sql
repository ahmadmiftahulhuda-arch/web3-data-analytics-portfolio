-- ============================================================
-- Query 05: Holder Distribution & Concentration Analysis
-- Ukuran: Gini coefficient, percentile distribution, whale vs retail ratio
-- Makin tinggi Gini (→1.0) → makin terkonsentrasi di sedikit wallet
-- Author  : Ahmad Miftahul Huda
-- ============================================================

DECLARE token_address STRING DEFAULT '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48';

WITH

-- Net balance setiap wallet (sama seperti query 01 tapi untuk semua holder)
net_balances AS (
  SELECT wallet, SUM(delta) AS net_balance
  FROM (
    SELECT to_address   AS wallet,  CAST(value AS NUMERIC) / 1e6 AS delta
    FROM `bigquery-public-data.crypto_ethereum.token_transfers`
    WHERE token_address = token_address
      AND to_address != '0x0000000000000000000000000000000000000000'

    UNION ALL

    SELECT from_address AS wallet, -CAST(value AS NUMERIC) / 1e6 AS delta
    FROM `bigquery-public-data.crypto_ethereum.token_transfers`
    WHERE token_address = token_address
      AND from_address != '0x0000000000000000000000000000000000000000'
  )
  GROUP BY wallet
  HAVING SUM(delta) > 0.01   -- filter dust wallets
),

-- Klasifikasi tier holder
holder_tiers AS (
  SELECT
    wallet,
    net_balance,
    CASE
      WHEN net_balance >= 10000000  THEN '🐳 Mega Whale (>$10M)'
      WHEN net_balance >= 1000000   THEN '🦈 Whale ($1M–$10M)'
      WHEN net_balance >= 100000    THEN '🐬 Large ($100K–$1M)'
      WHEN net_balance >= 10000     THEN '🐟 Medium ($10K–$100K)'
      WHEN net_balance >= 1000      THEN '🦐 Small ($1K–$10K)'
      ELSE                               '🌱 Micro (<$1K)'
    END                           AS holder_tier,
    PERCENT_RANK() OVER (ORDER BY net_balance)  AS percentile_rank
  FROM net_balances
),

-- Aggregasi per tier
tier_summary AS (
  SELECT
    holder_tier,
    COUNT(*)                                      AS wallet_count,
    ROUND(SUM(net_balance), 2)                    AS tier_total_balance,
    ROUND(AVG(net_balance), 2)                    AS avg_balance,
    ROUND(MIN(net_balance), 2)                    AS min_balance,
    ROUND(MAX(net_balance), 2)                    AS max_balance
  FROM holder_tiers
  GROUP BY holder_tier
),

-- Total supply untuk persentase
total AS (
  SELECT
    COUNT(*)         AS total_holders,
    SUM(net_balance) AS total_supply
  FROM net_balances
),

-- Gini coefficient approximation menggunakan BigQuery
-- Formula: G = (2 * sum(rank * balance) / (n * total)) - (n+1)/n
gini_calc AS (
  SELECT
    (2 * SUM(ROW_NUMBER() OVER (ORDER BY net_balance) * net_balance)
      / (COUNT(*) * SUM(net_balance))
    ) - (COUNT(*) + 1) / COUNT(*)                AS gini_coefficient
  FROM net_balances
)

-- Final output: distribusi per tier + Gini
SELECT
  t.holder_tier,
  t.wallet_count,
  ROUND(t.wallet_count / tt.total_holders * 100, 2)       AS pct_of_holders,
  t.tier_total_balance,
  ROUND(t.tier_total_balance / tt.total_supply * 100, 4)  AS pct_of_supply,
  t.avg_balance,
  t.min_balance,
  t.max_balance,
  tt.total_holders,
  ROUND(tt.total_supply, 2)                                AS total_supply,
  ROUND(gc.gini_coefficient, 4)                            AS gini_coefficient,
  CASE
    WHEN gc.gini_coefficient > 0.9 THEN 'Sangat Terkonsentrasi'
    WHEN gc.gini_coefficient > 0.7 THEN 'Terkonsentrasi'
    WHEN gc.gini_coefficient > 0.5 THEN 'Moderat'
    ELSE                                 'Terdistribusi'
  END                                                      AS concentration_label
FROM tier_summary t
CROSS JOIN total tt
CROSS JOIN gini_calc gc
ORDER BY t.max_balance DESC;
