#!/usr/bin/env python3
"""
Automated script to generate data.json and upload to InfinityFree hosting
"""

import sqlite3
import json
import os
import time
from datetime import datetime

def generate_data_json():
    """Generate data.json from rates.db"""
    try:
        # Connect to SQLite database
        conn = sqlite3.connect("rates.db")
        cursor = conn.cursor()
        
        # Query data (must be in insertion order)
        cursor.execute("SELECT date, rate FROM rates ORDER BY rowid;")
        rows = cursor.fetchall()
        
        # Python deduplication: keep only the last entry for each day
        daily = {}
        for date, rate in rows:
            daily[date] = rate  # Later entries overwrite earlier ones
        
        # Sort by date
        data = [
            {"date": date, "rate": rate}
            for date, rate in sorted(daily.items())
        ]
        
        # Write to data.json (UTF-8, no BOM)
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        conn.close()
        
        print(f"Success: Exported data.json with {len(data)} records (deduplicated by date)")
        return True
        
    except Exception as e:
        print(f"Error generating data.json: {e}")
        return False

def main():
    """Main execution function"""
    print(f"Starting automated data export at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to project directory
    os.chdir(r"C:\Users\Administrator\Documents\Github\Daily-USD-CNY-Dashboard")
    
    # Generate data.json
    if generate_data_json():
        print("✅ Data export completed successfully")
        print("Next step: Upload data.json to InfinityFree via browser automation")
        # Note: Browser automation will be handled by OpenClaw's browser control
    else:
        print("❌ Data export failed")

if __name__ == "__main__":
    main()