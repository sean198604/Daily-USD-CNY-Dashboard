import sqlite3
import json

# 1. 连接 SQLite 数据库
conn = sqlite3.connect("rates.db")
cursor = conn.cursor()

# 2. 查询数据（必须按插入顺序）
cursor.execute("SELECT date, rate FROM rates ORDER BY rowid;")
rows = cursor.fetchall()

# 3. Python 去重：同一天只保留最后一条
daily = {}
for date, rate in rows:
    daily[date] = rate   # 后面的会覆盖前面的

# 4. 按日期排序
data = [
    {"date": date, "rate": rate}
    for date, rate in sorted(daily.items())
]

# 5. 写入 data.json（UTF-8，无 BOM）
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

conn.close()

print(f"✅ 已导出 data.json，共 {len(data)} 条记录（按日期去重）")
