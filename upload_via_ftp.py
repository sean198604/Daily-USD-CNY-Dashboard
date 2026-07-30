import ftplib
import json
import sqlite3
import os
from datetime import datetime

def generate_data_json():
    """Generate data.json from SQLite database"""
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

def upload_to_infinityfree():
    """Upload data.json to infinityfree via FTP"""
    try:
        # FTP 凭据从环境变量读取，避免明文写入代码仓库
        # 本地部署：export FTP_HOST / FTP_USER / FTP_PASS
        ftp_host = os.getenv("FTP_HOST", "ftp.infinityfree.com")
        ftp_user = os.getenv("FTP_USER", "")
        ftp_pass = os.getenv("FTP_PASS", "")
        remote_path = "/htdocs/data.json"
        
        # Connect to FTP server
        print("Connecting to FTP server...")
        ftp = ftplib.FTP(ftp_host)
        ftp.login(ftp_user, ftp_pass)
        print("FTP login successful!")
        
        # Upload file
        print("Uploading data.json...")
        with open("data.json", "rb") as file:
            ftp.storbinary(f"STOR {remote_path}", file)
        print("File uploaded successfully!")
        
        # Close connection
        ftp.quit()
        print("FTP connection closed.")
        return True
        
    except Exception as e:
        print(f"FTP upload failed: {e}")
        return False

def main():
    """Main execution function"""
    print("Starting automatic USD/CNY data upload to infinityfree...")
    
    # Step 1: Generate data.json
    if not generate_data_json():
        print("Failed to generate data.json. Aborting upload.")
        return False
    
    # Step 2: Upload via FTP
    if not upload_to_infinityfree():
        print("Failed to upload data.json. Check FTP credentials and connection.")
        return False
    
    print("✅ Automatic upload completed successfully!")
    print(f"Data uploaded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return True

if __name__ == "__main__":
    main()