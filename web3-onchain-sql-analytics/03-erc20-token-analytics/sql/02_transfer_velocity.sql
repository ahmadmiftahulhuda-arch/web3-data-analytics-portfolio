-- ============================================================
-- Query 02: Token Transfer Velocity — 30 Hari Terakhir
-- Velocity = total volume transferred / estimated circulating supply
-- Semakin tinggi velocity → token lebih aktif berpindah tangan
-- Author  : Ahmad Miftahul Huda
-- ============================================================

DECLARE token_address STRING DEFAULT '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'; -- USDC
DECLARE lookback_days INT64 DEFAULT 30;

WITH

-- Volume transfer per hari
daily_volume AS (
  SELECT
    DATE(block_timestamp)                          AS transfer_date,
    COUNT(*)                                       AS transfer_count,
    COUNT(DISTINCT from_address)                   AS unique_senders,
    COUNT(DISTINCT to_address)                     AS unique_receivers,
    COUNT(DISTINCT from_address)
      + COUNT(DISTINCT to_address)                 AS total_unique_wallets,
    SUM(CAST(value AS NUMERIC)) / 1e6             AS daily_volume_usd,   -- asumsi USDC ≈ $1
    AVG(CAST(value AS NUMERIC)) / 1e6             AS avg_transfer_size,
    MAX(CAST(value AS NUMERIC)) / 1e6             AS max_transfer_size,
    PERCENTILE_CONT(CAST(value AS NUMERIC) / 1e6, 0.5)
      OVER (PARTITION BY DATE(block_timestamp))    AS median_transfer_size
  FROM `bigquery-public-data.crypto_ethereum.token_transfers`
  WHERE token_address = token_address
    AND block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL lookback_days DAY)
    AND from_address != '0x0000000000000000000000000000000000000000'
    AND to_address   != '0x0000000000000000000000000000000000000000'
  GROUP BY transfer_date
),

-- Hitung 7-day rolling average untuk smoothing
rolling_avg AS (
  SELECT
    transfer_date,
    transfer_count,
    unique_senders,
    unique_receivers,
    daily_volume_usd,
    avg_transfer_size,
    max_transfer_size,
    AVG(daily_volume_usd) OVER (
      ORDER BY transfer_date
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )                                              AS rolling_7d_avg_volume,
    AVG(transfer_count) OVER (
      ORDER BY transfer_date
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )                                              AS rolling_7d_avg_tx
  FROM daily_volume
)

SELECT
  transfer_date,
  transfer_count,
  unique_senders,
  unique_receivers,
  ROUND(daily_volume_usd, 2)           AS daily_volume_usd,
  ROUND(avg_transfer_size, 2)          AS avg_transfer_size,
  ROUND(max_transfer_size, 2)          AS max_transfer_size,
  ROUND(rolling_7d_avg_volume, 2)      AS rolling_7d_avg_volume,
  ROUND(rolling_7d_avg_tx, 0)          AS rolling_7d_avg_tx,
  -- WoW growth
  ROUND(
    (daily_volume_usd - LAG(daily_volume_usd, 7) OVER (ORDER BY transfer_date))
    / NULLIF(LAG(daily_volume_usd, 7) OVER (ORDER BY transfer_date), 0) * 100,
    2
  )                                    AS volume_wow_pct_change
FROM rolling_avg
ORDER BY transfer_date DESC;
