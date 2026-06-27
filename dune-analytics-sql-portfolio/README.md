# Dune Analytics SQL Portfolio

This folder contains SQL queries specifically written for and tested on the Dune Analytics platform to query decentralized protocol states and events.

## Researched Topic: Uniswap Liquidity Pool Performance Analysis

### Business & Protocol Case
An investigation into the performance of Uniswap V3 Liquidity Pools (e.g., USDC/WETH 0.05% pool). The goal is to track trade volume, fees generated, and analyze liquidity provider (LP) profitability under different market conditions.

### Rationale
Analyzing DEX pools is a core requirement for DeFi analysts **because** liquidity is the lifeblood of decentralized finance. Understanding pool dynamics helps protocol designers set optimal swap fees and liquidity rewards.

### Data Sources
*   **Dune Analytics**: Using the `uniswap_v3_ethereum.Pair_evt_Swap` and `uniswap_v3_ethereum.Pair_evt_Mint` event logs.

### Key Metrics to Analyze
*   Daily trade volume per pool.
*   Accumulated fees earned by liquidity providers (LP fees).
*   Active liquidity range concentrations (Ticks) and identifying where most trades occur.
