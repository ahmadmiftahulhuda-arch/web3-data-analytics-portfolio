-- ============================================================
-- Query 05: Net Mint vs Burn Analysis
-- Supply naik = net mint (demand tinggi / collateral masuk)
-- Supply turun = net burn (redemption / demand turun)
-- Author  : Ahmad Miftahul Huda
-- ============================================================

WITH

-- Daily supply per stablecoin
daily_supply AS (
  SELECT
    date,
    symbol,
    SUM(supply_usd)     AS total_supply
  FROM read_parquet('../output/stablecoin_supply_history.parquet')
  GROUP BY date, symbol
),

-- Hitung daily delta (mint - burn net)
daily_delta AS (
  SELECT
    date,
    symbol,
    total_supply,
    total_supply - LAG(total_supply) OVER (
      PARTITION BY symbol ORDER BY date
    )                                                         AS net_delta,   -- positif = mint, negatif = burn
    LAG(total_supply) OVER (
      PARTITION BY symbol ORDER BY date
    )                                                         AS prev_supply
  FROM daily_supply
),

-- Weekly aggregation untuk smoother view
weekly_flow AS (
  SELECT
    DATE_TRUNC('week', date)                                  AS week_start,
    symbol,
    SUM(CASE WHEN net_delta > 0 THEN net_delta ELSE 0 END)   AS weekly_minted,
    SUM(CASE WHEN net_delta < 0 THEN ABS(net_delta) ELSE 0 END) AS weekly_burned,
    SUM(net_delta)                                            AS weekly_net_flow,
    AVG(total_supply)                                         AS avg_weekly_supply,
    COUNT(*)                                                  AS days_in_week
  FROM daily_delta
  WHERE net_delta IS NOT NULL
    AND date >= CURRENT_DATE - INTERVAL '90 days'
  GROUP BY week_start, symbol
),

-- Identifikasi periode expansion vs contraction
phase_labels AS (
  SELECT
    week_start,
    symbol,
    ROUND(weekly_minted / 1e9, 4)                            AS weekly_minted_bn,
    ROUND(weekly_burned / 1e9, 4)                            AS weekly_burned_bn,
    ROUND(weekly_net_flow / 1e9, 4)                          AS weekly_net_flow_bn,
    ROUND(avg_weekly_supply / 1e9, 3)                        AS avg_supply_bn,
    ROUND(weekly_net_flow / NULLIF(avg_weekly_supply, 0) * 100, 3) AS net_flow_pct,

    -- Rolling 4-week trend
    SUM(weekly_net_flow) OVER (
      PARTITION BY symbol
      ORDER BY week_start
      ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    )                                                         AS rolling_4w_net_flow,

    CASE
      WHEN weekly_net_flow > 0
           AND weekly_minted > ABS(weekly_burned) * 1.5  THEN '🟢 Strong Expansion'
      WHEN weekly_net_flow > 0                            THEN '📈 Mild Expansion'
      WHEN weekly_net_flow < 0
           AND weekly_burned > weekly_minted * 1.5        THEN '🔴 Strong Contraction'
      WHEN weekly_net_flow < 0                            THEN '📉 Mild Contraction'
      ELSE                                                     '➡️  Neutral'
    END                                                       AS market_phase
  FROM weekly_flow
)

SELECT
  week_start,
  symbol,
  weekly_minted_bn,
  weekly_burned_bn,
  weekly_net_flow_bn,
  net_flow_pct,
  avg_supply_bn,
  ROUND(rolling_4w_net_flow / 1e9, 3)                       AS rolling_4w_net_flow_bn,
  market_phase
FROM phase_labels
ORDER BY symbol, week_start DESC;
