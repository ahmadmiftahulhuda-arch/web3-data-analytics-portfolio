-- ============================================================
-- Query 04: Stablecoin Depeg Early Warning Detection
-- Deteksi kapan harga stablecoin menyimpang > 0.3% dari $1.00
-- Source  : ../output/stablecoins_metadata.parquet (price field)
--           + manual price data jika diperlukan
-- Engine  : DuckDB
-- Author  : Ahmad Miftahul Huda
-- ============================================================

-- Catatan: DefiLlama /stablecoins endpoint menyediakan current price.
-- Untuk historical price, kita gunakan supply change sebagai proxy:
-- Jika supply turun tajam + price drop → kemungkinan depeg event.

WITH

-- Load metadata terbaru (berisi harga)
current_prices AS (
  SELECT
    symbol,
    price,
    circulating                                               AS current_supply_usd,
    ABS(price - 1.0)                                          AS price_deviation,
    ROUND((price - 1.0) * 100, 4)                             AS pct_deviation_from_peg
  FROM read_parquet('../output/stablecoins_metadata.parquet')
  WHERE price IS NOT NULL
    AND price > 0
),

-- Supply history untuk deteksi pola stress (supply drop = potential redemption)
supply_history AS (
  SELECT
    symbol,
    date,
    SUM(supply_usd)                                           AS total_supply,
    LAG(SUM(supply_usd), 1) OVER (
      PARTITION BY symbol ORDER BY date
    )                                                         AS prev_day_supply,
    LAG(SUM(supply_usd), 7) OVER (
      PARTITION BY symbol ORDER BY date
    )                                                         AS prev_week_supply
  FROM read_parquet('../output/stablecoin_supply_history.parquet')
  GROUP BY symbol, date
),

-- Hitung daily supply change
supply_changes AS (
  SELECT
    symbol,
    date,
    total_supply,
    ROUND((total_supply - prev_day_supply)
          / NULLIF(prev_day_supply, 0) * 100, 4)             AS daily_change_pct,
    ROUND((total_supply - prev_week_supply)
          / NULLIF(prev_week_supply, 0) * 100, 4)             AS weekly_change_pct
  FROM supply_history
  WHERE date >= CURRENT_DATE - INTERVAL '30 days'
),

-- Flag hari-hari dengan supply drop tajam (potential stress event)
stress_events AS (
  SELECT
    symbol,
    date,
    total_supply,
    daily_change_pct,
    weekly_change_pct,
    CASE
      WHEN daily_change_pct  < -5  THEN '🔴 Critical Drop (>5% daily)'
      WHEN daily_change_pct  < -2  THEN '🟡 Significant Drop (2-5% daily)'
      WHEN weekly_change_pct < -10 THEN '🟠 Weekly Stress (>10% weekly)'
      ELSE NULL
    END                                                       AS stress_flag
  FROM supply_changes
  WHERE daily_change_pct IS NOT NULL
)

-- === OUTPUT 1: Current price status semua stablecoin ===
SELECT
  'PRICE_STATUS'                                              AS report_type,
  symbol,
  ROUND(price, 6)                                             AS current_price,
  ROUND(pct_deviation_from_peg, 4)                            AS pct_from_peg,
  CASE
    WHEN ABS(pct_deviation_from_peg) < 0.1  THEN '✅ On Peg'
    WHEN ABS(pct_deviation_from_peg) < 0.3  THEN '🟡 Minor Deviation'
    WHEN ABS(pct_deviation_from_peg) < 1.0  THEN '🟠 Warning: Off Peg'
    ELSE                                          '🔴 DEPEG ALERT'
  END                                                         AS peg_status,
  CASE
    WHEN price > 1.0 THEN 'Premium (over peg)'
    WHEN price < 1.0 THEN 'Discount (under peg)'
    ELSE                   'At peg'
  END                                                         AS price_direction,
  ROUND(current_supply_usd / 1e9, 3)                         AS current_supply_bn,
  NULL::DATE                                                  AS event_date,
  NULL::DOUBLE                                                AS daily_change_pct,
  NULL                                                        AS stress_flag
FROM current_prices
WHERE symbol IN ('USDC', 'USDT', 'DAI', 'FRAX', 'TUSD', 'LUSD', 'CRVUSD')

UNION ALL

-- === OUTPUT 2: Historical stress events (30 hari) ===
SELECT
  'STRESS_EVENT'                                              AS report_type,
  symbol,
  NULL                                                        AS current_price,
  NULL                                                        AS pct_from_peg,
  NULL                                                        AS peg_status,
  NULL                                                        AS price_direction,
  ROUND(total_supply / 1e9, 3)                               AS current_supply_bn,
  date                                                        AS event_date,
  daily_change_pct,
  stress_flag
FROM stress_events
WHERE stress_flag IS NOT NULL

ORDER BY report_type, symbol, event_date DESC;
