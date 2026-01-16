import requests
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
import re

def fetch_usd_rate():
    url = 'https://www.boc.cn/sourcedb/whpj/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f'[错误] 无法访问汇率页面: {e}')
        return None

    all_trs = soup.find_all('tr')
    for tr in all_trs:
        tds = tr.find_all('td')
        if len(tds) < 8: continue
        
        cols = [td.get_text(strip=True) for td in tds]
        
        if cols[0] == '美元':
            try:
                # 1. 提取汇率
                rate_val = cols[1] if cols[1] else cols[5]
                rate = float(rate_val)
                
                # 2. 格式化处理
                # 合并所有可能的时间单元格，防止偏移
                raw_full = f"{cols[6]} {cols[7]}".strip()
                
                # 使用正则精确查找
                # 匹配日期：找到 2026.01.16 或 2026-01-16
                d_match = re.search(r'(\d{4}[\./-]\d{2}[\./-]\d{2})', raw_full)
                # 匹配时间：找到 15:59:28
                t_match = re.search(r'(\d{2}:\d{2}:\d{2})', raw_full)
                
                if d_match and t_match:
                    # 统一将日期转化为 YYYY-MM-DD 格式
                    clean_date = d_match.group(1).replace('.', '-').replace('/', '-')
                    clean_time = t_match.group(1)
                else:
                    # 备选方案：如果正则失败，尝试强行截取
                    # 日期通常是前 10 位
                    clean_date = cols[6][:10].replace('.', '-').replace('/', '-')
                    # 时间通常在 cols[7] 或者 cols[6] 的末尾
                    clean_time = cols[7] if len(cols[7]) == 8 else cols[6][-8:]
                
                # 最后的保险：确保日期字段里不含冒号（时间特征）
                if ":" in clean_date:
                    clean_date = clean_date.split()[0].split('T')[0]

                return {
                    'date': clean_date,
                    'pub_time': clean_time,
                    'rate': rate
                }
            except Exception as e:
                print(f'[错误] 数据行解析异常: {e}')
                continue

    print('[错误] 页面中未找到美元数据')
    return None

def store_rate_to_db(rate_data, db_path='rates.db'):
    if not rate_data:
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            # 确保表结构存在
            c.execute('''
                CREATE TABLE IF NOT EXISTS rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    pub_time TEXT,
                    rate REAL,
                    manual_flag INTEGER DEFAULT 0
                )
            ''')

            # 严格去重检查
            c.execute('''
                SELECT 1 FROM rates 
                WHERE date = ? AND pub_time = ? AND rate = ? AND manual_flag = 0
            ''', (rate_data['date'], rate_data['pub_time'], rate_data['rate']))
            
            if not c.fetchone():
                c.execute('''
                    INSERT INTO rates(date, pub_time, rate, manual_flag)
                    VALUES (?, ?, ?, 0)
                ''', (rate_data['date'], rate_data['pub_time'], rate_data['rate']))
                conn.commit()
                print(f"[成功入库] {rate_data['date']} | {rate_data['pub_time']} | {rate_data['rate']}")
                return True
            else:
                print(f"[跳过重复] {rate_data['date']} {rate_data['pub_time']}")
                return False
    except Exception as e:
        print(f'[错误] 数据库操作失败: {e}')
        return False

def fetch_and_store(db_path='rates.db'):
    data = fetch_usd_rate()
    return store_rate_to_db(data, db_path)

if __name__ == '__main__':
    fetch_and_store()