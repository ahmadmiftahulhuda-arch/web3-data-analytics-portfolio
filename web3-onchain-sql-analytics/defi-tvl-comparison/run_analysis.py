import os
import sys
import duckdb

def format_cell(val):
    if val is None:
        return 'NULL'
    # Format large TVL figures nicely
    if isinstance(val, (int, float)):
        if val > 1_000_000_000:
            return f"${val/1_000_000_000:,.2f}B"
        elif val > 1_000_000:
            return f"${val/1_000_000:,.2f}M"
        elif val > 1_000:
            return f"${val/1_000:,.2f}K"
        return f"{val:,.2f}"
    return str(val)

def print_table(headers, rows):
    if not rows:
        print("Empty set (0 rows)")
        return
        
    # Convert all cells to strings
    str_rows = [[format_cell(cell) for cell in row] for row in rows]
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
            
    # Print header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    separator_line = "-+-".join("-" * widths[i] for i in range(len(headers)))
    
    print(header_line)
    print(separator_line)
    
    # Print rows
    for row in str_rows:
        print(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    
    print(f"\n({len(rows)} row(s) returned)")

def main():
    sql_file = 'query.sql'
    csv_file = 'defillama_protocols.csv'
    
    if not os.path.exists(csv_file):
        print(f"Data file '{csv_file}' not found. Please run fetch_defillama.py first.")
        sys.exit(1)
        
    if not os.path.exists(sql_file):
        # Create a default query
        default_query = """-- DefiLlama TVL Analysis
-- You can query the CSV file directly as if it were a table!
SELECT name, symbol, category, tvl, change_7d
FROM 'defillama_protocols.csv'
ORDER BY tvl DESC
LIMIT 10;
"""
        with open(sql_file, 'w') as f:
            f.write(default_query)
        print(f"Created default '{sql_file}'.")
        
    with open(sql_file, 'r', encoding='utf-8') as f:
        query = f.read().strip()
        
    if not query:
        print("Query file is empty.")
        sys.exit(0)
        
    print(f"Executing query from {sql_file} against {csv_file}...\n")
    
    try:
        # DuckDB lets us query the CSV file directly!
        con = duckdb.connect()
        res = con.execute(query)
        headers = [desc[0] for desc in res.description] if res.description else []
        rows = res.fetchall()
        print_table(headers, rows)
        con.close()
    except Exception as e:
        print(f"Error executing query with DuckDB:\n{e}", file=sys.stderr)

if __name__ == '__main__':
    main()
