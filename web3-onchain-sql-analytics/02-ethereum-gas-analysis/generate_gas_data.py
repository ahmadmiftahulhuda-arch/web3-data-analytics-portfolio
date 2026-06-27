import os
import csv
import random
from datetime import datetime, timedelta

def generate_eth_gas_data():
    os.makedirs('data', exist_ok=True)
    filename = 'data/eth_gas_daily.csv'
    
    print(f"Generating realistic Ethereum gas data in {filename}...")
    random.seed(42)
    
    headers = ['block_timestamp', 'block_number', 'gas_price']
    
    # EIP-1559 activation date: August 5, 2021
    # We will generate:
    # 1. 2000 transactions in July/August 2021 (pre & post EIP-1559)
    # 2. 8000 transactions in the last 30 days (June 2026)
    
    transactions = []
    
    # Pre-EIP1559 Era: July 1, 2021 to Aug 4, 2021
    start_pre = datetime(2021, 7, 1)
    for i in range(1, 1001):
        # Random date in pre-EIP1559 era
        dt = start_pre + timedelta(days=random.randint(0, 33), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        # Block number < 12965000
        block_num = random.randint(12730000, 12964999)
        # Pre-EIP1559 gas prices were highly volatile, with frequent gas wars/MEV spikes
        # Base gas price is 30-100 Gwei, but spikes can go up to 500 Gwei
        if random.random() < 0.15:
            gas_gwei = random.randint(150, 450) # Gas spike
        else:
            gas_gwei = random.randint(30, 90)
        gas_price_wei = int(gas_gwei * 1e9)
        transactions.append((dt.strftime('%Y-%m-%d %H:%M:%S'), block_num, gas_price_wei))
        
    # Post-EIP1559 Early Era: Aug 5, 2021 to Aug 31, 2021
    start_post_early = datetime(2021, 8, 5)
    for i in range(1, 1001):
        dt = start_post_early + timedelta(days=random.randint(0, 26), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        block_num = random.randint(12965000, 13140000)
        # Post-EIP1559 gas prices became more stable due to base fee burns
        # Gas prices usually range between 20-70 Gwei, spikes are smaller (100-200 Gwei)
        if random.random() < 0.08:
            gas_gwei = random.randint(90, 180)
        else:
            gas_gwei = random.randint(20, 60)
        gas_price_wei = int(gas_gwei * 1e9)
        transactions.append((dt.strftime('%Y-%m-%d %H:%M:%S'), block_num, gas_price_wei))
        
    # Recent Era: Last 30 days (May 28, 2026 to June 27, 2026)
    # The current time is June 28, 2026
    start_recent = datetime(2026, 5, 28)
    for i in range(1, 8001):
        dt = start_recent + timedelta(days=random.randint(0, 29), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        block_num = random.randint(19800000, 20200000)
        
        # Gas fee hourly pattern:
        # UTC 13:00 - 18:00 (WIB 20:00 - 01:00) is usually busiest/most expensive
        # UTC 01:00 - 06:00 (WIB 08:00 - 13:00) is usually cheapest
        hour = dt.hour
        if 13 <= hour <= 18:
            # Expensive hours
            gas_gwei = random.randint(35, 75)
        elif 1 <= hour <= 6:
            # Cheap hours
            gas_gwei = random.randint(10, 25)
        else:
            # Regular hours
            gas_gwei = random.randint(20, 45)
            
        gas_price_wei = int(gas_gwei * 1e9)
        transactions.append((dt.strftime('%Y-%m-%d %H:%M:%S'), block_num, gas_price_wei))
        
    # Sort transactions by date
    transactions.sort(key=lambda x: x[0])
    
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(transactions)
        
    print(f"Generated {len(transactions)} transaction rows in {filename}.")

if __name__ == '__main__':
    generate_eth_gas_data()
