# 🚀 Coding Practice Hub

> **A Complete Local Daily Coding & Interview Practice Web Application**  
> Practice **SQL**, **Python**, **PySpark**, **Databricks**, **DSA**, and **System Design** with real code execution, DuckDB analytical engine, Monaco editor, execution history, and streak analytics.

---

## 🌐 Virtual Host & Local URLs

You can access the application using your custom virtual host name or standard localhost:

| Section | Virtual Host URL (Custom Name) | Standard Localhost URL | Description |
| :--- | :--- | :--- | :--- |
| **🏠 Dashboard** | [http://coding-practice-hub:5000/](http://coding-practice-hub:5000/) *(or [http://coding-practice-hub/](http://coding-practice-hub/))* | [http://localhost:5000/](http://localhost:5000/) | Overview, 8 KPI cards, 6/6 daily progress & streak tracking |
| **💻 Practice Workspace** | [http://coding-practice-hub:5000/practice](http://coding-practice-hub:5000/practice) | [http://localhost:5000/practice](http://localhost:5000/practice) | Monaco Editor workspace with 6 technology tabs & execution |
| **📜 Practice History** | [http://coding-practice-hub:5000/history](http://coding-practice-hub:5000/history) | [http://localhost:5000/history](http://localhost:5000/history) | Calendar & table history, multi-criteria filters & grouping |
| **📊 Datasets Manager** | [http://coding-practice-hub:5000/datasets](http://coding-practice-hub:5000/datasets) | [http://localhost:5000/datasets](http://localhost:5000/datasets) | Upload CSV/JSON/Parquet, DuckDB table explorer & code snippets |
| **📈 Reports & Analytics** | [http://coding-practice-hub:5000/reports](http://coding-practice-hub:5000/reports) | [http://localhost:5000/reports](http://localhost:5000/reports) | Performance charts, completion/success rates, & activity trends |
| **⚙️ Settings & Backup** | [http://coding-practice-hub:5000/settings](http://coding-practice-hub:5000/settings) | [http://localhost:5000/settings](http://localhost:5000/settings) | Environment status, execution timeouts, & 1-click backup/restore |

---

## 🛠 Enabling the Virtual Host (`coding-practice-hub`)

Windows requires a one-time administrator step to map the virtual host name `coding-practice-hub` to `127.0.0.1`:

### Method 1: Using the 1-Click Script (Recommended)
1. Open the project folder: `C:\Users\PC\Hemanth\Learning\Practice`
2. **Right-click** on **`add_virtual_host.bat`**
3. Select **"Run as administrator"** and approve the prompt.

### Method 2: PowerShell (Run as Administrator)
1. Press the **Windows Key**, type **PowerShell**, right-click it, and select **"Run as administrator"**.
2. Run this command:
```powershell
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "`n127.0.0.1 coding-practice-hub`n127.0.0.1 coding-practice-hub.local"
ipconfig /flushdns
```

Once completed, you can use **[http://coding-practice-hub:5000/](http://coding-practice-hub:5000/)** or **[http://coding-practice-hub/](http://coding-practice-hub/)** directly in your browser!

---

## 🏛️ Apache + mod_wsgi Deployment (VirtualHost)

If deploying with an Apache HTTP Server using `mod_wsgi`, use the pre-configured [`apache_vhost.conf`](file:///c:/Users/PC/Hemanth/Learning/Practice/apache_vhost.conf) and WSGI entry point [`application.py`](file:///c:/Users/PC/Hemanth/Learning/Practice/application.py) / [`wsgi.py`](file:///c:/Users/PC/Hemanth/Learning/Practice/wsgi.py).

### 1. WSGI Callable (`application.py`)
```python
from app import create_app

# WSGI callable for mod_wsgi / Waitress / Gunicorn
application = create_app()
```

### 2. Apache VirtualHost (`apache_vhost.conf`)
Include in your Apache `httpd.conf`:
```apache
<VirtualHost *:80>
    ServerName coding-practice-hub
    ServerAlias www.coding-practice-hub coding-practice-hub.local
    DocumentRoot "C:/Users/PC/Hemanth/Learning/Practice"

    Alias /static "C:/Users/PC/Hemanth/Learning/Practice/static"
    <Directory "C:/Users/PC/Hemanth/Learning/Practice/static">
        Require all granted
    </Directory>

    WSGIScriptAlias / "C:/Users/PC/Hemanth/Learning/Practice/wsgi.py"

    <Directory "C:/Users/PC/Hemanth/Learning/Practice">
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
</VirtualHost>
```

---

## ⚡ Starting the Application

### 1-Click Windows Launcher:
Double-click **`run.bat`**. It will start Flask on both port `5000` and port `80`, and automatically launch your browser.

### Via Command Line / Terminal:
```powershell
python app.py
```

---

## 🎯 Daily Practice Target: 6 Practices / Day

Every calendar day is modeled as **one unified Daily Practice Session** containing exactly six technology records:
- **1 SQL**: DuckDB analytical SQL engine (CTEs, Window functions, Aggregations, Joins)
- **1 Python**: Local Python 3.12 subprocess execution with stdout/stderr capture
- **1 PySpark**: Local PySpark DataFrame & Spark SQL practice
- **1 Databricks**: Practice subtypes (Delta Lake, Auto Loader, PySpark, SQL, Unity Catalog)
- **1 DSA**: Data structures & algorithms with test cases and time/space complexity tracking
- **1 System Design**: Structured architecture workspace with live **Mermaid.js** diagrams

> **Completion Logic**: A session reaches **6/6 COMPLETED** only when all 6 technology exercises are completed. Every state from `0/6` to `6/6` is tracked visually on the dashboard and streak counter.

---

## 🛠 Technology Stack

- **Backend**: Python 3.12.10, Flask (Dual-port serving on `5000` and `80`)
- **Metadata & History**: SQLite (`database/app.db`) with normalized schema, foreign keys, and indexes
- **SQL Practice Engine**: DuckDB (`database/practice.duckdb`) query engine with dataset auto-views
- **Code Execution**: Isolated subprocess runner with configurable timeout protection
- **Frontend**: Flask Jinja2 templates, HTML5, CSS3, Vanilla JavaScript
- **Code Editor**: Monaco Editor (syntax highlighting, line numbers, automatic indentation, dark/light themes)
- **Architecture Diagrams**: Live Mermaid.js rendering for System Design

---

## 📂 Project Directory Structure

```text
Practice/
├── app.py                     # Flask entry point (Dual-port 5000 and 80)
├── add_virtual_host.bat       # Script to map virtual host coding-practice-hub in hosts file
├── run.bat                    # 1-click launcher (starts server & opens browser)
├── config.py                  # Paths, constants, and default configurations
├── requirements.txt           # Python dependencies
├── README.md                  # Comprehensive documentation & virtual host references
├── database/
│   ├── app.db                 # Auto-initialized SQLite database
│   └── practice.duckdb        # Auto-initialized DuckDB database
├── models/
│   ├── __init__.py
│   └── db.py                  # Schema creation, migrations & daily session helpers
├── routes/
│   ├── dashboard.py           # Dashboard KPIs, streak metrics, today's targets
│   ├── practice.py            # Practice workspace, Monaco editor, execution, autosave
│   ├── history.py             # Practice history calendar, multi-filters & grouping
│   ├── datasets.py            # File uploads (CSV/JSON/Parquet), DuckDB views, previews
│   ├── reports.py             # Analytics, completion %, success %, trends, global search
│   └── settings.py            # Environment detection, execution timeout, backup/restore
├── services/
│   ├── code_executor.py       # Isolated subprocess runner with timeout guard
│   ├── duckdb_service.py      # DuckDB query executor & schema explorer
│   ├── pyspark_service.py     # PySpark execution & environment diagnostics
│   ├── streak_service.py      # Streaks, consistency & 6/6 calculation
│   └── backup_service.py      # Zip archive creation & restore
├── static/
│   ├── css/
│   │   └── style.css          # Developer-tool dark/light themes, split resizer
│   └── js/
│       ├── app.js             # Global shortcuts (Ctrl+K), theme switcher, search modal
│       └── practice.js        # Monaco controller, tab switcher, runner, autosave
├── templates/
│   ├── base.html              # Developer-tool navigation shell & search modal
│   ├── dashboard.html         # Dashboard overview & today's progress
│   ├── practice.html          # Resizable split workspace (Monaco 70% | Output 30%)
│   ├── history.html           # Calendar & table history, multi-filters & grouping
│   ├── tech_view.html         # Technology-specific browse views
│   ├── datasets.html          # Dataset management & code snippet generators
│   ├── reports.html           # Reports, activity trends & difficulty distributions
│   └── settings.html          # Settings, environment status & backup/restore
├── uploads/                   # Uploaded datasets (CSV, JSON, Parquet)
├── workspace/                 # Subprocess isolated script workspaces
├── tests/
│   └── test_hub.py            # Automated unit and integration tests
├── backups/                   # Backup ZIP archives
└── logs/                      # Application execution logs
```

---

## 💡 Keyboard Shortcuts

- `Ctrl + Enter` : Execute code in the active editor
- `Ctrl + S` : Manually save current practice state
- `Ctrl + K` : Open Global Practice Search modal from any page
- `Escape` : Close modals / dialogs

---

## 🧪 Running Automated Tests

Run the comprehensive test suite verifying all 9 core workflows:
```powershell
python -m unittest tests/test_hub.py
```
