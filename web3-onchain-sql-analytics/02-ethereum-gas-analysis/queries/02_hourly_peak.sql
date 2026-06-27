-- =====================================================================
-- Hourly gas fee pattern — find cheapest hours to transact
-- Hours in UTC. For WIB: add 7 hours to UTC value.
-- =====================================================================
SELECT
  EXTRACT(HOUR FROM block_timestamp) AS hour_utc,
  -- WIB conversion note for Indonesian audience
  MOD(EXTRACT(HOUR FROM block_timestamp) + 7, 24) AS hour_wib,
  COUNT(*) AS tx_count,
  APPROX_QUANTILES(gas_price / 1e9, 100)[OFFSET(50)] AS median_gas_gwei,
  -- Relative to daily average
  APPROX_QUANTILES(gas_price / 1e9, 100)[OFFSET(50)] /
    AVG(APPROX_QUANTILES(gas_price / 1e9, 100)[OFFSET(50)])
      OVER () AS vs_daily_avg
FROM `bigquery-public-data.crypto_ethereum.transactions`
WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND gas_price > 0
GROUP BY 1, 2
ORDER BY median_gas_gwei ASC;
