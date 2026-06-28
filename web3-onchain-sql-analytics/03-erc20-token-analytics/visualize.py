import os
import sys
import glob
import pandas as pd
import matplotlib.pyplot as plt

def generate_erc20_charts():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    output_dir = 'output'
    
    # Cari file keluaran terbaru untuk velocity dan distribution
    velocity_files = glob.glob(f"{output_dir}/*_USDC_velocity.csv")
    dist_files = glob.glob(f"{output_dir}/*_USDC_distribution.csv")
    
    if not velocity_files or not dist_files:
        print("Error: Mock CSV files not found. Please run generate_mock_data.py first.")
        return
        
    # Ambil file terbaru
    velocity_file = sorted(velocity_files)[-1]
    dist_file = sorted(dist_files)[-1]
    
    print(f"Reading velocity from {velocity_file}...")
    df_velocity = pd.read_csv(velocity_file)
    
    print(f"Reading distribution from {dist_file}...")
    df_dist = pd.read_csv(dist_file)
    
    plt.style.use('ggplot')
    
    # -----------------------------------------------------------------
    # CHART 1: Holder Distribution (Donut + Bar Chart)
    # -----------------------------------------------------------------
    print("Generating holder distribution chart...")
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Sort by supply share descending
    df_dist_sorted = df_dist.sort_values(by='pct_of_supply', ascending=False)
    
    colors = ['#1d3557', '#457b9d', '#a8dadc', '#f1faee', '#e63946', '#f4a261']
    
    # Plot bar chart for supply share
    bars = ax1.bar(df_dist_sorted['holder_tier'], df_dist_sorted['pct_of_supply'], color=colors[:len(df_dist_sorted)], width=0.5, label='Supply Share (%)')
    
    ax1.set_ylabel('Percentage of Supply (%)', fontsize=11, fontweight='bold', color='#1d3557')
    ax1.set_xlabel('Holder Tier', fontsize=11, fontweight='bold', labelpad=15)
    ax1.set_title('USDC Holder Distribution & Supply Concentration', fontsize=14, fontweight='bold', pad=15)
    plt.xticks(rotation=30, ha='right')
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, height + 1, f"{height:.1f}%", ha='center', va='bottom', fontsize=9, fontweight='bold')
        
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Gini Coefficient Annotation
    gini_coeff = df_dist['gini_coefficient'].iloc[0]
    concentration = df_dist['concentration_label'].iloc[0]
    
    textstr = '\n'.join((
        r'$\bf{Concentration\ Metrics}$',
        f'Gini Coefficient: {gini_coeff:.4f}',
        f'Classification: {concentration}',
        '',
        'Mega Whales (45 wallets)',
        'control 57.8% of supply!'
    ))
    props = dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='#cccccc')
    ax1.text(0.62, 0.85, textstr, transform=ax1.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
            
    plt.tight_layout()
    plt.savefig('holder_distribution.png', dpi=300)
    plt.close()
    print("Saved holder_distribution.png.")
    
    # -----------------------------------------------------------------
    # CHART 2: Daily Volume and Tx Count Trend
    # -----------------------------------------------------------------
    print("Generating transfer velocity trend chart...")
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Convert dates for plotting
    dates = pd.to_datetime(df_velocity['transfer_date']).dt.strftime('%b %d')
    volumes_billion = df_velocity['daily_volume_usd'] / 1e9
    
    # Plot Volume as Line Chart
    color_vol = '#457b9d'
    line1 = ax1.plot(dates, volumes_billion, color=color_vol, linewidth=2.5, marker='o', label='Daily Volume (Billion USD)')
    ax1.set_ylabel('Daily Volume (Billion USD)', fontsize=11, fontweight='bold', color=color_vol)
    ax1.set_xlabel('Date (2026)', fontsize=11, fontweight='bold', labelpad=10)
    ax1.tick_params(axis='y', labelcolor=color_vol)
    
    # Secondary axis for transaction count
    ax2 = ax1.twinx()
    color_tx = '#e63946'
    line2 = ax2.plot(dates, df_velocity['transfer_count'] / 1000, color=color_tx, linewidth=1.5, linestyle='--', marker='s', label='Tx Count (Thousands)')
    ax2.set_ylabel('Transaction Count (Thousands)', fontsize=11, fontweight='bold', color=color_tx)
    ax2.tick_params(axis='y', labelcolor=color_tx)
    
    # Customize layout
    ax1.set_title('USDC Daily Transfer Volume & Transaction Count Trends (30D)', fontsize=14, fontweight='bold', pad=15)
    ax1.xaxis.set_major_locator(plt.MaxNLocator(10)) # limit x labels
    
    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    
    plt.tight_layout()
    plt.savefig('transfer_velocity_trend.png', dpi=300)
    plt.close()
    print("Saved transfer_velocity_trend.png.")
    
    print("All ERC-20 charts generated successfully!")

if __name__ == '__main__':
    generate_erc20_charts()
