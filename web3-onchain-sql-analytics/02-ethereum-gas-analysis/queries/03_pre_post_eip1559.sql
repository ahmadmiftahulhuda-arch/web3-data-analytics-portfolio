-- =====================================================================
-- Volatility and predictability comparison: Pre vs Post EIP-1559
-- Block 12965000 = EIP-1559 activation (August 5, 2021)
-- We compare 500,000 blocks before and after the activation.
-- =====================================================================
SELECT
  CASE
    WHEN block_number >= 12965000 THEN 'Post-EIP1559'
    ELSE 'Pre-EIP1559'
  END AS fee_era,
  COUNT(*) AS total_tx,
  -- Average and Median gas price in Gwei
  AVG(gas_price / 1e9) AS avg_gas_price_gwei,
  APPROX_QUANTILES(gas_price / 1e9, 100)[OFFSET(50)] AS median_gas_price_gwei,
  -- Standard deviation measures volatility (predictability)
  STDDEV(gas_price / 1e9) AS stddev_gas_price_gwei,
  -- Max and Min prices
  MAX(gas_price / 1e9) AS max_gas_price_gwei,
  MIN(gas_price / 1e9) AS min_gas_price_gwei
FROM `bigquery-public-data.crypto_ethereum.transactions`
WHERE block_number BETWEEN 12965000 - 500000 AND 12965000 + 500000
  AND gas_price > 0
GROUP BY 1;
