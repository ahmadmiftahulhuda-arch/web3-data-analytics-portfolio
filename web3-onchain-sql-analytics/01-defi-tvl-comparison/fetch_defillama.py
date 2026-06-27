import csv
import json
import os
import requests

def fetch_tvl_data():
    url = "https://api.llama.fi/protocols"
    print(f"Fetching data from {url}...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        protocols = response.json()
        print(f"Successfully fetched {len(protocols)} DeFi protocols.")
        return protocols
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def save_to_csv(protocols, filename="defillama_protocols.csv"):
    if not protocols:
        return
        
    print(f"Saving data to {filename}...")
    
    # Define columns to extract
    headers = ['name', 'symbol', 'category', 'chains', 'tvl', 'change_1d', 'change_7d', 'change_30d']
    
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for p in protocols:
            # Extract fields with safe defaults
            name = p.get('name', 'Unknown')
            symbol = p.get('symbol', '')
            category = p.get('category', 'Other')
            
            # Chains is a list, join them as a comma-separated string
            chains_list = p.get('chains', [])
            chains = ", ".join(chains_list) if isinstance(chains_list, list) else str(chains_list)
            
            tvl = p.get('tvl', 0.0)
            change_1d = p.get('change_1d', 0.0)
            change_7d = p.get('change_7d', 0.0)
            change_30d = p.get('change_30d', 0.0)
            
            writer.writerow([name, symbol, category, chains, tvl, change_1d, change_7d, change_30d])
            
    print(f"Saved successfully! File size: {os.path.getsize(filename)} bytes.")

if __name__ == '__main__':
    data = fetch_tvl_data()
    if data:
        save_to_csv(data)
