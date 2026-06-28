-- ============================================================
-- Query 01: Stablecoin Supply Overview
-- Source  : ../output/stablecoin_supply_history.parquet
-- Engine  : DuckDB (jalankan via analyze.py)
-- Author  : Ahmad Miftahul Huda
-- ============================================================

WITH

-- Total supply per stablecoin per hari (sum semua chain)
daily_supply AS (
  SELECT
    date,
    symbol,
    SUM(supply_usd)     AS total_supply_usd
  FROM read_parquet('../output/stablecoin_supply_history.parquet')
  GROUP BY date, symbol
),

-- Latest snapshot
latest_date AS (
  SELECT MAX(date) AS max_date
  FROM daily_supply
),

-- Supply latest + 30D ago untuk perbandingan
snapshot AS (
  SELECT
    d.symbol,
    d.total_supply_usd                                          AS current_supply,
    d30.total_supply_usd                                        AS supply_30d_ago,
    d90.total_supply_usd                                        AS supply_90d_ago
  FROM daily_supply d
  JOIN latest_date l ON d.date = l.max_date

  LEFT JOIN daily_supply d30
    ON d30.symbol = d.symbol
    AND d30.date = (SELECT max_date - INTERVAL '30 days' FROM latest_date)

  LEFT JOIN daily_supply d90
    ON d90.symbol = d.symbol
    AND d90.date = (SELECT max_date - INTERVAL '90 days' FROM latest_date)
)

SELECT
  symbol,
  ROUND(current_supply / 1e9, 3)                              AS current_supply_bn,
  ROUND(supply_30d_ago / 1e9, 3)                              AS supply_30d_ago_bn,
  ROUND(supply_90d_ago / 1e9, 3)                              AS supply_90d_ago_bn,

  -- 30D change
  ROUND((current_supply - supply_30d_ago)
        / NULLIF(supply_30d_ago, 0) * 100, 2)                 AS pct_change_30d,

  -- 90D change
  ROUND((current_supply - supply_90d_ago)
        / NULLIF(supply_90d_ago, 0) * 100, 2)                 AS pct_change_90d,

  -- Market share
  ROUND(current_supply
        / SUM(current_supply) OVER () * 100, 2)               AS market_share_pct,

  CASE
    WHEN (current_supply - supply_30d_ago)
         / NULLIF(supply_30d_ago, 0) > 0.05  THEN '📈 Expanding'
    WHEN (current_supply - supply_30d_ago)
         / NULLIF(supply_30d_ago, 0) < -0.05 THEN '📉 Contracting'
    ELSE                                           '➡️  Stable'
  END                                                          AS supply_trend

FROM snapshot
ORDER BY current_supply DESC;
