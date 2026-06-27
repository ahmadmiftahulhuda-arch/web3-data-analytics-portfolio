import os
import sys
import duckdb

def format_cell(val):
    if val is None:
        return 'NULL'
    if isinstance(val, float):
        return f"{val:,.2f}"
    if isinstance(val, int):
        return f"{val:,}"
    return str(val)

def print_table(headers, rows):
    if not rows:
        print("Empty set (0 rows)")
        return
        
    str_rows = [[format_cell(cell) for cell in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
            
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    separator_line = "-+-".join("-" * widths[i] for i in range(len(headers)))
    
    print(header_line)
    print(separator_line)
    
    for row in str_rows:
        print(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    
    print(f"\n({len(rows)} row(s) returned)")

def translate_bq_to_duckdb(query):
    # Replace BigQuery table with local CSV
    query = query.replace("`bigquery-public-data.crypto_ethereum.transactions`", "'data/eth_gas_daily.csv'")
    
    # Replace BigQuery DATE_TRUNC with DuckDB DATE_TRUNC
    # BigQuery uses DATE_TRUNC(block_timestamp, DAY)
    # DuckDB uses DATE_TRUNC('day', block_timestamp)
    query = query.replace("DATE_TRUNC(block_timestamp, DAY)", "DATE_TRUNC('day', block_timestamp)")
    
    # Replace BigQuery TIMESTAMP_SUB with DuckDB date subtraction
    query = query.replace("TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)", "CURRENT_TIMESTAMP - INTERVAL 30 DAY")
    
    # Replace BigQuery APPROX_QUANTILES median array with DuckDB approx_quantile
    query = query.replace("APPROX_QUANTILES(gas_price / 1e9, 100)[OFFSET(50)]", "approx_quantile(gas_price / 1e9, 0.5)")
    query = query.replace("APPROX_QUANTILES(gas_price / 1e9, 100)[OFFSET(50)]", "approx_quantile(gas_price / 1e9, 0.5)")
    
    # Replace STDDEV with stddev
    query = query.replace("STDDEV(gas_price / 1e9)", "stddev_samp(gas_price / 1e9)")
    
    return query

def main():
    print("=====================================================================")
    print("Ethereum Gas Fee Analysis - Local Runner (BigQuery SQL -> DuckDB)")
    print("=====================================================================")
    print("Available queries to run:")
    print("1. Daily Median Gas Price Trend (01_daily_gas_trend.sql)")
    print("2. Hourly Gas Fee Pattern / Cheapest Hours (02_hourly_peak.sql)")
    print("3. Volatility Comparison Pre vs Post EIP-1559 (03_pre_post_eip1559.sql)")
    print("=====================================================================")
    
    choice = input("Enter the number of the query to run (1-3): ").strip()
    
    query_files = {
        '1': 'queries/01_daily_gas_trend.sql',
        '2': 'queries/02_hourly_peak.sql',
        '3': 'queries/03_pre_post_eip1559.sql'
    }
    
    if choice not in query_files:
        print("Invalid choice. Exiting.")
        sys.exit(1)
        
    query_file = query_files[choice]
    csv_file = 'data/eth_gas_daily.csv'
    
    if not os.path.exists(csv_file):
        print(f"Dataset '{csv_file}' not found. Please run generate_gas_data.py first.")
        sys.exit(1)
        
    if not os.path.exists(query_file):
        print(f"Query file '{query_file}' not found.")
        sys.exit(1)
        
    with open(query_file, 'r', encoding='utf-8') as f:
        bq_query = f.read().strip()
        
    print(f"\nExecuting {query_file}...")
    
    # Translate BQ SQL to DuckDB SQL
    duck_query = translate_bq_to_duckdb(bq_query)
    
    try:
        con = duckdb.connect()
        res = con.execute(duck_query)
        headers = [desc[0] for desc in res.description] if res.description else []
        rows = res.fetchall()
        print_table(headers, rows)
        con.close()
    except Exception as e:
        print(f"Error running analysis:\n{e}", file=sys.stderr)

if __name__ == '__main__':
    main()
