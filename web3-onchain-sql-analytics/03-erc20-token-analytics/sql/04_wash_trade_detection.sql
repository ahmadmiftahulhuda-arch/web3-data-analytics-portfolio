-- ============================================================
-- Query 04: Wash Trade & Circular Transfer Detection
-- Metode: identifikasi wallet yang mengirim DAN menerima token
--         dari wallet yang sama dalam window waktu singkat (< 1 jam)
-- Author  : Ahmad Miftahul Huda
-- ============================================================

DECLARE token_address STRING DEFAULT '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48';
DECLARE lookback_days INT64 DEFAULT 30;
DECLARE time_window_minutes INT64 DEFAULT 60;   -- deteksi dalam window 1 jam

WITH

-- Ambil semua transfer dalam periode
transfers AS (
  SELECT
    transaction_hash,
    block_timestamp,
    from_address,
    to_address,
    CAST(value AS NUMERIC) / 1e6     AS amount
  FROM `bigquery-public-data.crypto_ethereum.token_transfers`
  WHERE token_address = token_address
    AND block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL lookback_days DAY)
    AND from_address != '0x0000000000000000000000000000000000000000'
    AND to_address   != '0x0000000000000000000000000000000000000000'
),

-- Self-join: cari pasangan A→B dan B→A dalam window waktu singkat
circular_pairs AS (
  SELECT
    t1.from_address                               AS wallet_a,
    t1.to_address                                 AS wallet_b,
    t1.block_timestamp                            AS first_transfer_time,
    t2.block_timestamp                            AS return_transfer_time,
    TIMESTAMP_DIFF(t2.block_timestamp,
                   t1.block_timestamp, MINUTE)    AS minutes_between,
    t1.amount                                     AS amount_sent,
    t2.amount                                     AS amount_returned,
    ABS(t1.amount - t2.amount)                    AS amount_difference,
    t1.transaction_hash                           AS tx_hash_forward,
    t2.transaction_hash                           AS tx_hash_return
  FROM transfers t1
  JOIN transfers t2
    ON  t1.from_address = t2.to_address           -- A mengirim ke B, B mengirim balik ke A
    AND t1.to_address   = t2.from_address
    AND t2.block_timestamp > t1.block_timestamp   -- return terjadi setelah forward
    AND TIMESTAMP_DIFF(t2.block_timestamp,
                       t1.block_timestamp,
                       MINUTE) <= time_window_minutes
),

-- Flagging: hitung berapa kali pasangan wallet ini melakukan circular transfer
suspicious_pairs AS (
  SELECT
    wallet_a,
    wallet_b,
    COUNT(*)                                      AS circular_tx_count,
    ROUND(SUM(amount_sent), 2)                    AS total_volume_circulated,
    ROUND(AVG(minutes_between), 1)                AS avg_minutes_between,
    ROUND(MIN(minutes_between), 1)                AS fastest_return_minutes,
    ROUND(AVG(amount_difference), 2)              AS avg_amount_difference,
    MIN(first_transfer_time)                      AS first_seen,
    MAX(return_transfer_time)                     AS last_seen,

    -- Skor kecurigaan (0–100): makin tinggi makin mencurigakan
    LEAST(100,
      ROUND(
        (COUNT(*) * 20)                           -- frekuensi
        + (60 - AVG(minutes_between))             -- kecepatan return
        + (CASE WHEN AVG(amount_difference) < 1
                THEN 20 ELSE 0 END)               -- jumlah hampir identik
      , 0)
    )                                             AS suspicion_score

  FROM circular_pairs
  GROUP BY wallet_a, wallet_b
  HAVING COUNT(*) >= 2                           -- minimal 2 kali circular untuk flag
)

SELECT
  wallet_a,
  wallet_b,
  circular_tx_count,
  total_volume_circulated,
  avg_minutes_between,
  fastest_return_minutes,
  avg_amount_difference,
  suspicion_score,
  CASE
    WHEN suspicion_score >= 80 THEN '🔴 High Risk'
    WHEN suspicion_score >= 50 THEN '🟡 Medium Risk'
    ELSE                             '🟢 Low Risk'
  END                                            AS risk_level,
  first_seen,
  last_seen
FROM suspicious_pairs
ORDER BY suspicion_score DESC, total_volume_circulated DESC
LIMIT 100;
