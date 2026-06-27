-- =====================================================================
-- DeFi Market Concentration Analysis (Herfindahl-Hirschman Index - HHI)
-- =====================================================================
-- This query calculates the HHI score of the DeFi ecosystem.
-- HHI is calculated by summing the squares of the market share of each
-- protocol.
--   HHI < 1,500  : Highly competitive (decentralized)
--   HHI 1.5K-2.5K: Moderately concentrated
--   HHI > 2,500  : Highly concentrated (monopolistic)
-- =====================================================================

WITH market_share AS (
    SELECT name, 
           tvl,
           tvl * 100.0 / SUM(tvl) OVER() AS share_pct
    FROM 'defillama_protocols.csv'
    WHERE category != 'CEX' 
      AND tvl > 0
)
SELECT SUM(share_pct * share_pct) AS hhi_score
FROM market_share;
