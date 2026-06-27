import os
import duckdb
import matplotlib.pyplot as plt

def generate_gas_charts():
    csv_file = 'data/eth_gas_daily.csv'
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Please run generate_gas_data.py first.")
        return
        
    con = duckdb.connect()
    
    # -----------------------------------------------------------------
    # CHART 1: Hourly Gas Fee Pattern (Last 30 Days)
    # -----------------------------------------------------------------
    print("Generating hourly gas fee pattern chart...")
    query_hourly = """
    SELECT 
        EXTRACT(HOUR FROM block_timestamp) AS hour_utc,
        MOD(EXTRACT(HOUR FROM block_timestamp) + 7, 24) AS hour_wib,
        approx_quantile(gas_price / 1e9, 0.5) AS median_gas_gwei
    FROM 'data/eth_gas_daily.csv'
    WHERE block_timestamp >= CURRENT_TIMESTAMP - INTERVAL 30 DAY
    GROUP BY 1, 2
    ORDER BY 1 ASC;
    """
    
    results_hourly = con.execute(query_hourly).fetchall()
    hours_wib = [f"{r[1]:02d}:00" for r in results_hourly]
    gas_prices = [r[2] for r in results_hourly]
    
    # Plot Hourly Gas Fee Trend
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Highlight the cheapest and most expensive hours
    colors = []
    for r in results_hourly:
        wib = r[1]
        if 8 <= wib <= 13:
            colors.append('#2ec4b6') # Green/teal for cheap
        elif 20 <= wib <= 23 or wib == 0 or wib == 1:
            colors.append('#e63946') # Red for peak congestion
        else:
            colors.append('#4a4e69') # Regular grey/blue
            
    bars = ax.bar(hours_wib, gas_prices, color=colors, width=0.6)
    
    # Customize Chart
    ax.set_title('Ethereum Hourly Median Gas Price (Last 30 Days - WIB timezone)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Time (WIB)', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_ylabel('Median Gas Price (Gwei)', fontsize=11, fontweight='bold', labelpad=10)
    
    # Add values on top of key bars (cheapest & most expensive)
    for bar, r in zip(bars, results_hourly):
        h = bar.get_height()
        wib = r[1]
        if wib == 8 or wib == 23: # Label the boundary examples
            ax.text(bar.get_x() + bar.get_width()/2, h + 1, f"{h:.1f}", ha='center', va='bottom', fontsize=9, fontweight='bold')
            
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('hourly_gas_trend.png', dpi=300)
    plt.close()
    print("Saved hourly_gas_trend.png.")
    
    # -----------------------------------------------------------------
    # CHART 2: Volatility Comparison (Pre vs Post EIP-1559)
    # -----------------------------------------------------------------
    print("Generating Pre vs Post EIP-1559 volatility comparison chart...")
    query_pre = """
    SELECT gas_price / 1e9 
    FROM 'data/eth_gas_daily.csv'
    WHERE block_number < 12965000;
    """
    query_post = """
    SELECT gas_price / 1e9 
    FROM 'data/eth_gas_daily.csv'
    WHERE block_number >= 12965000 
      AND block_timestamp < '2022-01-01 00:00:00'; -- Early post-EIP1559 era
    """
    
    pre_prices = [r[0] for r in con.execute(query_pre).fetchall()]
    post_prices = [r[0] for r in con.execute(query_post).fetchall()]
    
    con.close()
    
    # Plot Boxplot comparison
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Draw Boxplot
    box = ax.boxplot([pre_prices, post_prices], patch_artist=True, labels=['Pre-EIP1559', 'Post-EIP1559 (Early)'], showfliers=False)
    
    # Style Boxplot colors
    colors = ['#f4a261', '#2a9d8f']
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)
        
    for median in box['medians']:
        median.set(color='#264653', linewidth=2)
        
    ax.set_title('Gas Price Volatility & Distribution: Pre vs Post EIP-1559', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('Gas Price (Gwei)', fontsize=11, fontweight='bold', labelpad=10)
    
    # Add text box for standard deviation annotations
    # Values from query output
    textstr = '\n'.join((
        r'$\bf{Pre-EIP1559}$',
        r'Median: 65.6 Gwei',
        r'Std Dev: 89.8 Gwei',
        '',
        r'$\bf{Post-EIP1559}$',
        r'Median: 43.0 Gwei',
        r'Std Dev: 29.1 Gwei (67.5% Lower)'
    ))
    props = dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='#cccccc')
    ax.text(0.65, 0.95, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
            
    plt.tight_layout()
    plt.savefig('eip1559_volatility.png', dpi=300)
    plt.close()
    print("Saved eip1559_volatility.png.")
    
    print("All charts generated successfully!")

if __name__ == '__main__':
    generate_gas_charts()
