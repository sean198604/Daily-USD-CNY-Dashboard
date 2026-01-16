import sqlite3
import webbrowser
import threading
from datetime import datetime, time
from flask import Flask, render_template, request, redirect, url_for, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from waitress import serve

# 假设你的抓取脚本名为 fetch_usd_rate.py
import fetch_usd_rate

app = Flask(__name__)
app.config['DB_PATH'] = 'rates.db'

# ========== 数据库工具函数 ==========
def get_db_connection():
    """使用 row_factory 让结果可以像字典一样访问"""
    conn = sqlite3.connect(app.config['DB_PATH'])
    conn.row_factory = sqlite3.Row
    return conn

# ========== 核心逻辑：数据筛选 ==========
def get_best_rate_for_day(records, target_time):
    """
    根据优先级筛选一天的最佳汇率：
    1. 手动录入 (manual_flag = 1)
    2. 无发布时间记录 (可能是早期手动同步的数据)
    3. 发布时间最接近 09:31:00 的记录
    """
    # 1. 查找手动记录
    manual_records = [rec for rec in records if rec['manual_flag'] == 1]
    if manual_records:
        return manual_records[0]

    # 2. 查找没有发布时间的记录
    no_pub_time = [rec for rec in records if not rec['pub_time'] or str(rec['pub_time']).strip() == '']
    if no_pub_time:
        return no_pub_time[0]

    # 3. 计算时间差，找最接近 target_time 的
    def time_diff(rec):
        try:
            t = datetime.strptime(rec['pub_time'], '%H:%M:%S').time()
            return abs(
                datetime.combine(datetime.min, t) - datetime.combine(datetime.min, target_time)
            ).total_seconds()
        except (ValueError, TypeError):
            return float('inf')

    return min(records, key=time_diff)

# ========== 路由接口 ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/rates')
def api_rates():
    days = request.args.get('days', default=60, type=int)
    target_time = time(9, 31)
    
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT id, date, pub_time, rate, manual_flag 
        FROM rates 
        ORDER BY date DESC, pub_time DESC
    ''').fetchall()
    conn.close()

    # 按日期分组
    grouped = {}
    for row in rows:
        d = row['date']
        if d not in grouped:
            grouped[d] = []
        grouped[d].append(row)

    result = []
    for d in sorted(grouped.keys(), reverse=True):
        chosen = get_best_rate_for_day(grouped[d], target_time)
        result.append({
            'date': chosen['date'],
            'pub_time': chosen['pub_time'] if chosen['pub_time'] else '',
            'rate': chosen['rate']
        })

    # 截取天数并重新按日期正序排列（方便图表展示）
    result = result[:days]
    result.reverse()
    return jsonify(result)

@app.route('/admin')
def admin():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM rates ORDER BY date DESC, pub_time DESC LIMIT 200').fetchall()
    conn.close()
    return render_template('admin.html', rows=rows)

@app.route('/admin/add', methods=['POST'])
def admin_add():
    date = request.form.get('date')
    rate = request.form.get('rate')
    if date and rate:
        with get_db_connection() as conn:
            # 保证每个日期只能有一条手动记录
            conn.execute('DELETE FROM rates WHERE date = ? AND manual_flag = 1', (date,))
            conn.execute('INSERT INTO rates(date, rate, manual_flag) VALUES (?, ?, 1)', (date, rate))
            conn.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:rate_id>', methods=['POST'])
def admin_delete(rate_id):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM rates WHERE id = ?', (rate_id,))
        conn.commit()
    return redirect(url_for('admin'))

@app.route('/api/fetch', methods=['POST'])
def api_fetch():
    try:
        fetch_usd_rate.fetch_and_store()
        conn = get_db_connection()
        row = conn.execute('SELECT date, pub_time, rate FROM rates ORDER BY id DESC LIMIT 1').fetchone()
        conn.close()
        
        if row:
            return jsonify({
                'date': row['date'],
                'pub_time': row['pub_time'],
                'rate': row['rate'],
                'time': row['pub_time']
            })
        return jsonify({'error': '未找到记录'})
    except Exception as e:
        return jsonify({'error': str(e)})

# ========== 定时任务 ==========
def job_fetch_daily():
    print(f"[{datetime.now()}] 定时抓取任务启动...")
    try:
        fetch_usd_rate.fetch_and_store()
        print("抓取成功")
    except Exception as e:
        print(f"抓取失败: {e}")

scheduler = BackgroundScheduler()
# 建议：由于汇率发布时间不固定，可以考虑每隔15分钟抓取一次，或者在9:30-10:00之间增加频率
scheduler.add_job(job_fetch_daily, 'cron', hour=9, minute=31, misfire_grace_time=60)
scheduler.start()

# ========== 启动逻辑 ==========
def open_browser():
    webbrowser.open("http://127.0.0.1:5050")

if __name__ == '__main__':
    print("🚀 服务已启动：http://127.0.0.1:5050")
    
    # 1.5秒后自动打开浏览器
    threading.Timer(1.5, open_browser).start()
    
    # 使用 Waitress 运行生产环境（单线程模式，避免 APScheduler 重复启动）
    serve(app, host='0.0.0.0', port=5050, threads=4)