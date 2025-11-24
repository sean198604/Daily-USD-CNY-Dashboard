import requests
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup


def fetch_usd_rate():
    url = 'https://www.boc.cn/sourcedb/whpj/'
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f'[错误] 无法访问汇率页面: {e}')
        return None

    # 提取汇率表格
    tables = soup.find_all('table')
    table = next((t for t in tables if len(t.find_all('tr')) > 10), None)
    if not table:
        print('[错误] 未找到合适的汇率表格')
        return None

    # 查找美元现汇买入价和发布时间
    for tr in table.find_all('tr'):
        cols = [td.get_text(strip=True) for td in tr.find_all('td')]
        if cols and '美元' in cols[0] and len(cols) >= 7:
            try:
                rate = float(cols[1])
                raw_pub_time = cols[6]  # 可能是 '2025.07.16 15:17:34' 或 '2025/11/24 09:18:14'

                # 支持多种时间格式
                dt = None
                for fmt in ('%Y.%m.%d %H:%M:%S', '%Y/%m/%d %H:%M:%S'):
                    try:
                        dt = datetime.strptime(raw_pub_time, fmt)
                        break
                    except ValueError:
                        pass

                if dt is None:
                    print(f'[错误] 无法解析日期格式: {raw_pub_time}')
                    return None

                return {
                    'date': dt.strftime('%Y-%m-%d'),
                    'pub_time': dt.strftime('%H:%M:%S'),
                    'rate': rate
                }

            except Exception as e:
                print(f'[错误] 解析美元汇率失败: {e}')
                return None

    print('[错误] 未找到美元汇率数据')
    return None


def store_rate_to_db(rate_data, db_path='rates.db'):
    if not rate_data:
        print('[警告] 无可保存的汇率数据')
        return False

    date = rate_data['date']
    pub_time = rate_data['pub_time']
    rate = rate_data['rate']

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # 创建表（如不存在）
        c.execute('''
            CREATE TABLE IF NOT EXISTS rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                pub_time TEXT,
                rate REAL,
                manual_flag INTEGER DEFAULT 0
            )
        ''')

        # 检查是否已存在
        c.execute('''
            SELECT 1 FROM rates
            WHERE date = ? AND pub_time = ? AND rate = ? AND manual_flag = 0
        ''', (date, pub_time, rate))
        exists = c.fetchone()

        if not exists:
            c.execute('''
                INSERT INTO rates(date, pub_time, rate, manual_flag)
                VALUES (?, ?, ?, 0)
            ''', (date, pub_time, rate))
            conn.commit()
            print(f'[成功] 新增汇率记录: {date} {pub_time} - {rate}')
            return True
        else:
            print(f'[跳过] 汇率记录已存在: {date} {pub_time} - {rate}')
            return False

    except Exception as e:
        print(f'[错误] 数据库操作失败: {e}')
        return False

    finally:
        conn.close()


def fetch_and_store(db_path='rates.db'):
    rate_data = fetch_usd_rate()
    return store_rate_to_db(rate_data, db_path=db_path)


if __name__ == '__main__':
    fetch_and_store()
