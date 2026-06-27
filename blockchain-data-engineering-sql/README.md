# Blockchain Data Engineering SQL

This folder focuses on relational database schema design, event indexing, and ETL/ELT transformations of raw blockchain logs into clean, queryable models.

## Researched Topic: Relational Database Schema for NFT ERC-721 Event Tracking

### Business & Protocol Case
Designing a normalized relational database schema to index and process raw smart contract logs of ERC-721 (NFT) transfers and mints. The goal is to design tables, index columns for fast querying, and write clean SQL queries to track current ownership and history of specific NFTs.

### Rationale
Raw blockchain logs are unorganized, flat, and difficult to query directly. We need a relational schema **because** it organizes flat transfer logs into structured tables (`nft_tokens`, `nft_transfers`, `nft_owners`), enabling instant lookups for NFT portfolios, floor prices, and history.

###  Sources
*   **Dune Analytics / Flipside**: Raw event log tables (`ethereum.core.fact_event_logs`).
*   **Dummy Schema Creation**: Designing local SQL tables to mock NFT mints and transfers.

### Key Metrics to Analyze
*   Current owner of any specific Token ID at any point in time.
*   Token transfer velocity (how often a token changes hands).
*   Historical price changes per token to map holding duration before selling.
