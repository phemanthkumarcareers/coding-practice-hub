<p align="center">
  <img src="static/images/logo.png" width="150" alt="Coding Practice Hub Logo" style="border-radius: 20px;">
</p>

# 🚀 Coding Practice Hub

> **A Complete Local Daily Coding & Interview Practice Web Application**  
> Practice **SQL**, **Python**, **PySpark**, **Databricks**, **DSA**, and **System Design** with real code execution, DuckDB analytical engine, multi-file Python project workspace, multi-database management, Monaco editor, execution history, and streak analytics.

---

## 🌐 Local Application URLs

Access your local application at port `5000`:

👉 **[http://localhost:5000/](http://localhost:5000/)**  
*(Alternative loopback: [http://127.0.0.1:5000/](http://127.0.0.1:5000/))*

### 🗺 Application Routes

| Section | Localhost URL | Description |
| :--- | :--- | :--- |
| **🏠 Dashboard** | [http://localhost:5000/](http://localhost:5000/) | Overview, 8 KPI cards, 6/6 daily progress & streak tracking |
| **💻 Practice Workspace** | [http://localhost:5000/practice](http://localhost:5000/practice) | Full-width Monaco Editor, multi-file workspace, console output & live execution |
| **📜 Practice History** | [http://localhost:5000/history](http://localhost:5000/history) | Calendar & table history, multi-criteria filters & grouping |
| **📊 Datasets Manager** | [http://localhost:5000/datasets](http://localhost:5000/datasets) | Upload CSV/JSON/Parquet, DuckDB table explorer & code snippets |
| **📈 Reports & Analytics** | [http://localhost:5000/reports](http://localhost:5000/reports) | Performance charts, completion/success rates, & activity trends |
| **⚙️ Settings & Backup** | [http://localhost:5000/settings](http://localhost:5000/settings) | Environment status, execution timeouts, & 1-click backup/restore |

---

## ⚡ Quick Start & Running the App

### Option 1: 1-Click Windows Launcher (Auto-opens browser)
Double-click **`run.bat`** in the project folder. It will start the server and automatically launch **[http://localhost:5000/](http://localhost:5000/)** in your browser.

### Option 2: Via Terminal / PowerShell
```powershell
python app.py
```
Then open: **[http://localhost:5000/](http://localhost:5000/)**

---

## 💻 Layout & Navigation Features

### 1. Left Vertical Sidebar (Maximized Screen Height & Collapsible)
- **Top Navbar Replaced with Left Sidebar**: Eliminates the top navbar to free up the full vertical height of the screen (100vh) for code editing and result inspection.
- **Collapsible Mini-Sidebar**: Click the `◀` / `▶` toggle button on the sidebar to collapse it into a compact 68px icon-only mode, maximizing horizontal screen space for wide monitors or split-screen coding.
- **Integrated Sidebar Utilities**:
  - Brand header & navigation links (Dashboard, Practice, History, Datasets, Reports, Settings).
  - Quick Search trigger button (`Ctrl + K`).
  - Dedicated bottom theme selector and local server status.

### 2. App-Level Theming (System Default, Light, Dark, Grey)
- **4 Theme Choices**:
  - **🖥️ System Default**: Dynamically tracks your operating system's color scheme preferences (`prefers-color-scheme`) and switches automatically.
  - **☀️ Light Theme**: Crisp, clean, high-contrast light theme with white editor and subtle grey borders.
  - **🌙 Dark Theme**: Deep navy/slate developer dark theme with rich visual hierarchy.
  - **🩶 Grey Theme**: Modern zinc/charcoal dark theme (inspired by Zed and JetBrains Fleet) with softer contrast.
- **Live Monaco Synchronization**: Theme switches instantly update Monaco Editor between `vs` and `vs-dark`, and persist across browser sessions in `localStorage` and backend settings.

### 3. Vertical Split Stack (Full-Width Editor with Bottom Console)
- **Maximized Coding Width**: The Monaco Editor stretches across 100% of the pane width, ideal for extensive scripts, wide SQL joins, and complex classes.
- **Draggable Horizontal Resizer**: Drag the horizontal divider bar between the code editor and bottom console to adjust the view heights dynamically.
- **Integrated Console & Status**: Execution status badges, execution times in milliseconds, formatted output tables for SQL, and terminal stderr logs render in the dedicated console pane below the code.

### 4. Multi-File Python Project Workspace
- **Multi-File Tab Bar**: Practice real-world project structures directly in the browser across Python, DSA, and Databricks.
- **`+ New File` Creation**: Add helper modules such as `utils.py`, `models.py`, or `config.py`.
- **Seamless Cross-Module Imports**: Subprocess runner executes all project files together in an isolated workspace, allowing statements like:
  ```python
  from utils import calculate_metrics
  import helper
  ```
- **File Management**: Switch tabs with a single click, delete files, and preserve editor code across all tabs.

### 5. Multi-Database Creation & Context Selection in DuckDB / SQL
- **Active Database Selector**: Switch active database context from the top toolbar dropdown (e.g. `main`, `analytics_db`).
- **Direct Table Querying**: When querying the currently active database, query tables directly without schema prefixes:
  ```sql
  SELECT * FROM employees;
  ```
- **Cross-Database Queries**: Query tables from any other attached database using database dot notation:
  ```sql
  SELECT * FROM analytics_db.sales_summary;
  ```
- **`+ Create Database`**: Create brand new persistent DuckDB databases in `database/user_dbs/` with automatic attachment on startup.
- **Live DDL Synchronization**: Any `CREATE TABLE ...` or `CREATE VIEW ...` executed in SQL automatically refreshes the Database Explorer modal.
- **Direct CSV Querying**: Query uploaded CSV files directly using their filename:
  ```sql
  SELECT * FROM sample_employees.csv;
  ```

---

## 🎯 Daily Practice Target: 6 Practices / Day

Every calendar day is modeled as **one unified Daily Practice Session** containing exactly six technology records:
- **1 SQL**: DuckDB analytical SQL engine (CTEs, Window functions, Aggregations, Joins, Multi-DB)
- **1 Python**: Multi-file Python 3.12 subprocess execution with module imports and stdout/stderr capture
- **1 PySpark**: Local PySpark DataFrame & Spark SQL practice
- **1 Databricks**: Practice subtypes (Delta Lake, Auto Loader, PySpark, SQL, Unity Catalog)
- **1 DSA**: Data structures & algorithms with test cases and time/space complexity tracking
- **1 System Design**: Structured architecture workspace with live **Mermaid.js** diagrams

> **Completion Logic**: A session reaches **6/6 COMPLETED** only when all 6 technology exercises are completed. Every state from `0/6` to `6/6` is tracked visually on the dashboard and streak counter.

---

## 🔒 Practice Data Privacy & Git Policy

All user practice data is strictly isolated and excluded from version control:
- **Ignored Databases**: All `.db`, `.duckdb`, `.sqlite`, `.sqlite3`, and `database/user_dbs/*.duckdb` files are ignored in `.gitignore`.
- **Ignored Practice Datasets**: All user-uploaded datasets in `uploads/` are completely excluded from GitHub commits.
- **Ignored Subprocess Temp Files**: Ephemeral execution scripts and temporary caches in `workspace/` are excluded.
- **Pure Code Tracking**: Only application source code, templates, static assets, and migration scripts are committed to the GitHub repository.

---

## 🛠 Technology Stack

- **Backend**: Python 3.12.10, Flask (served on port `5000`)
- **Metadata & History**: SQLite (`database/app.db`) with normalized schema, foreign keys, and indexes
- **SQL Practice Engine**: DuckDB (`database/practice.duckdb` & `database/user_dbs/*.duckdb`) multi-database engine
- **Code Execution**: Isolated subprocess runner with multi-file support and configurable timeout protection
- **Frontend**: Flask Jinja2 templates, HTML5, CSS3, Vanilla JavaScript
- **Code Editor**: Monaco Editor (syntax highlighting, line numbers, automatic indentation, dark/light themes)
- **Architecture Diagrams**: Live Mermaid.js rendering for System Design
- **WSGI Callable**: Standard `application.py` / `wsgi.py` compatible with Apache `mod_wsgi`, Gunicorn, and Waitress

---

## 📂 Project Directory Structure

```text
Practice/
├── app.py                     # Flask entry point (Port 5000)
├── application.py             # WSGI application callable
├── wsgi.py                    # WSGI entrypoint
├── run.bat                    # 1-click launcher (starts server & opens browser)
├── config.py                  # Paths, constants, and default configurations
├── requirements.txt           # Python dependencies
├── README.md                  # Comprehensive documentation & URL references
├── database/
│   ├── .gitkeep
│   ├── app.db                 # Auto-initialized SQLite database (ignored in git)
│   ├── practice.duckdb        # Auto-initialized DuckDB database (ignored in git)
│   └── user_dbs/              # Custom user DuckDB databases (ignored in git)
│       └── .gitkeep
├── models/
│   ├── __init__.py
│   └── db.py                  # Schema creation, migrations & daily session helpers
├── routes/
│   ├── dashboard.py           # Dashboard KPIs, streak metrics, today's targets
│   ├── practice.py            # Practice workspace, Monaco editor, execution, multi-db & multi-file API
│   ├── history.py             # Practice history calendar, multi-filters & grouping
│   ├── datasets.py            # File uploads (CSV/JSON/Parquet), DuckDB views, previews
│   ├── reports.py             # Analytics, completion %, success %, trends, global search
│   └── settings.py            # Environment detection, execution timeout, backup/restore
├── services/
│   ├── code_executor.py       # Isolated subprocess runner with multi-file project support
│   ├── duckdb_service.py      # DuckDB multi-database executor, live DDL syncer & schema explorer
│   ├── pyspark_service.py     # PySpark execution & environment diagnostics
│   ├── streak_service.py      # Streaks, consistency & 6/6 calculation
│   └── backup_service.py      # Zip archive creation & restore
├── static/
│   ├── images/
│   │   └── logo.png           # Brand application logo
│   ├── css/
│   │   └── style.css          # Developer-tool dark/light themes, vertical resizer, file tabs
│   └── js/
│       ├── app.js             # Global shortcuts (Ctrl+K), theme switcher, search modal
│       └── practice.js        # Monaco controller, tab switcher, multi-file manager, multi-db selector
├── templates/
│   ├── base.html              # Shell layout with logo brand & favicon
│   ├── dashboard.html         # Dashboard overview with logo branding
│   ├── practice.html          # Vertical split layout (Full width Monaco on top | Output below)
│   ├── history.html           # Calendar & table history, multi-filters & grouping
│   ├── tech_view.html         # Technology-specific browse views
│   ├── datasets.html          # Dataset management & code snippet generators
│   ├── reports.html           # Reports, activity trends & difficulty distributions
│   └── settings.html          # Settings, environment status & backup/restore
├── uploads/                   # Uploaded datasets (ignored in git)
├── workspace/                 # Subprocess isolated script workspaces (ignored in git)
├── tests/
│   └── test_hub.py            # Automated unit and integration tests
├── backups/                   # Backup ZIP archives (ignored in git)
└── logs/                      # Application execution logs (ignored in git)
```

---

## 💡 Keyboard Shortcuts

- `Ctrl + Enter` : Execute code in the active editor
- `Ctrl + S` : Manually save current practice state
- `Ctrl + K` : Open Global Practice Search modal from any page
- `Escape` : Close modals / dialogs

---

## 🧪 Running Automated Tests

Run the comprehensive test suite verifying core workflows:
```powershell
python -m unittest tests/test_hub.py
```
