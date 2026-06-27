# Crypto Transaction Analytics SQL 

This folder is dedicated to transaction-level analysis, wallet profiling, whale tracking, and stablecoin flow monitoring on various blockchains.

## Researched Topic: Whale Wallet Monitoring & Stablecoin Flows

### Business & Protocol Case
An analysis of stablecoin movements (USDT, USDC, DAI) from large-holder wallets (known as "Whales") to Centralized Exchanges (CEXs) such as Binance and Coinbase. The goal is to detect capital inflows/outflows that signal market accumulation or selling pressure.

### Rationale
Tracking whale wallets is highly popular and valuable **because** large-volume movements often predict future price trends or market liquidity shifts. Knowing when whales are dumping stablecoins to buy assets (or vice versa) gives crucial market sentiment signals.

### Data Sources
*   **Dune Analytics / Flipside**: Using token transfer tables (`ethereum.core.ez_token_transfers`).

### Key Metrics to Analyze
*   Daily net flow of stablecoins (Inflows - Outflows) to exchange deposit addresses.
*   Identification of whale wallets transferring more than $1 Million in a single transaction.
*   Historical correlation between massive stablecoin inflows to CEXs and BTC/ETH price movements.
