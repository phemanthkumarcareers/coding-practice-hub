# 🚀 Coding Practice Hub

> **A Complete Local Daily Coding & Interview Practice Web Application**  
> Practice **SQL**, **Python**, **PySpark**, **Databricks**, **DSA**, and **System Design** with real code execution, DuckDB analytical engine, Monaco editor, execution history, and streak analytics.

---

## 🌐 Custom Local Domain URL

Access your application directly via the custom local domain URL:

👉 **[http://coding-practice-hub/](http://coding-practice-hub/)**

*(Fallback / Alternative: [http://localhost:5000/](http://localhost:5000/))*

### 🗺 Route Directory

| Section | Custom Domain URL | Standard Localhost URL | Description |
| :--- | :--- | :--- | :--- |
| **🏠 Dashboard** | [http://coding-practice-hub/](http://coding-practice-hub/) | [http://localhost:5000/](http://localhost:5000/) | Overview, 8 KPI cards, 6/6 daily progress & streak tracking |
| **💻 Practice Workspace** | [http://coding-practice-hub/practice](http://coding-practice-hub/practice) | [http://localhost:5000/practice](http://localhost:5000/practice) | Monaco Editor workspace with 6 technology tabs & execution |
| **📜 Practice History** | [http://coding-practice-hub/history](http://coding-practice-hub/history) | [http://localhost:5000/history](http://localhost:5000/history) | Calendar & table history, multi-criteria filters & grouping |
| **📊 Datasets Manager** | [http://coding-practice-hub/datasets](http://coding-practice-hub/datasets) | [http://localhost:5000/datasets](http://localhost:5000/datasets) | Upload CSV/JSON/Parquet, DuckDB table explorer & code snippets |
| **📈 Reports & Analytics** | [http://coding-practice-hub/reports](http://coding-practice-hub/reports) | [http://localhost:5000/reports](http://localhost:5000/reports) | Performance charts, completion/success rates, & activity trends |
| **⚙️ Settings & Backup** | [http://coding-practice-hub/settings](http://coding-practice-hub/settings) | [http://localhost:5000/settings](http://localhost:5000/settings) | Environment status, execution timeouts, & 1-click backup/restore |

---

## 🛠 One-Time Setup for `http://coding-practice-hub/` (Windows)

To allow Windows to resolve `coding-practice-hub` to your local machine (`127.0.0.1`):

### Option A: 1-Click Script (Recommended)
Right-click **`setup_domain.bat`** in the project directory and choose **"Run as administrator"**.  
*(This automatically adds `127.0.0.1 coding-practice-hub` to `C:\Windows\System32\drivers\etc\hosts` and flushes the DNS cache).*

### Option B: Manual Command (PowerShell as Administrator)
Open PowerShell as Administrator and run:
```powershell
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "`n127.0.0.1 coding-practice-hub"
ipconfig /flushdns
```

---

## ⚡ Starting the Application

### 1-Click Windows Launcher:
Double-click **`run.bat`**. It will start Flask and automatically launch **[http://coding-practice-hub/](http://coding-practice-hub/)** in your browser.

### Via Command Line / Terminal:
```powershell
python app.py
```
*(By default, the server listens on port `80` so you can use `http://coding-practice-hub/` without specifying any port. You can also specify `--port 5000` if desired).*

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

- **Backend**: Python 3.12.10, Flask
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
├── app.py                     # Flask entry point, intelligent port resolver (80/5000)
├── setup_domain.bat           # 1-click script to map coding-practice-hub in hosts file
├── run.bat                    # 1-click launcher (starts server & opens browser)
├── config.py                  # Paths, constants, and default configurations
├── requirements.txt           # Python dependencies
├── README.md                  # Comprehensive documentation & URL references
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
