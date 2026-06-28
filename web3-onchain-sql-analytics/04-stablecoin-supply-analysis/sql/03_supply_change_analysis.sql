-- ============================================================
-- Query 03: Supply Change Analysis — WoW & MoM
-- Metrik: perubahan supply mingguan dan bulanan per stablecoin
-- Author  : Ahmad Miftahul Huda
-- ============================================================

WITH

daily_supply AS (
  SELECT
    date,
    symbol,
    SUM(supply_usd) AS total_supply
  FROM read_parquet('../output/stablecoin_supply_history.parquet')
  GROUP BY date, symbol
),

-- Tambahkan lag untuk WoW (7 hari) dan MoM (30 hari)
with_lags AS (
  SELECT
    date,
    symbol,
    total_supply,
    LAG(total_supply, 7)  OVER (PARTITION BY symbol ORDER BY date) AS supply_7d_ago,
    LAG(total_supply, 30) OVER (PARTITION BY symbol ORDER BY date) AS supply_30d_ago,
    LAG(total_supply, 1)  OVER (PARTITION BY symbol ORDER BY date) AS supply_1d_ago
  FROM daily_supply
)

SELECT
  date,
  symbol,
  ROUND(total_supply / 1e9, 4)                                     AS supply_bn,

  -- Day-over-Day
  ROUND((total_supply - supply_1d_ago)
        / NULLIF(supply_1d_ago, 0) * 100, 3)                       AS dod_pct,

  -- Week-over-Week
  ROUND((total_supply - supply_7d_ago)
        / NULLIF(supply_7d_ago, 0) * 100, 3)                       AS wow_pct,

  -- Month-over-Month
  ROUND((total_supply - supply_30d_ago)
        / NULLIF(supply_30d_ago, 0) * 100, 3)                      AS mom_pct,

  -- Absolute changes
  ROUND((total_supply - supply_7d_ago)  / 1e9, 4)                  AS wow_abs_change_bn,
  ROUND((total_supply - supply_30d_ago) / 1e9, 4)                  AS mom_abs_change_bn,

  -- Label trend
  CASE
    WHEN wow_pct > 5  THEN '🚀 Strong Growth'
    WHEN wow_pct > 2  THEN '📈 Moderate Growth'
    WHEN wow_pct > 0  THEN '🟢 Slight Growth'
    WHEN wow_pct > -2 THEN '🟡 Slight Decline'
    WHEN wow_pct > -5 THEN '📉 Moderate Decline'
    ELSE                   '🔴 Strong Decline'
  END                                                               AS wow_trend_label

FROM with_lags
WHERE supply_7d_ago IS NOT NULL
  AND date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY symbol, date DESC;
