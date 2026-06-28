import os
import sys
import duckdb
import matplotlib.pyplot as plt

def generate_stablecoin_charts():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    metadata_file = 'output/stablecoins_metadata.parquet'
    history_file = 'output/stablecoin_supply_history.parquet'
    
    if not os.path.exists(metadata_file) or not os.path.exists(history_file):
        print("Error: Parquet data files not found. Please run fetch_defillama.py first.")
        return
        
    con = duckdb.connect()
    
    # -----------------------------------------------------------------
    # CHART 1: Stablecoin Market Share (Pie Chart)
    # -----------------------------------------------------------------
    print("Generating stablecoin market share pie chart...")
    query_share = """
    SELECT symbol, circulating / 1e9 AS supply_bn
    FROM 'output/stablecoins_metadata.parquet'
    WHERE symbol IN ('USDT', 'USDC', 'DAI', 'FRAX')
    ORDER BY supply_bn DESC;
    """
    
    results_share = con.execute(query_share).fetchall()
    symbols = [r[0] for r in results_share]
    supplies = [r[1] for r in results_share]
    
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Modern Web3-like pastel colors
    colors = ['#00b4d8', '#90e0ef', '#caf0f8', '#ffd166']
    
    # Draw Pie Chart
    wedges, texts, autotexts = ax.pie(
        supplies, 
        labels=symbols, 
        autopct='%1.1f%%',
        startangle=140, 
        colors=colors,
        textprops=dict(color='#2c2c2c', fontweight='bold', fontsize=11),
        wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2) # Donut chart style
    )
    
    # Style autopct text
    for autotext in autotexts:
        autotext.set_color('black')
        autotext.set_fontsize(10)
        
    ax.set_title('Stablecoin Supply Market Share (USDT/USDC/DAI/FRAX)', fontsize=14, fontweight='bold', pad=20)
    
    # Add a center text for total supply
    total_supply = sum(supplies)
    ax.text(0, 0, f'Total\n${total_supply:.1f}B', ha='center', va='center', fontsize=14, fontweight='bold', color='#4a4a4a')
    
    plt.tight_layout()
    plt.savefig('stablecoin_market_share.png', dpi=300)
    plt.close()
    print("Saved stablecoin_market_share.png.")
    
    # -----------------------------------------------------------------
    # CHART 2: 30-Day Stablecoin Supply Growth (Bar Chart)
    # -----------------------------------------------------------------
    print("Generating stablecoin 30-day supply growth bar chart...")
    query_growth = """
    WITH ordered_supply AS (
        SELECT symbol, date, SUM(supply_usd) / 1e9 AS total_supply_bn,
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) as rn_desc,
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date ASC) as rn_asc
        FROM 'output/stablecoin_supply_history.parquet'
        WHERE date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY symbol, date
    ),
    supply_ends AS (
        SELECT 
            symbol,
            MAX(CASE WHEN rn_desc = 1 THEN total_supply_bn END) AS current_supply_bn,
            MAX(CASE WHEN rn_asc = 1 THEN total_supply_bn END) AS start_supply_bn
        FROM ordered_supply
        GROUP BY symbol
    )
    SELECT symbol,
           (current_supply_bn - start_supply_bn) * 100.0 / start_supply_bn AS pct_change_30d
    FROM supply_ends
    WHERE symbol IN ('USDT', 'USDC', 'DAI', 'FRAX')
    ORDER BY pct_change_30d DESC;
    """
    
    results_growth = con.execute(query_growth).fetchall()
    growth_symbols = [r[0] for r in results_growth]
    growth_pcts = [r[1] for r in results_growth]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Bar colors depending on positive/negative growth
    bar_colors = ['#2ec4b6' if x >= 0 else '#e63946' for x in growth_pcts]
    
    bars = ax.bar(growth_symbols, growth_pcts, color=bar_colors, width=0.5)
    
    # Customize labels and borders
    ax.set_title('Stablecoin 30-Day Supply Growth (%)', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('Percentage Change (%)', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_xlabel('Stablecoin', fontsize=11, fontweight='bold', labelpad=10)
    
    # Add grid lines
    ax.yaxis.grid(True, linestyle='--', alpha=0.6, color='#cccccc')
    ax.xaxis.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add values on the bars
    for bar in bars:
        height = bar.get_height()
        sign = '+' if height >= 0 else ''
        ax.text(
            bar.get_x() + bar.get_width()/2, 
            height + (0.2 if height >= 0 else -0.5), 
            f"{sign}{height:.2f}%", 
            ha='center', va='bottom' if height >= 0 else 'top', 
            fontsize=10, fontweight='bold', color='#2c2c2c'
        )
        
    # Draw line at y=0
    ax.axhline(0, color='#666666', linewidth=1, linestyle='-')
    
    plt.tight_layout()
    plt.savefig('stablecoin_supply_growth.png', dpi=300)
    plt.close()
    print("Saved stablecoin_supply_growth.png.")
    
    con.close()
    print("All stablecoin charts generated successfully!")

if __name__ == '__main__':
    generate_stablecoin_charts()
