# USD 买入价汇率看板项目 (Flask + ECharts)

一个轻量级的网页看板，实时从人行官网爬取美元（USD）对人民币（CNY）的现汇买入价数据，并支持手动刷新和定时抓取。

## ✨ 项目亮点

- 使用 Flask 构建后端 API 和管理面板
- 使用 APScheduler 每天定时自动抓取汇率
- 前端基于 ECharts 绘制交互式图表
- 支持管理员手动添加或修正汇率数据
- 可通过鼠标滚轮缩放查看历史数据范围
```
┌────────────┐        定时/手动触发        ┌──────────────┐
│ APScheduler│──────────────────────────▶│ fetch_usd... │
└────────────┘                           └──────────────┘
        ▲                                       │
        │ parse->date,rate                      │
        │                                       ▼
    ┌──────────────┐                   ┌──────────────┐
    │  SQLite DB   │◀──────────────────│ insert/update│
    └──────────────┘                   └──────────────┘
        ▲                                       │
        │ /api/rates                            │
        │                                       ▼
    ┌──────────────┐                   前端 HTML+ECharts
    │  Flask App   │◀───────────────────────────────┐
    │ - Admin(CRUD)│                                │
    │ - REST API   │                                ▼
    └──────────────┘                  ┌───────────────────────┐
                                      │  User Browser Canvas  │
                                      └───────────────────────┘
```

## 📦 安装依赖
#本地运行
macos
```bash
进入项目所在文件夹 cd 拖拽目录进终端
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

windows
进入项目所在文件夹 在地址栏输入cmd回车
```bash
pip install -r requirements.txt
```

## 🚀 启动项目
macos
进入项目所在文件夹 cd 拖拽目录进终端
```bash
./venv/bin/python fetch_usd_rate.py
./venv/bin/python app.py
```

windows
进入项目所在文件夹 在地址栏输入cmd回车
```bash
python fetch_usd_rate.py   # 初次初始化
python app.py
```
访问http://localhost:5050/或ip地址+：5050进行访问
管理员后台http://localhost:5050/admin

## 📁 项目结构

```
your-project/
├── app.py
├── fetch_usd_rate.py
├── rates.db
├── requirements.txt
├── templates/
│   ├── index.html
│   └── admin.html
├── static/
│   └── LOGO.PNG
```
其中LOGO.PNG请自行替换

## 📅 数据来源

数据来源于中国银行官网，默认每天上午9:30定时自动获取。

## 📄 License

MIT License
