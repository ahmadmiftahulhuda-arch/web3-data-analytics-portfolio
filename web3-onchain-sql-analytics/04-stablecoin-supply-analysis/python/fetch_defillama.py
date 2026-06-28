"""
Stablecoin Supply Fetcher — DefiLlama API
==========================================
Fetch data supply, harga, dan distribusi chain dari DefiLlama
Stablecoins API. Output disimpan sebagai Parquet untuk query DuckDB.

Usage:
    python fetch_defillama.py
    python fetch_defillama.py --stablecoins USDC USDT DAI --days 90

Author: Ahmad Miftahul Huda
"""

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

OUTPUT_DIR = Path(__file__).parent.parent / "output"
BASE_URL   = "https://stablecoins.llama.fi"

# Stablecoin IDs di DefiLlama (cek di /stablecoins untuk ID lainnya)
STABLECOIN_IDS = {
    "USDT":  "1",
    "USDC":  "2",
    "BUSD":  "3",
    "DAI":   "5",
    "FRAX":  "6",
    "TUSD":  "9",
    "USDP":  "25",
    "USDD":  "29",
    "GUSD":  "34",
    "LUSD":  "113",
    "CRVUSD":"63",
    "PYUSD": "109",
}

CHAINS_TO_TRACK = [
    "ethereum", "arbitrum", "polygon", "optimism",
    "base", "avalanche", "bsc", "solana"
]


def fetch_json(url: str, label: str = "") -> dict | list | None:
    """Fetch JSON dari URL dengan retry sederhana."""
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"  ⚠️  Attempt {attempt+1}/3 failed for {label}: {e}")
            time.sleep(2 ** attempt)
    print(f"  ❌ Failed to fetch: {label}")
    return None


def fetch_all_stablecoins() -> pd.DataFrame:
    """Fetch metadata semua stablecoin dari /stablecoins endpoint."""
    print("📥 Fetching stablecoin metadata...")
    data = fetch_json(f"{BASE_URL}/stablecoins?includePrices=true", "stablecoins list")
    if not data:
        return pd.DataFrame()

    rows = []
    for coin in data.get("peggedAssets", []):
        rows.append({
            "id":             coin.get("id"),
            "name":           coin.get("name"),
            "symbol":         coin.get("symbol"),
            "peg_type":       coin.get("pegType"),
            "peg_mechanism":  coin.get("pegMechanism"),
            "circulating":    coin.get("circulating", {}).get("peggedUSD", 0),
            "price":          coin.get("price"),
            "chains":         ", ".join(coin.get("chains", [])),
            "chain_count":    len(coin.get("chains", [])),
        })

    df = pd.DataFrame(rows)
    df["fetched_at"] = datetime.now(timezone.utc).isoformat()
    print(f"  ✅ {len(df)} stablecoins fetched")
    return df


def fetch_historical_supply(stablecoin_id: str, symbol: str) -> pd.DataFrame:
    """Fetch historical supply breakdown per chain untuk 1 stablecoin."""
    print(f"  📥 Fetching {symbol} historical supply...")
    data = fetch_json(
        f"{BASE_URL}/stablecoin/{stablecoin_id}",
        f"{symbol} history"
    )
    if not data:
        return pd.DataFrame()

    rows = []
    for chain_name, chain_data in data.get("chainBalances", {}).items():
        for entry in chain_data.get("tokens", []):
            date_ts = entry.get("date")
            if not date_ts:
                continue
            date = datetime.fromtimestamp(date_ts, tz=timezone.utc).date()
            
            circulating = entry.get("circulating", {})
            supply_usd = circulating.get("peggedUSD", 0)
            
            rows.append({
                "date":       date,
                "symbol":     symbol,
                "chain":      chain_name.lower(),
                "supply_usd": supply_usd,
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        print(f"     ✅ {symbol}: {len(df):,} rows ({df['date'].min()} → {df['date'].max()})")
    return df


def fetch_chain_totals() -> pd.DataFrame:
    """Fetch total stablecoin supply per chain."""
    print("\n📥 Fetching chain-level stablecoin totals...")
    all_rows = []

    for chain in CHAINS_TO_TRACK:
        data = fetch_json(
            f"{BASE_URL}/stablecoincharts/{chain}",
            f"{chain} totals"
        )
        if not data:
            continue

        for entry in data:
            date_ts = entry.get("date")
            if not date_ts:
                continue
            date = datetime.fromtimestamp(int(date_ts), tz=timezone.utc).date()
            all_rows.append({
                "date":            date,
                "chain":           chain,
                "total_stables_usd": entry.get("totalCirculatingUSD", {}).get("peggedUSD", 0),
            })
        time.sleep(0.3)  # rate limit courtesy

    df = pd.DataFrame(all_rows)
    print(f"  ✅ {len(df):,} chain-date rows fetched")
    return df


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    parser = argparse.ArgumentParser(description="Fetch stablecoin data from DefiLlama")
    parser.add_argument(
        "--stablecoins", nargs="+",
        default=["USDC", "USDT", "DAI", "FRAX"],
        help="Stablecoin symbols to fetch"
    )
    parser.add_argument("--days", type=int, default=90, help="Days of history to keep")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n🔗 Stablecoin Supply Fetcher — DefiLlama API")
    print(f"   Stablecoins : {', '.join(args.stablecoins)}")
    print(f"   Output dir  : {OUTPUT_DIR}/\n")

    # 1. Metadata semua stablecoin
    meta_df = fetch_all_stablecoins()
    if not meta_df.empty:
        meta_df.to_parquet(OUTPUT_DIR / "stablecoins_metadata.parquet", index=False)
        meta_df.to_csv(OUTPUT_DIR / "stablecoins_metadata.csv", index=False)
        print(f"  💾 Saved metadata ({len(meta_df)} rows)")

    # 2. Historical supply per stablecoin
    all_supply = []
    for symbol in args.stablecoins:
        coin_id = STABLECOIN_IDS.get(symbol.upper())
        if not coin_id:
            print(f"  ⚠️  ID tidak ditemukan untuk {symbol}, skip.")
            continue
        df = fetch_historical_supply(coin_id, symbol.upper())
        if not df.empty:
            all_supply.append(df)
        time.sleep(0.5)

    if all_supply:
        supply_df = pd.concat(all_supply, ignore_index=True)
        # Filter ke N hari terakhir
        cutoff = pd.Timestamp.now(tz="UTC").normalize() - pd.Timedelta(days=args.days)
        supply_df = supply_df[supply_df["date"] >= cutoff.date()]
        supply_df.to_parquet(OUTPUT_DIR / "stablecoin_supply_history.parquet", index=False)
        supply_df.to_csv(OUTPUT_DIR / "stablecoin_supply_history.csv", index=False)
        print(f"\n  💾 Saved supply history ({len(supply_df):,} rows)")

    # 3. Chain totals
    chain_df = fetch_chain_totals()
    if not chain_df.empty:
        cutoff = pd.Timestamp.now(tz="UTC").normalize() - pd.Timedelta(days=args.days)
        chain_df = chain_df[chain_df["date"] >= cutoff.date()]
        chain_df.to_parquet(OUTPUT_DIR / "chain_stablecoin_totals.parquet", index=False)
        chain_df.to_csv(OUTPUT_DIR / "chain_stablecoin_totals.csv", index=False)
        print(f"  💾 Saved chain totals ({len(chain_df):,} rows)")

    print(f"\n✅ Fetch complete! Files saved to {OUTPUT_DIR}/")
    print("   Next step: run `python analyze.py` untuk query SQL via DuckDB")


if __name__ == "__main__":
    main()
