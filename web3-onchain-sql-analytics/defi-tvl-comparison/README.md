# DeFi Protocol TVL Comparison
 
A pipeline that pulls live protocol data from [DefiLlama](https://defillama.com/), cleans it with SQL via DuckDB, and surfaces key metrics around DeFi market share, protocol dominance, and growth momentum.
 
---
 
## Data Source
 
**DefiLlama API** — `https://api.llama.fi/protocols`
 
Free, no auth required. DefiLlama is the de facto standard for on-chain TVL tracking; its adapters are open-source and auditable on GitHub, which makes it a reliable foundation for any DeFi analytics work.
 
---
 
## Project Layout
 
```
.
├── fetch_defillama.py        # Hits the API and writes raw output to CSV
├── run_analysis.py           # Loads query.sql and runs it against the CSV via DuckDB
├── query.sql                 # Core data cleaning + analytics query
└── defillama_protocols.csv   # Raw dataset (auto-generated, not committed)
```
 
---
 
## Data Cleaning
 
Raw API responses need work before they're usable. `query.sql` handles this inside a CTE before any analysis runs:
 
| Issue | Fix |
|---|---|
| Extra whitespace in string fields | `TRIM()` on `name`, `symbol`, `category` |
| Inconsistent symbol casing | `UPPER(TRIM(symbol))` |
| Missing/empty symbols (`''`, `'-'`, `NULL`) | Replaced with `'N/A'` via `CASE WHEN` |
| Missing category | Defaulted to `'Other'` via `COALESCE()` |
| NULL percentage change fields | Defaulted to `0.0` via `COALESCE()` |
| CEX entries (exchange reserves) | Excluded — `WHERE category != 'CEX'` |
| Inactive or invalid protocols | Excluded — `WHERE tvl > 0` |
 
CEX reserves are excluded by design: exchange-held assets aren't deployed in DeFi and would distort TVL rankings.
 
---
 
## Findings
 
Results below are from a recent snapshot against the live dataset.
 
### Top 5 Protocols by TVL
 
| # | Protocol | Category | Symbol | TVL |
|---|---|---|---|---|
| 1 | Lido | Liquid Staking | LDO | $14.37B |
| 2 | Aave V3 | Lending | AAVE | $11.89B |
| 3 | SSV Network | Staking Pool | SSV | $7.82B |
| 4 | LayerZero V2 | Bridge | ZRO | $7.36B |
| 5 | WBTC | Bridge | N/A | $6.86B |
 
### Category Market Share (Top 5)
 
| Category | Total TVL | Notes |
|---|---|---|
| Bridge | $44.19B | Cross-chain liquidity infrastructure |
| Lending | $36.02B | Decentralized credit markets |
| Liquid Staking | $30.41B | ETH staking + yield derivatives |
| RWA | $25.48B | Tokenized treasuries and real-world credit |
| DEX | $11.29B | On-chain exchange liquidity pools |
 
### Fastest Growing (TVL > $100M, 7-day window)
 
| Protocol | Category | 7d Change | TVL |
|---|---|---|---|
| Mellow Core | Onchain Capital Allocator | +32.08% | $177.86M |
| Dolomite | Lending | +23.88% | $192.23M |
| Polygon Bridge | Chain Bridge | +22.18% | $2.74B |
 
---
 
## Key Takeaways
 
**Bridges and Liquid Staking are the backbone of multi-chain DeFi.** Bridges lead at $44.19B, followed by Liquid Staking at $30.41B. Lido's position ($14.37B) reflects how dominant ETH staking yield has become as a baseline rate across the ecosystem.
 
**RWA is no longer a niche.** At $25.48B, tokenized real-world assets have moved into fourth place by category. Demand for stable, off-chain yield (primarily US T-bills) is clearly finding its way on-chain at scale.
 
**Capital allocators are gaining traction.** Mellow Core's +32% weekly growth suggests that depositors are moving toward automated, restaking-layer yield optimization rather than managing positions manually.
 
---
 
## Getting Started
 
```bash
# Install dependencies
pip install requests duckdb
 
# Pull the latest data
python fetch_defillama.py
 
# Run the SQL analysis
python run_analysis.py
```
 
The CSV is regenerated fresh on each run, so results will reflect current on-chain state.