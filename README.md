# Coding Practice Hub

**Coding Practice Hub** is a local web application built for daily technical coding and interview practice across six core disciplines: **SQL**, **Python**, **PySpark**, **Databricks**, **DSA (Data Structures & Algorithms)**, and **System Design**.

---

## 🎯 Daily Practice Model & Target

- **Daily Target**: **6 practices / day** (1 SQL | 1 Python | 1 PySpark | 1 Databricks | 1 DSA | 1 System Design).
- **Session Architecture**: Every calendar day is modeled as **one Daily Practice Session** containing exactly six technology practice records.
- **Completion Tracking**: A day is **6/6 COMPLETED** only when all six technology practices are marked completed. Visually displays every state from `0/6` through `6/6`.

---

## 🛠 Technology Stack

- **Backend**: Python 3.12.10, Flask (served on a single port `5000`)
- **Metadata & History**: SQLite (`database/app.db`) with normalized schema, foreign keys, and indexes
- **SQL Practice Engine**: DuckDB (`database/practice.duckdb`) supporting SELECT, JOIN, GROUP BY, CTEs, Window Functions, and Analytical SQL
- **Subprocess Execution**: Isolated Python subprocess executor with configurable timeout protection
- **Spark Execution**: Local PySpark with automatic Java/SPARK_HOME detection and non-crashing diagnostics
- **Frontend**: Flask Jinja2 templates, HTML5, CSS3, Vanilla JavaScript
- **Code Editor**: Monaco Editor (syntax highlighting, line numbers, automatic indentation, dark/light themes)
- **Architecture Diagrams**: Mermaid.js preview for System Design workspaces

---

## 🚀 Quick Start (Windows Setup)

### 1. Prerequisites
- Python 3.12.10 installed on your system.
- (Optional for PySpark): Java JDK 11 or 17 (set in `JAVA_HOME`). DuckDB and Python run without Java.

### 2. Setup Virtual Environment & Install Dependencies
Open PowerShell or Command Prompt in this folder (`c:\Users\PC\Hemanth\Learning\Practice`):

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Launch the Application
```powershell
python app.py
```

Open your browser and navigate to:
```
http://localhost:5000
```

---

## 📂 Project Directory Structure

```text
Practice/
├── app.py                     # Flask entry point and blueprint registry
├── config.py                  # Paths, constants, and default configurations
├── requirements.txt           # Python dependencies
├── README.md                  # Comprehensive setup and usage documentation
├── database/
│   ├── app.db                 # SQLite database (auto-initialized)
│   └── practice.duckdb        # DuckDB database (auto-initialized)
├── models/
│   ├── __init__.py
│   └── db.py                  # Schema creation, migrations & query helpers
├── routes/
│   ├── dashboard.py           # Dashboard KPIs, streak metrics, today's targets
│   ├── practice.py            # Practice workspace, Monaco editor, execution, autosave
│   ├── history.py             # Practice history calendar, multi-filters, grouping
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

## 💡 Key Features & Workflow

### 1. Daily Practice Workflow
1. From the **Dashboard**, click **Start Today's Practice** or **Continue Today's Practice**.
2. Work through each of the **6 Technology Tabs**:
   - **SQL**: Write DuckDB SQL queries. Inspect schema via the *Table Explorer*.
   - **Python**: Write algorithms, scripts, or pandas code. Pre-mapped `DATASETS` dictionary is accessible.
   - **PySpark**: Practice PySpark DataFrame transformations, joins, and aggregations.
   - **Databricks**: Choose practice subtype (PySpark, SQL, Delta Lake, Auto Loader, Unity Catalog, etc.).
   - **DSA**: Enter problem constraints, time/space complexity, test cases, and solve in Python.
   - **System Design**: Write Markdown with embedded `mermaid` diagrams; preview updates live on the right pane.
3. Press **Ctrl+Enter** or click **▶ Run** to execute code.
   - Code is executed in an isolated subprocess with timeout handling.
   - Every execution attempt is saved into **Execution History** (snapshot, duration, status, output, error).
4. Restoring code from execution history never deletes newer history.
5. Edits are **autosaved** every 15 seconds. Click **✓ Complete** when done.

### 2. Dataset Management & Querying
- Upload `.csv`, `.parquet`, or `.json` files in the **Datasets** tab.
- Uploaded datasets are **immediately queryable in DuckDB** (e.g. `SELECT * FROM sample_employees_1;`).
- One-click copy for **SQL**, **Python (pandas)**, and **PySpark** snippets.

### 3. Practice History & Technology Views
- Browse past dates in a calendar/table format with 6 status indicators.
- Filter across **Date Range**, **Technology**, **Status**, **Difficulty**, **Topic**, and **Tags**.
- Group results dynamically by Date, Technology, Status, Difficulty, or Topic.
- Dedicated browse views for each technology (`/history/tech/SQL`, etc.).

### 4. Global Search (`Ctrl+K`)
- Press `Ctrl+K` from any screen to search across titles, problem statements, code, notes, topics, and tags.

### 5. Backup & Restore
- Go to **Settings** -> **Backup & Restore**.
- Click **Create Backup Now** to download a compressed `.zip` containing your SQLite database, DuckDB database, uploads, and workspace files.
- Restore from a `.zip` file with confirmation.

---

## 🧪 Running Automated Tests

Run the test suite verifying all 9 core workflows:
```powershell
python -m unittest tests/test_hub.py
```

---

## 🔧 Troubleshooting

- **PySpark / Java Missing**:
  DuckDB and Python work out of the box. If you want to execute PySpark code locally, install OpenJDK 17 and set `JAVA_HOME` in **Settings**. If Java is missing, the output console provides guidance without crashing the application.
- **Port Conflict**:
  If port `5000` is in use, modify `app.run(port=5000)` in `app.py` or specify the port.
