-- ============================================================
-- Query 03: Whale Wallet Movement Detection
-- Definisi whale: transfer tunggal > 100,000 token (USDC = $100K)
-- Tracking: kapan whale masuk/keluar, ke exchange atau ke wallet lain?
-- Author  : Ahmad Miftahul Huda
-- ============================================================

DECLARE token_address STRING DEFAULT '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48';
DECLARE whale_threshold NUMERIC DEFAULT 100000;  -- $100K minimum untuk USDC
DECLARE lookback_days INT64 DEFAULT 30;

WITH

-- Label exchange addresses yang diketahui (CEX hot wallets)
known_exchanges AS (
  SELECT address, exchange_name FROM UNNEST([
    STRUCT('0x28c6c06298d514db089934071355e5743bf21d60' AS address, 'Binance'     AS exchange_name),
    STRUCT('0x21a31ee1afc51d94c2efccaa2092ad1028285549',              'Binance'    ),
    STRUCT('0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be',              'Binance'    ),
    STRUCT('0xfe9e8709d3215310075d67e3ed32a380ccf451c8',              'Binance'    ),
    STRUCT('0x6cc5f688a315f3dc28a7781717a9a798a59fda7b',              'OKX'        ),
    STRUCT('0x6cfc5f688a315f3dc28a7781717a9a798a59fda7',              'OKX'        ),
    STRUCT('0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43',              'Coinbase'   ),
    STRUCT('0x503828976d22510aad0201ac7ec88293211d23da',              'Coinbase'   ),
    STRUCT('0x77134cbc06cb00b66f4c7e623d5fdbf6777635ec',              'Coinbase'   ),
    STRUCT('0x2910543af39aba0cd09dbb2d50200b3e800a63d2',              'Kraken'     ),
    STRUCT('0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13',              'Kraken'     ),
    STRUCT('0xe853c56864a2ebe4576a807d26fdc4a0ada51919',              'Bybit'      ),
    STRUCT('0x1fd169a4f5c59acf79d0fd5d91d1201ef1bce9f1',              'Bybit'      )
  ])
),

-- Ambil semua whale transfer dalam periode lookback
whale_transfers AS (
  SELECT
    t.transaction_hash,
    t.block_timestamp,
    DATE(t.block_timestamp)                       AS transfer_date,
    t.from_address,
    t.to_address,
    CAST(t.value AS NUMERIC) / 1e6               AS amount,
    e_from.exchange_name                          AS from_exchange,
    e_to.exchange_name                            AS to_exchange,

    -- Klasifikasi transfer
    CASE
      WHEN e_from.exchange_name IS NOT NULL AND e_to.exchange_name IS NOT NULL
        THEN 'exchange_to_exchange'
      WHEN e_from.exchange_name IS NOT NULL
        THEN 'exchange_outflow'          -- Token keluar dari exchange → bullish signal
      WHEN e_to.exchange_name IS NOT NULL
        THEN 'exchange_inflow'           -- Token masuk ke exchange → potential sell
      ELSE 'wallet_to_wallet'            -- Transfer antar wallet — whale accumulation
    END                                           AS transfer_type

  FROM `bigquery-public-data.crypto_ethereum.token_transfers` t
  LEFT JOIN known_exchanges e_from ON t.from_address = e_from.address
  LEFT JOIN known_exchanges e_to   ON t.to_address   = e_to.address

  WHERE t.token_address  = token_address
    AND CAST(t.value AS NUMERIC) / 1e6 >= whale_threshold
    AND t.block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL lookback_days DAY)
    AND t.from_address != '0x0000000000000000000000000000000000000000'
    AND t.to_address   != '0x0000000000000000000000000000000000000000'
)

-- Summary: distribusi transfer per tipe dan per hari
SELECT
  transfer_date,
  transfer_type,
  COUNT(*)                                        AS tx_count,
  ROUND(SUM(amount), 2)                           AS total_volume,
  ROUND(AVG(amount), 2)                           AS avg_amount,
  ROUND(MAX(amount), 2)                           AS largest_transfer,
  COUNT(DISTINCT from_address)                    AS unique_senders,
  COUNT(DISTINCT to_address)                      AS unique_receivers
FROM whale_transfers
GROUP BY transfer_date, transfer_type
ORDER BY transfer_date DESC, total_volume DESC;
