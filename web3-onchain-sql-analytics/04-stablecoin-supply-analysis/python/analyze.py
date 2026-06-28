"""
Stablecoin Analysis — DuckDB Query Runner
==========================================
Jalankan semua SQL queries menggunakan DuckDB terhadap data
yang sudah di-fetch dari DefiLlama (Parquet files).

Usage:
    python analyze.py                          # Jalankan semua queries
    python analyze.py --query supply_overview  # Jalankan 1 query spesifik
    python analyze.py --print-findings         # Print summary ke terminal

Author: Ahmad Miftahul Huda
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

import duckdb
import pandas as pd

SQL_DIR    = Path(__file__).parent.parent / "sql"
OUTPUT_DIR = Path(__file__).parent.parent / "output"

QUERIES = {
    "supply_overview":      "01_supply_overview.sql",
    "chain_distribution":   "02_chain_distribution.sql",
    "supply_change":        "03_supply_change_analysis.sql",
    "depeg_detection":      "04_depeg_detection.sql",
    "mint_burn":            "05_mint_burn_analysis.sql",
}


def check_data_exists() -> bool:
    """Pastikan file Parquet tersedia sebelum query."""
    required_files = [
        "stablecoin_supply_history.parquet",
        "stablecoins_metadata.parquet",
        "chain_stablecoin_totals.parquet",
    ]
    missing = [f for f in required_files if not (OUTPUT_DIR / f).exists()]
    if missing:
        print("❌ Data files tidak ditemukan:")
        for f in missing:
            print(f"   - {OUTPUT_DIR / f}")
        print("\n💡 Jalankan dulu: python fetch_defillama.py")
        return False
    return True


def run_query(con: duckdb.DuckDBPyConnection, query_name: str, sql_file: str) -> pd.DataFrame:
    """Load dan jalankan satu SQL file, return sebagai DataFrame."""
    sql_path = SQL_DIR / sql_file
    if not sql_path.exists():
        print(f"  ⚠️  SQL file tidak ditemukan: {sql_path}")
        return pd.DataFrame()

    sql = sql_path.read_text(encoding='utf-8')

    try:
        df = con.execute(sql).fetchdf()
        print(f"  ✅ {query_name}: {len(df):,} rows")
        return df
    except Exception as e:
        print(f"  ❌ {query_name} failed: {e}")
        return pd.DataFrame()


def print_key_findings(results: dict[str, pd.DataFrame]) -> None:
    """Print ringkasan temuan ke terminal."""
    print("\n" + "="*60)
    print("📊 KEY FINDINGS — STABLECOIN SUPPLY ANALYSIS")
    print("="*60)

    # Supply overview
    if "supply_overview" in results and not results["supply_overview"].empty:
        df = results["supply_overview"]
        print("\n🏦 Current Supply Overview:")
        for _, row in df.iterrows():
            trend = row.get("supply_trend", "")
            print(
                f"   {row['symbol']:<8} "
                f"${row['current_supply_bn']:>8.2f}B  "
                f"30D: {row.get('pct_change_30d', 0):>+6.2f}%  "
                f"Share: {row.get('market_share_pct', 0):>5.1f}%  "
                f"{trend}"
            )

    # Depeg alerts
    if "depeg_detection" in results and not results["depeg_detection"].empty:
        df = results["depeg_detection"]
        price_status = df[df["report_type"] == "PRICE_STATUS"]
        alerts = price_status[price_status["peg_status"] != "✅ On Peg"]

        if len(alerts) > 0:
            print(f"\n⚠️  DEPEG ALERTS ({len(alerts)} stablecoins off peg):")
            for _, row in alerts.iterrows():
                print(
                    f"   🔔 {row['symbol']}: "
                    f"${row['current_price']:.5f} "
                    f"({row['pct_from_peg']:+.3f}%) — {row['peg_status']}"
                )
        else:
            print("\n✅ All stablecoins currently on peg")

        # Stress events
        stress = df[df["report_type"] == "STRESS_EVENT"]
        if len(stress) > 0:
            print(f"\n🚨 Supply Stress Events (30D): {len(stress)} detected")
            for _, row in stress.head(5).iterrows():
                print(
                    f"   {row['event_date']} | {row['symbol']}: "
                    f"{row['daily_change_pct']:+.2f}% — {row['stress_flag']}"
                )

    print("\n" + "="*60)


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Stablecoin Supply Analyzer — DuckDB")
    parser.add_argument(
        "--query", choices=list(QUERIES.keys()),
        default=None, help="Jalankan query spesifik (default: semua)"
    )
    parser.add_argument(
        "--print-findings", action="store_true",
        help="Print key findings summary ke terminal"
    )
    args = parser.parse_args()

    # Cek data tersedia
    if not check_data_exists():
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    print(f"\n🔗 Stablecoin Supply Analyzer — DuckDB")
    print(f"   SQL dir    : {SQL_DIR}/")
    print(f"   Output dir : {OUTPUT_DIR}/\n")

    # Buka koneksi DuckDB
    con = duckdb.connect()

    # Tentukan queries yang akan dijalankan
    to_run = {args.query: QUERIES[args.query]} if args.query else QUERIES

    results = {}
    print("🚀 Running queries...\n")

    for query_name, sql_file in to_run.items():
        df = run_query(con, query_name, sql_file)
        results[query_name] = df

        if not df.empty:
            # Simpan ke CSV
            out_path = OUTPUT_DIR / f"{timestamp}_{query_name}.csv"
            df.to_csv(out_path, index=False)
            print(f"     💾 {out_path.name}")

    con.close()

    # Print findings
    if args.print_findings or not args.query:
        print_key_findings(results)

    print(f"\n✅ Analysis complete! Results in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
