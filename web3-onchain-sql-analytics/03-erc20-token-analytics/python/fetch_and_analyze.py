"""
ERC-20 Token Analytics — BigQuery Fetcher & Local Analyzer
==========================================================
Jalankan semua SQL queries ke BigQuery, simpan sebagai CSV,
lalu analisis lokal menggunakan DuckDB.

Usage:
    python fetch_and_analyze.py --token USDC --days 30
    python fetch_and_analyze.py --token USDT --days 7  --dry-run

Author: Ahmad Miftahul Huda
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import duckdb
from google.cloud import bigquery

# ── Token registry (tambah token lain di sini) ────────────────────────────
TOKEN_REGISTRY = {
    "USDC": {"address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "decimals": 6},
    "USDT": {"address": "0xdac17f958d2ee523a2206206994597c13d831ec7", "decimals": 6},
    "DAI":  {"address": "0x6b175474e89094c44da98b954eedeac495271d0f", "decimals": 18},
    "WETH": {"address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "decimals": 18},
    "LINK": {"address": "0x514910771af9ca656af840dff83e8264ecf986ca", "decimals": 18},
}

OUTPUT_DIR = Path(__file__).parent.parent / "output"
SQL_DIR    = Path(__file__).parent.parent / "sql"


def load_sql(filename: str, token_address: str, lookback_days: int) -> str:
    """Load SQL file dan inject parameter."""
    sql_path = SQL_DIR / filename
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    sql = sql_path.read_text(encoding='utf-8')
    # Replace DECLARE statements dengan nilai aktual
    sql = sql.replace(
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        token_address.lower()
    )
    return sql


def run_query(client: bigquery.Client, sql: str, query_name: str) -> pd.DataFrame:
    """Jalankan query BigQuery dan return sebagai DataFrame."""
    print(f"  ⏳ Running {query_name}...")
    try:
        job = client.query(sql)
        df = job.to_dataframe()
        print(f"  ✅ {query_name}: {len(df):,} rows returned")
        return df
    except Exception as e:
        print(f"  ❌ {query_name} failed: {e}")
        return pd.DataFrame()


def analyze_locally(dfs: dict, token_symbol: str) -> None:
    """Analisis tambahan menggunakan DuckDB (tanpa BigQuery cost)."""
    print("\n📊 Running local analysis with DuckDB...")
    con = duckdb.connect()

    # Register DataFrames ke DuckDB
    for name, df in dfs.items():
        if not df.empty:
            con.register(name, df)

    # Summary statistics
    if "velocity" in dfs and not dfs["velocity"].empty:
        summary = con.execute("""
            SELECT
                MIN(transfer_date)                  AS period_start,
                MAX(transfer_date)                  AS period_end,
                SUM(transfer_count)                 AS total_transfers,
                ROUND(SUM(daily_volume_usd), 2)     AS total_volume,
                ROUND(AVG(daily_volume_usd), 2)     AS avg_daily_volume,
                ROUND(MAX(daily_volume_usd), 2)     AS peak_daily_volume,
                SUM(unique_senders)                 AS total_unique_senders
            FROM velocity
        """).fetchdf()

        print(f"\n  📈 {token_symbol} Transfer Summary:")
        for col in summary.columns:
            print(f"     {col}: {summary[col].values[0]}")

    if "whale" in dfs and not dfs["whale"].empty:
        whale_summary = con.execute("""
            SELECT
                transfer_type,
                SUM(tx_count)        AS total_txs,
                ROUND(SUM(total_volume), 2) AS total_volume
            FROM whale
            GROUP BY transfer_type
            ORDER BY total_volume DESC
        """).fetchdf()

        print(f"\n  🐋 Whale Activity Breakdown:")
        print(whale_summary.to_string(index=False))

    con.close()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    parser = argparse.ArgumentParser(description="ERC-20 Token Analytics")
    parser.add_argument("--token",   default="USDC",  help="Token symbol (USDC/USDT/DAI/WETH/LINK)")
    parser.add_argument("--days",    default=30, type=int, help="Lookback days")
    parser.add_argument("--dry-run", action="store_true",  help="Print queries only, don't run")
    parser.add_argument("--project", default=None,         help="GCP project ID")
    args = parser.parse_args()

    # Validasi token
    token_symbol = args.token.upper()
    if token_symbol not in TOKEN_REGISTRY:
        print(f"❌ Token '{token_symbol}' tidak dikenal. Pilih dari: {list(TOKEN_REGISTRY.keys())}")
        sys.exit(1)

    token_info    = TOKEN_REGISTRY[token_symbol]
    token_address = token_info["address"]

    print(f"\n🔗 Web3 On-Chain Analytics — ERC-20 Token Analysis")
    print(f"   Token   : {token_symbol} ({token_address})")
    print(f"   Period  : Last {args.days} days")
    print(f"   Output  : {OUTPUT_DIR}/\n")

    if args.dry_run:
        print("🔍 DRY RUN — queries akan di-print saja, tidak dieksekusi ke BigQuery.\n")

    # Setup output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # Inisialisasi BigQuery client
    if not args.dry_run:
        client = bigquery.Client(project=args.project)
        print("✅ BigQuery client connected\n")

    # Definisi queries yang akan dijalankan
    queries = [
        ("01_top_holders.sql",        "top_holders",  "Top 20 Holders"),
        ("02_transfer_velocity.sql",  "velocity",     "Transfer Velocity (30D)"),
        ("03_whale_movement.sql",     "whale",        "Whale Movement"),
        ("04_wash_trade_detection.sql","wash_trades", "Wash Trade Detection"),
        ("05_holder_distribution.sql","distribution", "Holder Distribution"),
    ]

    dfs = {}
    print("🚀 Running queries...\n")

    for sql_file, df_key, label in queries:
        sql = load_sql(sql_file, token_address, args.days)

        if args.dry_run:
            print(f"  📋 [{label}] SQL loaded from {sql_file}")
            print(f"     First 200 chars: {sql[:200].strip()}...\n")
            continue

        df = run_query(client, sql, label)
        dfs[df_key] = df

        # Simpan ke CSV
        if not df.empty:
            output_path = OUTPUT_DIR / f"{timestamp}_{token_symbol}_{df_key}.csv"
            df.to_csv(output_path, index=False)
            print(f"     💾 Saved to {output_path.name}")

    # Analisis lokal dengan DuckDB
    if not args.dry_run and dfs:
        analyze_locally(dfs, token_symbol)

    print(f"\n✅ Done! Output files saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
