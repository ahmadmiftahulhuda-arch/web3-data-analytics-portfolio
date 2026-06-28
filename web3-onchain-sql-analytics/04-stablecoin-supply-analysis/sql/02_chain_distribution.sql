-- ============================================================
-- Query 02: Stablecoin Distribution per Chain
-- Pertanyaan: Di chain mana masing-masing stablecoin paling dominan?
-- Source  : ../output/stablecoin_supply_history.parquet
-- Engine  : DuckDB
-- Author  : Ahmad Miftahul Huda
-- ============================================================

WITH

-- Supply terbaru per stablecoin per chain
latest AS (
  SELECT
    s.symbol,
    s.chain,
    s.supply_usd,
    s.date
  FROM read_parquet('../output/stablecoin_supply_history.parquet') s
  WHERE s.date = (
    SELECT MAX(date)
    FROM read_parquet('../output/stablecoin_supply_history.parquet')
  )
),

-- Total per stablecoin untuk hitung market share per chain
stablecoin_totals AS (
  SELECT symbol, SUM(supply_usd) AS total_supply
  FROM latest
  GROUP BY symbol
),

-- Total per chain (semua stablecoin)
chain_totals AS (
  SELECT chain, SUM(supply_usd) AS chain_total_supply
  FROM latest
  GROUP BY chain
),

-- Join semua
enriched AS (
  SELECT
    l.symbol,
    l.chain,
    l.supply_usd,
    st.total_supply                                           AS stablecoin_total,
    ct.chain_total_supply,

    -- % supply token ini di chain ini vs total supply token
    ROUND(l.supply_usd / NULLIF(st.total_supply, 0) * 100, 2) AS pct_of_token_supply,

    -- % token ini vs total semua stablecoin di chain ini
    ROUND(l.supply_usd / NULLIF(ct.chain_total_supply, 0) * 100, 2) AS dominance_in_chain,

    -- Rank per chain
    RANK() OVER (PARTITION BY l.chain ORDER BY l.supply_usd DESC) AS rank_in_chain,

    -- Rank per stablecoin
    RANK() OVER (PARTITION BY l.symbol ORDER BY l.supply_usd DESC) AS rank_of_chain_for_token

  FROM latest l
  JOIN stablecoin_totals st ON l.symbol = st.symbol
  JOIN chain_totals ct      ON l.chain  = ct.chain
  WHERE l.supply_usd > 1000000  -- filter chain dengan < $1M (noise)
)

-- Output: distribusi lengkap
SELECT
  chain,
  symbol,
  ROUND(supply_usd / 1e9, 4)                                 AS supply_bn,
  pct_of_token_supply,
  dominance_in_chain,
  rank_in_chain,
  rank_of_chain_for_token,

  -- Label dominansi
  CASE
    WHEN dominance_in_chain >= 50 THEN '🥇 Dominant'
    WHEN dominance_in_chain >= 25 THEN '🥈 Major'
    WHEN dominance_in_chain >= 10 THEN '🥉 Significant'
    ELSE                                '📌 Minor'
  END                                                         AS dominance_label

FROM enriched
ORDER BY chain, supply_usd DESC;
