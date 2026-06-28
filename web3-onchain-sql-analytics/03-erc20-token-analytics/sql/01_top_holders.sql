-- ============================================================
-- Query 01: Top 20 ERC-20 Token Holders by Net Balance
-- Dataset : bigquery-public-data.crypto_ethereum.token_transfers
-- Token   : Ganti @token_address sesuai token yang dianalisis
-- Author  : Ahmad Miftahul Huda
-- ============================================================

DECLARE token_address STRING DEFAULT '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'; -- USDC

WITH

-- Hitung total token yang masuk ke setiap wallet
inflows AS (
  SELECT
    to_address                          AS wallet,
    SUM(CAST(value AS NUMERIC)) / 1e6   AS total_received   -- USDC = 6 decimals
  FROM `bigquery-public-data.crypto_ethereum.token_transfers`
  WHERE token_address = token_address
    AND to_address IS NOT NULL
    AND to_address != '0x0000000000000000000000000000000000000000'
  GROUP BY wallet
),

-- Hitung total token yang keluar dari setiap wallet
outflows AS (
  SELECT
    from_address                        AS wallet,
    SUM(CAST(value AS NUMERIC)) / 1e6   AS total_sent
  FROM `bigquery-public-data.crypto_ethereum.token_transfers`
  WHERE token_address = token_address
    AND from_address IS NOT NULL
    AND from_address != '0x0000000000000000000000000000000000000000'
  GROUP BY wallet
),

-- Gabungkan inflow & outflow → net balance per wallet
net_balances AS (
  SELECT
    COALESCE(i.wallet, o.wallet)            AS wallet_address,
    COALESCE(i.total_received, 0)           AS total_received,
    COALESCE(o.total_sent, 0)               AS total_sent,
    COALESCE(i.total_received, 0)
      - COALESCE(o.total_sent, 0)           AS net_balance
  FROM inflows  i
  FULL OUTER JOIN outflows o ON i.wallet = o.wallet
)

-- Final: ambil top 20 holder dengan net balance positif
SELECT
  ROW_NUMBER() OVER (ORDER BY net_balance DESC)   AS rank,
  wallet_address,
  ROUND(total_received, 2)                         AS total_received,
  ROUND(total_sent, 2)                             AS total_sent,
  ROUND(net_balance, 2)                            AS net_balance,
  ROUND(
    net_balance / SUM(net_balance) OVER () * 100, 4
  )                                                AS pct_of_total_supply
FROM net_balances
WHERE net_balance > 0
ORDER BY net_balance DESC
LIMIT 20;
