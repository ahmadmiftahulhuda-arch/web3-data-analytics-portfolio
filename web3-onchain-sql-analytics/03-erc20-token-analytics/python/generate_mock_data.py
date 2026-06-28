import os
import csv
from datetime import datetime, timedelta

def generate_erc20_mock_data():
    output_dir = '../output'
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = "20260628_0100"
    token = "USDC"
    
    print(f"Generating mock data for {token} in {output_dir}...")
    
    # 1. Top Holders
    # columns: rank, wallet_address, total_received, total_sent, net_balance, pct_of_total_supply
    top_holders_file = f"{output_dir}/{timestamp}_{token}_top_holders.csv"
    top_holders_data = [
        [1, "0x47ac0fb4f2d84898e4d9e7b4dab3c14503a415f6", 15200000000.0, 10200000000.0, 5000000000.0, 15.625],
        [2, "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", 12400000000.0, 8400000000.0, 4000000000.0, 12.5],
        [3, "0xf977814e90da44bfa03b6295a0616a897441acec", 8200000000.0, 5200000000.0, 3000000000.0, 9.375],
        [4, "0xe78388b4f2d73f32e92c2a07cb2b5cf2b291d9cc", 5500000000.0, 3500000000.0, 2000000000.0, 6.25],
        [5, "0x55fe5afc5f3d4a2ee523a22e623a223a223a223a", 4800000000.0, 3300000000.0, 1500000000.0, 4.6875],
        [6, "0x0d0707963952c2f1b55a8ebabbea3420f0d1e13b", 3200000000.0, 2000000000.0, 1200000000.0, 3.75],
        [7, "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8", 2900000000.0, 1900000000.0, 1000000000.0, 3.125],
        [8, "0xdad169a4f5c59acf79d0fd5d91d1201ef1bce9f1", 2500000000.0, 1600000000.0, 900000000.0, 2.8125],
        [9, "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b", 2100000000.0, 1300000000.0, 800000000.0, 2.5],
        [10, "0x28c6c06298d514db089934071355e5743bf21d60", 1900000000.0, 1200000000.0, 700000000.0, 2.1875]
    ]
    with open(top_holders_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "wallet_address", "total_received", "total_sent", "net_balance", "pct_of_total_supply"])
        writer.writerows(top_holders_data)
        
    # 2. Transfer Velocity (30D)
    # columns: transfer_date, transfer_count, daily_volume_usd, unique_senders
    velocity_file = f"{output_dir}/{timestamp}_{token}_velocity.csv"
    velocity_data = []
    start_date = datetime(2026, 5, 29)
    for i in range(30):
        dt = start_date + timedelta(days=i)
        tx_count = 150000 + i * 2000 + (10000 if i%7 in (5,6) else -5000)
        vol_usd = 2200000000.0 + i * 15000000.0 + (300000000.0 if i%7 in (2,3) else -100000000.0)
        unique_senders = 45000 + i * 500
        velocity_data.append([dt.strftime('%Y-%m-%d'), tx_count, vol_usd, unique_senders])
        
    with open(velocity_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["transfer_date", "transfer_count", "daily_volume_usd", "unique_senders"])
        writer.writerows(velocity_data)
        
    # 3. Whale Movement
    # columns: transfer_date, transfer_type, tx_count, total_volume, avg_amount, largest_transfer, unique_senders, unique_receivers
    whale_file = f"{output_dir}/{timestamp}_{token}_whale.csv"
    whale_data = []
    types = ['wallet_to_wallet', 'exchange_outflow', 'exchange_inflow', 'exchange_to_exchange']
    for i in range(30):
        dt = start_date + timedelta(days=i)
        for t in types:
            if t == 'wallet_to_wallet':
                tx = 85
                vol = 145000000.0
            elif t == 'exchange_outflow':
                tx = 54
                vol = 95000000.0
            elif t == 'exchange_inflow':
                tx = 48
                vol = 82000000.0
            else:
                tx = 12
                vol = 24000000.0
            whale_data.append([dt.strftime('%Y-%m-%d'), t, tx, vol, vol/tx, vol*0.4, tx-2, tx-3])
            
    with open(whale_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["transfer_date", "transfer_type", "tx_count", "total_volume", "avg_amount", "largest_transfer", "unique_senders", "unique_receivers"])
        writer.writerows(whale_data)
        
    # 4. Wash Trades
    # columns: wallet_a, wallet_b, circular_tx_count, total_volume_circulated, avg_minutes_between, fastest_return_minutes, avg_amount_difference, suspicion_score, risk_level, first_seen, last_seen
    wash_file = f"{output_dir}/{timestamp}_{token}_wash_trades.csv"
    wash_data = [
        ["0x3a4f2b5cf2b5cf2b5cf2b5cf2b5cf2b5cf2b5cf2", "0x5e5afc5f3d4a2ee523a22e623a22e623a223a223a", 45, 12500000.0, 3.4, 1.2, 0.05, 94.0, "🔴 High Risk", "2026-06-01 12:00:00", "2026-06-25 18:30:00"],
        ["0xfe9e8709d3215310075d67e3ed32a380ccf451c8", "0x2910543af39aba0cd09dbb2d50200b3e800a63d2", 22, 6400000.0, 5.8, 2.1, 0.12, 88.0, "🔴 High Risk", "2026-06-03 08:15:00", "2026-06-24 14:22:00"],
        ["0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13", "0xe853c56864a2ebe4576a807d26fdc4a0ada51919", 15, 3200000.0, 12.4, 4.5, 0.45, 72.0, "🟡 Medium Risk", "2026-06-05 09:30:00", "2026-06-22 17:15:00"],
        ["0x1fd169a4f5c59acf79d0fd5d91d1201ef1bce9f1", "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be", 8, 1200000.0, 18.2, 8.4, 0.85, 54.0, "🟡 Medium Risk", "2026-06-10 14:00:00", "2026-06-20 11:45:00"]
    ]
    with open(wash_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["wallet_a", "wallet_b", "circular_tx_count", "total_volume_circulated", "avg_minutes_between", "fastest_return_minutes", "avg_amount_difference", "suspicion_score", "risk_level", "first_seen", "last_seen"])
        writer.writerows(wash_data)
        
    # 5. Distribution
    # columns: holder_tier, wallet_count, pct_of_holders, tier_total_balance, pct_of_supply, avg_balance, min_balance, max_balance, total_holders, total_supply, gini_coefficient, concentration_label
    dist_file = f"{output_dir}/{timestamp}_{token}_distribution.csv"
    dist_data = [
        ["🐳 Mega Whale (>$10M)", 45, 0.05, 18500000000.0, 57.8125, 411111111.11, 10200000.0, 5000000000.0, 90000, 32000000000.0, 0.8423, "Terkonsentrasi"],
        ["🦈 Whale ($1M–$10M)", 245, 0.27, 7200000000.0, 22.5, 29387755.10, 1100000.0, 9800000.0, 90000, 32000000000.0, 0.8423, "Terkonsentrasi"],
        ["🐬 Large ($100K–$1M)", 1250, 1.39, 3800000000.0, 11.875, 3040000.0, 105000.0, 950000.0, 90000, 32000000000.0, 0.8423, "Terkonsentrasi"],
        ["🐟 Medium ($10K–$100K)", 8460, 9.40, 1800000000.0, 5.625, 212765.96, 10200.0, 98000.0, 90000, 32000000000.0, 0.8423, "Terkonsentrasi"],
        ["🦐 Small ($1K–$10K)", 25000, 27.78, 600000000.0, 1.875, 24000.0, 1050.0, 9800.0, 90000, 32000000000.0, 0.8423, "Terkonsentrasi"],
        ["🌱 Micro (<$1K)", 55000, 61.11, 100000000.0, 0.3125, 1818.18, 0.05, 990.0, 90000, 32000000000.0, 0.8423, "Terkonsentrasi"]
    ]
    with open(dist_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["holder_tier", "wallet_count", "pct_of_holders", "tier_total_balance", "pct_of_supply", "avg_balance", "min_balance", "max_balance", "total_holders", "total_supply", "gini_coefficient", "concentration_label"])
        writer.writerows(dist_data)
        
    print("Mock data generation completed successfully!")

if __name__ == '__main__':
    generate_erc20_mock_data()
