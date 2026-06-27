-- =====================================================================
-- SQL DATA CLEANING & ANALYTICS: DeFi TVL Comparison
-- =====================================================================
-- This query performs data cleaning using a Common Table Expression (CTE)
-- to handle NULL values, trim whitespaces, standardize symbols,
-- and filter out non-DeFi data (such as CEX reserves).
--
-- After cleaning, it queries the top 10 decentralized protocols by TVL.
-- =====================================================================

WITH cleaned_protocols AS (
    SELECT 
        -- 1. Clean name and remove extra whitespaces
        TRIM(name) AS protocol_name,
        
        -- 2. Standardize symbols, handle missing symbols, and uppercase them
        CASE 
            WHEN TRIM(symbol) = '' OR TRIM(symbol) = '-' OR symbol IS NULL THEN 'N/A'
            ELSE UPPER(TRIM(symbol))
        END AS protocol_symbol,
        
        -- 3. Handle NULL/empty categories
        COALESCE(TRIM(category), 'Other') AS protocol_category,
        
        -- 4. Keep raw TVL
        tvl,
        
        -- 5. Handle missing values (NULLs) in change percentages
        COALESCE(change_1d, 0.0) AS change_1d,
        COALESCE(change_7d, 0.0) AS change_7d,
        COALESCE(change_30d, 0.0) AS change_30d,
        
        -- 6. Clean chains data
        TRIM(chains) AS chains
    FROM 'defillama_protocols.csv'
    
    -- 7. FILTER OUT CENTRALIZED EXCHANGES (CEX)
    -- We exclude CEXs because exchange reserves are not DeFi protocols.
    -- We also exclude records with zero/negative TVL.
    WHERE category != 'CEX' 
      AND tvl > 0
)
SELECT 
    protocol_name, 
    protocol_symbol, 
    protocol_category, 
    tvl, 
    change_7d
FROM cleaned_protocols
ORDER BY tvl DESC
LIMIT 10;