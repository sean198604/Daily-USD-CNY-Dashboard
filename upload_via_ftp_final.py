#!/usr/bin/env python3
"""
Upload USD/CNY data.json to infinityfree via FTP
"""

import sqlite3
import json
import ftplib
import os
from pathlib import Path

def export_data_json():
    """Export data from SQLite to JSON"""
    # Connect to SQLite database
    conn = sqlite3.connect("rates.db")
    cursor = conn.cursor()
    
    # Query data
    cursor.execute("SELECT date, rate FROM rates ORDER BY rowid;")
    rows = cursor.fetchall()
    
    # Deduplicate by date (keep last entry for each date)
    daily = {}
    for date, rate in rows:
        daily[date] = rate
    
    # Sort by date and create data structure
    data = [
        {"date": date, "rate": rate}
        for date, rate in sorted(daily.items())
    ]
    
    # Write to data.json
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    conn.close()
    print(f"Success: Exported data.json with {len(data)} records (deduplicated by date)")
    return len(data)

def upload_to_infinityfree():
    """Upload data.json to infinityfree via FTP"""
    # FTP 凭据从环境变量读取，避免明文写入代码仓库
    # 本地部署：export FTP_HOST / FTP_USER / FTP_PASS
    FTP_HOST = os.getenv("FTP_HOST", "ftpupload.net")
    FTP_USER = os.getenv("FTP_USER", "")
    FTP_PASS = os.getenv("FTP_PASS", "")
    REMOTE_PATH = "/trustlayer.free.nf/htdocs"
    
    try:
        # Connect to FTP server
        print("Connecting to FTP server...")
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        print("FTP login successful!")
        
        # Change to target directory
        ftp.cwd(REMOTE_PATH)
        
        # Upload file
        print("Uploading data.json...")
        with open("data.json", "rb") as file:
            ftp.storbinary("STOR data.json", file)
        print("File uploaded successfully!")
        
        # Close connection
        ftp.quit()
        print("FTP connection closed.")
        
        return True
        
    except Exception as e:
        print(f"Error uploading to FTP: {e}")
        return False

def main():
    """Main execution function"""
    print("Starting automatic USD/CNY data upload to infinityfree...")
    
    # Export data to JSON
    record_count = export_data_json()
    
    # Upload to infinityfree
    success = upload_to_infinityfree()
    
    if success:
        print("SUCCESS: Automatic upload completed successfully!")
        print(f"Uploaded {record_count} records to infinityfree.")
    else:
        print("ERROR: Upload failed. Check FTP credentials and network connection.")
    
    return success

if __name__ == "__main__":
    main()