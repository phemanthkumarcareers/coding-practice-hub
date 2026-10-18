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
| **📚 Documentation** | [http://localhost:5000/documentation](http://localhost:5000/documentation) | Confluence Knowledge Base: Key Notes, Interview Q&A, Tech Notes, Cloud & Revision Hub |
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

## 📦 Complete Software Prerequisites & Local Installation Guide

Follow these steps to set up and run the application from scratch on any local machine (Windows, macOS, or Linux).

### 1. System Requirements & Prerequisites
- **Python**: Version `3.10`, `3.11`, or `3.12` (tested and recommended on Python `3.12`).
  - Download: [https://www.python.org/downloads/](https://www.python.org/downloads/)
  - *Windows*: Ensure the **"Add python.exe to PATH"** checkbox is checked during installation.
- **Java Virtual Machine (JVM / JDK 17 LTS)** (Required for PySpark & Apache Spark execution):
  - **Eclipse Adoptium Temurin 17 LTS**: Free, open-source enterprise OpenJDK distribution maintained by the Eclipse Foundation.
  - Download: [https://adoptium.net/temurin/releases/?version=17](https://adoptium.net/temurin/releases/?version=17)
  - PySpark requires Java to launch the underlying Apache Spark JVM execution engine.
- **Git**: [https://git-scm.com/downloads](https://git-scm.com/downloads)

### 2. Step-by-Step Installation Instructions

#### Step 1: Install Java (JVM) — Eclipse Adoptium Temurin 17 LTS (Required for PySpark)
Apache Spark and PySpark run on top of the Java Virtual Machine (JVM). To practice PySpark transformations, DataFrame APIs, and Spark SQL locally, Java 17 LTS must be installed:

1. **Download Eclipse Adoptium Temurin 17 LTS**:
   - Go to: [https://adoptium.net/temurin/releases/?version=17](https://adoptium.net/temurin/releases/?version=17)
   - Select your Operating System (**Windows**, **macOS**, or **Linux**) and Architecture (**x64** or **aarch64/ARM**).
   - Download the standard **JDK (.msi on Windows, .pkg on macOS, or .tar.gz/.deb on Linux)**.

2. **Windows Installation Instructions (.msi)**:
   - Double-click the downloaded `.msi` file to launch the setup wizard.
   - On the **"Custom Setup"** screen, you will see a list of feature components:
     - ⚠️ **Important**: Click on **"Set JAVA_HOME variable"** and choose **"Will be installed on local hard drive"**.
     - ⚠️ **Important**: Ensure **"Add to PATH"** is set to **"Will be installed on local hard drive"**.
   - Click **Next** and **Install**.

3. **macOS Installation (via Homebrew or PKG)**:
   ```bash
   brew install --cask temurin@17
   ```

4. **Linux Installation (Ubuntu / Debian)**:
   ```bash
   sudo apt update
   sudo apt install openjdk-17-jdk -y
   ```

5. **Verify Java / JVM in your Terminal**:
   Open a new PowerShell / Command Prompt / Terminal window and verify:
   ```bash
   java -version
   ```
   You should see output similar to:
   ```text
   openjdk version "17.0.x" 2026-xx-xx
   OpenJDK Runtime Environment Temurin-17.0.x+x (build 17.0.x+x)
   OpenJDK 64-Bit Server VM Temurin-17.0.x+x (build 17.0.x+x, mixed mode, sharing)
   ```

> [!TIP]
> **Automatic Java Discovery in the App**:
> Even if you forgot to set the `JAVA_HOME` environment variable, the application automatically scans standard directories on launch (`C:\Program Files\Eclipse Adoptium`, `C:\Program Files\Java`, `C:\Program Files\Microsoft`) to auto-discover your Java installation and inject it into PySpark sessions dynamically. You can also view live Java status anytime on the **Settings & Diagnostics** page (`/settings`).

---

#### Step 2: Clone the Repository
```bash
git clone https://github.com/phemanthkumarcareers/coding-practice-hub.git
cd coding-practice-hub
```

#### Step 3: Create a Python Virtual Environment
Creating an isolated virtual environment prevents library conflicts:
- **Windows (PowerShell / Command Prompt)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

#### Step 4: Upgrade Pip & Install All Python Dependencies
All required dependencies are defined in `requirements.txt`:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 📋 Dependencies Breakdown (`requirements.txt`):
| Package | Version | Purpose in Application |
| :--- | :--- | :--- |
| **`Flask`** | `>=3.0.0` | Core WSGI web framework, REST routing, template rendering & session management |
| **`duckdb`** | `>=1.0.0` | Embedded in-process analytical SQL database engine with multi-DB & direct CSV querying |
| **`pandas`** | `>=2.0.0` | High-performance DataFrame manipulation & tabular data parsing in Python workspace |
| **`pyarrow`** | `>=14.0.0` | Columnar memory format, Parquet file processing, and DuckDB/Pandas zero-copy exchange |
| **`pyspark`** | `>=3.5.0` | Apache Spark Python API for local distributed computing, DataFrame transformations & Spark SQL (requires JVM) |
| **`tabulate`** | `>=0.9.0` | Formatted console tables and clean multi-column stdout printing |
| **`python-dateutil`** | `>=2.8.0` | Date manipulation, streak counter intervals, and calendar tracking |
| **`Werkzeug`** | `>=3.0.0` | Secure filename handling, request routing, and web server WSGI utilities |
| **`Jinja2`** | `>=3.1.0` | Server-side templating engine for responsive UI layouts |

#### Step 5: Verify Environment & Diagnostics
Run the automated test suite to verify that your local environment is correctly configured:
```bash
python -m unittest discover -s tests -p "test_*.py"
```
You should see all 22 tests passing with `OK`.

#### Step 6: Start the Application Server
- **Option A**: Double-click `run.bat` (Windows).
- **Option B**: Run `python app.py` and open [http://localhost:5000/](http://localhost:5000/) in your browser.

---

## 💻 Layout & Navigation Features

### 1. Left Vertical Sidebar (Maximized Screen Height & Collapsible)
- **Top Navbar Replaced with Left Sidebar**: Eliminates the top navbar to free up the full vertical height of the screen (100vh) for code editing and result inspection.
- **Collapsible Mini-Sidebar**: Click the `◀` / `▶` toggle button on the sidebar to collapse it into a compact 68px icon-only mode, maximizing horizontal screen space for wide monitors or split-screen coding.
- **Flicker-Free Persistent State**: User preference is stored in `localStorage` and initialized synchronously during parsing before first paint. When refreshed in minimized mode, it renders directly in minimized state without opening and auto-collapsing. Smooth transitions are enabled strictly during interactive toggle clicks.
- **Integrated Daily Practice Targets (On the Side)**:
  - Date picker and daily session progress badge (`0 / 6`).
  - Vertical list of all 6 daily practice targets (SQL, Python, PySpark, Databricks, DSA, System Design) with live status dots (Completed, In Progress, Not Started).
  - Keeps the top workspace header clean, uncluttered, and free of button collisions.
- **Integrated Sidebar Utilities**:
  - Prominent brand header with full title visibility and dedicated single `◀` / `▶` collapse toggle (clean, uncluttered layout without disturbing double icons).
  - Navigation links (Dashboard, Practice, History, Datasets, Reports, Settings).
  - Quick Search trigger button (`Ctrl + K`).
  - Dedicated bottom theme selector and local server status.

### 2. App-Level Theming (System Default, Light, Dark, Grey)
- **4 Theme Choices**:
  - **🖥️ System Default**: Dynamically tracks your operating system's color scheme preferences (`prefers-color-scheme`) and switches automatically.
  - **☀️ Light Theme**: Crisp, clean, high-contrast light theme with white editor, subtle borders, and dedicated light-mode emblem.
  - **🌙 Dark Theme**: Deep navy/slate developer dark theme with rich visual hierarchy and glowing cyber emblem.
  - **🩶 Grey Theme**: Modern zinc/charcoal dark theme (inspired by Zed and JetBrains Fleet) with metallic emblem.
- **Theme-Adaptive Logo & Icon Background Across Sidebar and Main-Content**:
  - Switching themes dynamically swaps all logo instances across the **Sidebar** and **Main-Content** (Dashboard header, Practice workspace header, History, Datasets, Reports, and Settings), as well as the browser favicon, between `logo-light.png`, `logo-dark.png`, and `logo-grey.png`.
  - Icon container backgrounds, borders, and shadows adapt automatically via `--logo-bg`, `--logo-border`, and `--logo-shadow` CSS variables so the emblem blends natively without dark square artifacts in light mode.
  - Synchronous pre-paint initialization ensures instant display on page refresh without flicker.
- **Live Monaco Synchronization**: Theme switches instantly update Monaco Editor between `vs` and `vs-dark`, and persist across browser sessions in `localStorage` and backend settings.

### 3. Fullscreen & Maximize Editor (70% Editor + 30% Output Console)
- **⛶ Normal Browser Fullscreen**: Click the `⛶ Fullscreen` button in the editor tab bar / practice workspace actions (or press `F11`) to expand the app into true edge-to-edge browser fullscreen mode.
- **🗖 Maximize Editor & Console**: Click the `🗖 Maximize` button to isolate the coding environment into distraction-free focus mode. Unlike legacy focus modes that hide the console, this mode cleanly allocates **70% of screen height to the Monaco Editor** and **30% to the Output Console**, allowing you to code and inspect execution results simultaneously. The vertical resizer handle remains fully interactive.
- **Universal Escape (`Esc`) Handler**: Pressing `Escape` naturally exits fullscreen modes in clean priority:
  1. Closes any open modal dialog (Explorer, Create Database, Confirm, History).
  2. Restores the editor from Maximized Mode to standard view.
  3. Exits edge-to-edge browser fullscreen mode.

### 4. Zero Browser Popups (Custom In-App Modal Dialogs)
- **No Native `alert()`, `confirm()`, or `prompt()`**: All destructive confirmations and database creations use sleek in-app modals (`#app-confirm-modal` and `#create-db-modal`).
- **Confirmation Modals**: Destructive operations (resetting workspace code, deleting custom project files, removing uploaded datasets, restoring backups) use sleek modal dialogs with customizable confirmation and cancellation buttons.

### 5. Multi-File Project Workspace & Folder-Wise Files Explorer for ALL Editors
- **Universal Multi-File Tabs**: Practice real-world file structures directly in the browser across **all 6 technologies** (SQL, Python, PySpark, Databricks, DSA, and System Design).
- **Remove Tab vs Permanent Delete**:
  - **Closing Tabs (`×`)**: Clicking `×` removes the tab from the active editor view without deleting the file from disk or the workspace. The file remains safely saved and can be reopened anytime.
  - **Permanent Deletion**: Destructive deletion is accessed via right-click context menu, tab options, or the Files Drawer trash icon (`🗑️`), requiring confirmation via a custom in-app modal (zero browser popups).
- **Manual File Loading (`📂 Open File ▾`)**: Quickly load any previously saved file into an active tab with one click, or import files from disk.
- **Folder-Wise Files Explorer (`📁 Files`)**: An integrated collapsible file drawer on the left of Monaco editor organizing:
  - 📁 **Current Practice Files**: All files in the active session with open/closed status.
  - 📁 **Past Practice Sessions**: Historical folders grouped by session date for the active technology with one-click file loading.
  - 📁 **Starter Templates & Code Library**: Curated code starters for SQL (joins, window functions, CTEs, DuckDB file queries), Python, PySpark, Databricks, DSA, and System Design.
- **Instant `+ New File` Creation (Zero Popups)**: Clicking `+ New File` instantly generates a new tab with intelligent technology-specific defaults (`query_2.sql`, `module_2.py`, `notes_2.md`) and preloaded template content without modal popups.
- **Inline Tab Renaming (Click-to-Rename, Blur-to-Save)**: Click any file tab name to edit it in place. No extra `X` or tick icons—simply click anywhere on the screen (or press `Enter`) to automatically commit the new filename. Pressing `Escape` cancels the rename.
- **Problem Statement & Notes Accordion Bounds**: Minimized/maximized height constraints ensure the Problem Statement & Practice Notes section has a solid minimum height when opened while capping maximum expansion to protect editor vertical space.
- **Streamlined IDE Tab Bar**: Clean, unified tab header with proper readable font sizing, context-aware file icons (`🗄️ .sql`, `🐍 .py`, `📝 .md`, `⚙️ .json`, `📄`), and zero horizontal scrollbar clutter.
- **Integrated Window & Shortcut Controls**: Quick access to keyboard shortcuts (`Ctrl+Enter to Run | Ctrl+S to Save`), maximize (`🗖`), and full screen (`⛶`) integrated directly into the tab bar right header.
- **Minimized Theme Dropdown**: A compact, elegant dropdown at the bottom of the sidebar displaying the current theme (System, Light, Dark, Grey) that lists options upward without consuming vertical screen space.
- **Sidebar-Only Logo**: Brand logo is dedicated exclusively to the sidebar header, keeping page headers and workspace titles clean, focused, and distraction-free.

### 6. Hierarchical Database, Tables & Views Explorer
- **Database Accordion / Dropdown**: Hierarchically groups all databases (`practice (main / default)` and user-created DuckDB databases in `database/user_dbs/`). Click any database header to expand/collapse its tables and views.
- **Tables & Views Tree with Badges**: Clearly identifies tables (`📄 TABLE`) and views (`👁️ VIEW`), row counts, and column counts.
- **`+` / `−` Column Inspector with Column Sizes**: Click the `+` button beside any table to expand an inspector panel displaying:
  - **Column Name**: Clickable link for instant insertion into the code editor.
  - **Data Type**: `BIGINT`, `VARCHAR`, `BOOLEAN`, `DOUBLE`, `TIMESTAMP`, etc.
  - **Column Size / Length**: Calculated human-readable memory footprints (`4 bytes`, `8 bytes`, `max N chars`, `16 bytes`, etc.).
  - **Nullability**: `YES` or `NO`.
  - **Quick Insert Action**: One-click `+ Add` button to insert column names into your query at cursor position.
- **1-Click Query Snippet Insertion**: Click `Insert Query` on any table to auto-generate a `SELECT * FROM "table" LIMIT 10;` (or cross-database qualified `SELECT * FROM "dbname"."table" LIMIT 10;`).

### 7. Multi-Database Creation & Context Selection in DuckDB / SQL
- **Active Database Selector**: Switch active database context from the top toolbar dropdown (e.g. `main`, `analytics_db`).
- **Direct Table Querying**: When querying the currently active database, query tables directly without schema prefixes:
  ```sql
  SELECT * FROM employees;
  ```
- **Cross-Database Queries**: Query tables from any other attached database using database dot notation:
  ```sql
  SELECT * FROM analytics_db.sales_summary;
  ```
- **In-App `+ Create Database` Modal**: Create brand new persistent DuckDB databases in `database/user_dbs/` using a clean in-app popup modal (no browser popups) with automatic attachment on startup.
- **Live DDL Synchronization**: Any `CREATE TABLE ...` or `CREATE VIEW ...` executed in SQL automatically refreshes the Database Explorer modal.
- **Direct CSV Querying**: Query uploaded CSV files directly using their filename:
  ```sql
  SELECT * FROM sample_employees.csv;
  ```

### 8. Confluence-Style Documentation & Interview Preparation Hub
- **Dedicated Knowledge Workspace (`/documentation`)**:
  - Full-featured documentation platform inspired by Confluence, designed for interview preparation, revision notes, and day-to-day lessons learned.
  - Accessible via the **`📚 Documentation`** sidebar navigation link, direct URL `http://localhost:5000/documentation` (or alias `/notes`), and inside the code editor via `Ctrl + J`.
- **Dedicated Topic Tabs & Editors**:
  - **📝 Key Notes**: Core lessons, conceptual takeaways, and critical daily practice insights.
  - **🎯 Interview Questions & Answers**: Question bank for technical interviews with complete questions, answers, code solutions, time/space complexity, and follow-ups.
  - **🗄️ SQL Notes**: Advanced window functions, SARGable predicates, query execution plans, CTEs, and QUALIFY filtering.
  - **🐍 Python Notes**: Generators, memory footprint, decorators, OOP patterns, and multiprocessing/GIL.
  - **⚡ PySpark Notes**: Spark transformations, actions, broadcast joins, skew handling, and windowing.
  - **🧱 Databricks Notes**: Delta Lake ACID logs, time travel, liquid clustering, Auto Loader, and Unity Catalog.
  - **☁️ Cloud (AWS & Azure)**: Side-by-side data engineering service mapping (S3 vs ADLS Gen2, Athena vs Synapse Serverless, Glue vs ADF, EMR vs Azure Databricks).
  - **🧩 DSA Notes**: Top algorithmic patterns (Two Pointers, Sliding Window, Binary Search) with Big-O complexity tables.
  - **📐 System Design**: Medallion lakehouse architecture (Bronze, Silver, Gold), streaming ingestion pipelines, and interactive **Mermaid.js** flowcharts.
  - **🤝 HR & Behavioral**: Structured responses using the **STAR** framework (Situation, Task, Action, Result) with common leadership and conflict scenarios.
  - **📅 Daily Practice**: Chronological daily logs linked to practice dates.
- **Three Viewing Modes for Seamless Revision & Editing**:
  - **`👁️ View (Doc)`**: Clean, read-only reading mode tailored for interview revision with formatted markdown, styled code blocks, rendered tables, and interactive Mermaid diagrams.
  - **`✏️ Edit (Markdown)`**: Focused full-screen markdown editor equipped with formatting toolbars and syntax helpers.
  - **`🗖 Split View`**: Side-by-side editing with real-time live preview.
- **Document Actions & Quick Controls**:
  - Instant `+ New Doc` creation with category auto-selection.
  - Quick action buttons on every document row in the sidebar tree: `👁️` View (Read-Only), `✏️` Edit, `🗑️` Delete, and `📌` Pin.
  - Real-time autosave with debounce status indicator, `Ctrl + S` instant save shortcut, and 1-click clipboard copy.
  - Rich callout boxes: `> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, and `> [!IMPORTANT]`.
  - Prebuilt template inserter for 1-click generation of interview questions, system design blueprints, and tech cheatsheets.
  - **Window Controls (Maximize, Restore & Fullscreen)**:
    - **`🗖 Maximize / 🗗 Restore`**: Expand the document pane to occupy the entire screen in focus mode, hiding the sidebar for immersive revision (toggle via top header button or toolbar icon). Pressing `Esc` immediately restores the standard view.
    - **`⛶ Fullscreen`**: Expand into true edge-to-edge browser fullscreen (`F11` / Fullscreen button).
- **Embedded Practice Workspace Drawer (`Ctrl + J`)**:
  - Access your notes and documentation directly inside the code editor without navigating away.
  - Toggle using the **`📚 Docs`** button in the header, the `📚` quick button in the editor toolbar, or the global shortcut **`Ctrl + J`**.
  - One-click **`↗ Full Page`** button to open the full documentation hub in a new tab.

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
- **Big Data & Analytics Engine**: PySpark 4.2.0 + Eclipse Adoptium OpenJDK 17 LTS (automatic JVM discovery and worker configuration)
- **Code Execution**: Isolated subprocess runner with multi-file support and configurable timeout protection
- **Frontend**: Flask Jinja2 templates, HTML5, CSS3, Vanilla JavaScript
- **Code Editor**: Monaco Editor (syntax highlighting, line numbers, automatic indentation, dark/light themes)
- **Architecture Diagrams**: Live Mermaid.js rendering for System Design

---

## 📂 Project Directory Structure

```text
Practice/
├── app.py                     # Flask application server (Port 5000)
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
│   │   ├── logo-dark.png      # Dark theme brand application logo
│   │   ├── logo-light.png     # Light theme brand application logo
│   │   ├── logo-grey.png      # Grey (zinc) theme brand application logo
│   │   └── logo.png           # Fallback brand logo
│   ├── css/
│   │   └── style.css          # Theme variables (--app-logo-image), vertical resizer, file tabs
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
- `F11` : Toggle true browser fullscreen
- `Escape` : Close modals / restore from Maximized Editor mode

---

## 🧪 Automated Tests & Strict Isolation

Run the comprehensive test suite verifying core workflows:
```powershell
python -m unittest tests/test_hub.py
```
> [!NOTE]
> **Strict Test Isolation**: The test suite runs against a disposable, isolated SQLite database (`database/test_isolated.db`) and automatically tears down and purges all test databases, DuckDB tables, and backup archives upon completion. The user's practice data in `database/app.db` is strictly preserved and never modified by automated tests.

---

## 🎨 Tactile Animations & Modern UI Polish

- **Tactile Click Feedback**: Interactive elements (`.btn`, `.file-tab`, `.sidebar-link`, `.sidebar-tech-btn`, `.theme-dropdown-trigger`, cards) feature smooth active press scales (`scale(0.96) translateY(1px)`) and coordinates-aware click ripple waves.
- **Glassmorphic Modals**: Custom modal dialogs feature pop-in animations (`cubic-bezier(0.16, 1, 0.3, 1)`), backdrop blur (`backdrop-filter: blur(8px)`), and in-app prompt/confirm controllers.
- **Dynamic Breathing Indicators**: Active practices feature smooth glowing pulses on status dots and badges.
- **Ultra-Clean Scrollbars**: Modern, rounded 6px scrollbars across all viewports with smooth hover states.
