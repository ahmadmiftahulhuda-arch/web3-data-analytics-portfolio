WITH cleaned_protocols AS (
    SELECT 
        TRIM(name) AS protocol_name,
        CASE 
            WHEN TRIM(symbol) = '' OR TRIM(symbol) = '-' OR symbol IS NULL THEN 'N/A'
            ELSE UPPER(TRIM(symbol))
        END AS protocol_symbol,
        COALESCE(TRIM(category), 'Other') AS protocol_category,
        tvl,
        COALESCE(change_1d, 0.0) AS change_1d,
        COALESCE(change_7d, 0.0) AS change_7d,
        COALESCE(change_30d, 0.0) AS change_30d,
        TRIM(chains) AS chains
    FROM 'defillama_protocols.csv'
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
