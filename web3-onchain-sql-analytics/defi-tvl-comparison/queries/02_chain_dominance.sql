-- =====================================================================
-- DeFi Multi-Chain vs Single-Chain Dominance Analysis
-- =====================================================================
-- This query determines if TVL is concentrated in multi-chain protocols
-- or single-chain protocols. We check if the 'chains' column contains
-- a comma, indicating support for multiple networks.
-- =====================================================================

SELECT 
    CASE 
        WHEN chains LIKE '%,%' THEN 'Multi-Chain Protocol'
        ELSE 'Single-Chain Protocol'
    END AS protocol_type,
    COUNT(*) AS total_protocols,
    SUM(tvl) AS total_tvl,
    SUM(tvl) * 100.0 / SUM(SUM(tvl)) OVER() AS persentase_tvl
FROM 'defillama_protocols.csv'
WHERE category != 'CEX' 
  AND tvl > 0
GROUP BY 1
ORDER BY total_tvl DESC;
