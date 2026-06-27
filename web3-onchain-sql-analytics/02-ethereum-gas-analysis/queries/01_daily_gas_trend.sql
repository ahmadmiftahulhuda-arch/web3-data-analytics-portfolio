-- =====================================================================
-- Daily median gas price trend (30-day window)
-- We use MEDIAN not AVG because MEV bots skew the average upward.
-- Block 12965000 = EIP-1559 activation (August 5, 2021)
-- =====================================================================
SELECT
  DATE_TRUNC(block_timestamp, DAY) AS day,
  COUNT(*) AS total_tx,

  -- Median is more representative than mean for gas data
  APPROX_QUANTILES(gas_price / 1e9, 100)[OFFSET(50)] AS median_gas_gwei,
  AVG(gas_price / 1e9) AS avg_gas_gwei,

  -- Flag EIP-1559 era
  CASE
    WHEN block_number >= 12965000 THEN 'post_eip1559'
    ELSE 'pre_eip1559'
  END AS fee_era

FROM `bigquery-public-data.crypto_ethereum.transactions`
WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND gas_price > 0
GROUP BY 1, 5
ORDER BY 1 DESC;
