import os
import duckdb
import matplotlib.pyplot as plt

def generate_chart():
    csv_file = 'defillama_protocols.csv'
    image_file = 'category_tvl.png'
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Please run fetch_defillama.py first.")
        return
        
    print("Querying database to generate chart data...")
    
    # 1. Connect to DuckDB and query top 5 categories
    query = """
    WITH cleaned_protocols AS (
        SELECT 
            COALESCE(TRIM(category), 'Other') AS category, 
            tvl
        FROM 'defillama_protocols.csv'
        WHERE category != 'CEX' AND tvl > 0
    )
    SELECT category, SUM(tvl) AS total_tvl
    FROM cleaned_protocols
    GROUP BY category
    ORDER BY total_tvl DESC
    LIMIT 5;
    """
    
    try:
        con = duckdb.connect()
        results = con.execute(query).fetchall()
        con.close()
    except Exception as e:
        print(f"Database error: {e}")
        return
        
    if not results:
        print("No data returned from database.")
        return
        
    # Extract data for plotting
    categories = [r[0] for r in results]
    tvls = [r[1] for r in results]
    
    # Convert TVL to Billions for readability
    tvls_billions = [val / 1_000_000_000 for val in tvls]
    
    print(f"Retrieved top categories: {dict(zip(categories, tvls_billions))}")
    
    # 2. Plotting (Horizontal Bar Chart)
    # Set style for modern aesthetics
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Choose a nice Web3-like color palette (purple-ish gradient)
    colors = ['#5e548e', '#9f86c0', '#be95c4', '#e0b1cb', '#f2d5e3']
    
    # Draw bars (reverse order so largest is at the top)
    bars = ax.barh(categories[::-1], tvls_billions[::-1], color=colors[::-1], height=0.6)
    
    # Customize labels and titles
    ax.set_title('Top 5 DeFi Categories by Total Value Locked (TVL)', fontsize=16, fontweight='bold', pad=20, color='#2c2c2c')
    ax.set_xlabel('Total Value Locked (Billions USD)', fontsize=12, labelpad=15, fontweight='bold')
    ax.set_ylabel('DeFi Category', fontsize=12, labelpad=15, fontweight='bold')
    
    # Add values on the bars
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 1.0, bar.get_y() + bar.get_height()/2, 
                f"${width:.2f}B", 
                va='center', ha='left', fontsize=10, fontweight='bold', color='#4f4f4f')
                
    # Customize grid and borders
    ax.xaxis.grid(True, linestyle='--', alpha=0.6, color='#cccccc')
    ax.yaxis.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    
    plt.tight_layout()
    
    # 3. Save plot
    plt.savefig(image_file, dpi=300)
    plt.close()
    
    print(f"Successfully generated and saved chart to {image_file}!")

if __name__ == '__main__':
    generate_chart()
