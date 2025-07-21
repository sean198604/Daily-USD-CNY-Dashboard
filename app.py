from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime, timedelta, time
from apscheduler.schedulers.background import BackgroundScheduler
import fetch_usd_rate

app = Flask(__name__)
app.config['DB_PATH'] = 'rates.db'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/rates')
def api_rates():
    days = int(request.args.get('days', 60))
    conn = sqlite3.connect(app.config['DB_PATH'])
    c = conn.cursor()

    c.execute('''
        SELECT id, date, pub_time, rate, manual_flag
        FROM rates
        ORDER BY date DESC, pub_time DESC
    ''')
    rows = c.fetchall()
    conn.close()

    target_time = time(9, 30)
    grouped = {}

    for _id, d, pt, r, m in rows:
        if d not in grouped:
            grouped[d] = []
        grouped[d].append((_id, d, pt, r, m))

    result = []

    for d, records in grouped.items():
        manual_records = [rec for rec in records if rec[4] == 1]
        if manual_records:
            chosen = manual_records[0]
        else:
            no_pub_time_records = [rec for rec in records if not rec[2] or rec[2].strip() == '']
            if no_pub_time_records:
                chosen = no_pub_time_records[0]
            else:
                def time_diff(rec):
                    try:
                        t = datetime.strptime(rec[2], '%H:%M:%S').time()
                        return abs(
                            datetime.combine(datetime.min, t) - datetime.combine(datetime.min, target_time)
                        ).total_seconds()
                    except Exception:
                        return float('inf')

                chosen = min(records, key=time_diff)

        result.append({
            'date': chosen[1],
            'pub_time': chosen[2] if chosen[2] else '',
            'rate': chosen[3]
        })

    result.sort(key=lambda x: x['date'], reverse=True)
    result = result[:days]
    result.sort(key=lambda x: x['date'])

    return jsonify(result)


@app.route('/admin', methods=['GET'])
def admin():
    conn = sqlite3.connect(app.config['DB_PATH'])
    c = conn.cursor()
    c.execute('SELECT id, date, pub_time, rate, manual_flag FROM rates ORDER BY date DESC, pub_time DESC')
    rows = c.fetchall()
    conn.close()
    return render_template('admin.html', rows=rows)


@app.route('/admin/add', methods=['POST'])
def admin_add():
    date = request.form['date']
    rate = request.form['rate']

    conn = sqlite3.connect(app.config['DB_PATH'])
    c = conn.cursor()

    # 保证每个日期只能有一条手动记录
    c.execute('''
        DELETE FROM rates
        WHERE date = ? AND manual_flag = 1
    ''', (date,))

    c.execute('''
        INSERT INTO rates(date, rate, manual_flag)
        VALUES (?, ?, 1)
    ''', (date, rate))

    conn.commit()
    conn.close()
    return redirect(url_for('admin'))


@app.route('/api/fetch', methods=['POST'])
def api_fetch():
    try:
        fetch_usd_rate.fetch_and_store()

        conn = sqlite3.connect(app.config['DB_PATH'])
        c = conn.cursor()
        c.execute('''
            SELECT date, pub_time, rate FROM rates
            ORDER BY date DESC, pub_time DESC
            LIMIT 1
        ''')
        row = c.fetchone()
        conn.close()

        if row:
            return jsonify({
                'date': row[0],
                'pub_time': row[1],
                'rate': row[2]
            })
        else:
            return jsonify({'error': '无记录'})
    except Exception as e:
        return jsonify({'error': str(e)})


# ========== 定时任务配置 ==========
def job_fetch_daily():
    try:
        print(f"[定时任务] 抓取开始 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        fetch_usd_rate.fetch_and_store()
        print(f"[定时任务] 抓取成功")
    except Exception as e:
        print(f"[定时任务错误] {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(
    job_fetch_daily,
    'cron',
    hour=9,
    minute=30,
    misfire_grace_time=60  # 防止错过任务
)
scheduler.start()


# ========== 启动方式（适配 Windows 用 waitress）==========
if __name__ == '__main__':
    from waitress import serve
    print("🚀 启动服务：http://0.0.0.0:5050")
    serve(app, host='0.0.0.0', port=5050)
import webbrowser
import threading

def open_browser():
    webbrowser.open("http://127.0.0.1:5050")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    app.run()
