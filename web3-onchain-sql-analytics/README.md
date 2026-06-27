# Web3 On-Chain SQL Analytics 🌐

This folder is dedicated to analyzing on-chain transaction data from blockchain networks (such as Ethereum, L2s, and Solana) using SQL.

## 🔬 Researched Topic: Ethereum Gas Fee Optimization

### 📈 Business & Protocol Case
An analysis of gas consumption and fee trends on the Ethereum network. The goal is to identify gas price volatility, detect peak congestion hours, and recommend optimal low-cost transaction windows for decentralized applications (dApps) and retail users.

### 📊 Rationale
Analyzing gas patterns is crucial **because** transaction costs are a major UX barrier in Web3. Helping projects optimize their transaction timings directly improves user retention and saves money.

### 💾 Data Sources
*   **Dune Analytics**: Using the `ethereum.transactions` or `gas_tracker` schemas.
*   **Flipside Crypto**: Using the `ethereum.core.fact_transactions` table.

### 🎯 Key Metrics to Analyze
*   Average and median gas prices (in Gwei) grouped by hour of the day and day of the week.
*   Correlation between high gas prices and market volatility (price movements of ETH).
*   Total gas spent by top DeFi smart contracts (Uniswap, OpenSea, etc.) over time.
