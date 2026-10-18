import sqlite3
import json
import os
from datetime import datetime, date
from pathlib import Path
from config import SQLITE_PATH, DEFAULT_SETTINGS, TECHNOLOGIES, STATUSES

def get_connection():
    db_path = os.environ.get("CODING_HUB_DB_PATH") or SQLITE_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS daily_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE,
        status TEXT DEFAULT 'NOT STARTED',
        completed_count INTEGER DEFAULT 0,
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS practices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL REFERENCES daily_sessions(id) ON DELETE CASCADE,
        technology TEXT NOT NULL,
        title TEXT DEFAULT '',
        difficulty TEXT DEFAULT 'Medium',
        topic TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        question TEXT DEFAULT '',
        code TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        status TEXT DEFAULT 'NOT STARTED',
        latest_output TEXT DEFAULT '',
        latest_error TEXT DEFAULT '',
        duration_ms INTEGER DEFAULT 0,
        extra_metadata TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP NULL,
        UNIQUE(session_id, technology)
    );

    CREATE TABLE IF NOT EXISTS executions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        practice_id INTEGER NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
        code_snapshot TEXT NOT NULL,
        output TEXT DEFAULT '',
        error_output TEXT DEFAULT '',
        status TEXT NOT NULL,
        duration_ms INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS datasets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        original_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        table_name TEXT NOT NULL UNIQUE,
        row_count INTEGER DEFAULT 0,
        column_count INTEGER DEFAULT 0,
        columns_json TEXT DEFAULT '[]',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS practice_tags (
        practice_id INTEGER NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
        tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
        PRIMARY KEY(practice_id, tag_id)
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );

    CREATE TABLE IF NOT EXISTS key_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT DEFAULT 'Daily Practice',
        date_str TEXT DEFAULT '',
        technology TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        content TEXT DEFAULT '',
        is_pinned INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_practices_session ON practices(session_id);
    CREATE INDEX IF NOT EXISTS idx_practices_tech ON practices(technology);
    CREATE INDEX IF NOT EXISTS idx_practices_status ON practices(status);
    CREATE INDEX IF NOT EXISTS idx_executions_practice ON executions(practice_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_date ON daily_sessions(date);
    CREATE INDEX IF NOT EXISTS idx_key_notes_date ON key_notes(date_str);
    CREATE INDEX IF NOT EXISTS idx_key_notes_cat ON key_notes(category);
    CREATE INDEX IF NOT EXISTS idx_key_notes_tech ON key_notes(technology);
    """)

    # Populate default settings if not exists
    for key, val in DEFAULT_SETTINGS.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

    # Populate starter Key Notes if table is empty
    cursor.execute("SELECT COUNT(*) as cnt FROM key_notes")
    if cursor.fetchone()["cnt"] == 0:
        today_str = date.today().isoformat()
        starter_notes = [
            (
                f"Daily Practice Notes - {today_str}",
                "Daily Practice",
                today_str,
                "SQL",
                "daily, practice, tips",
                "# Daily Practice Notes\n\n> [!NOTE]\n> Record your daily practice insights, problem-solving approaches, and interview takeaways here.\n\n## 🎯 Today's Goals & Focus Areas\n- [ ] SQL: Advanced window functions and analytical queries\n- [ ] Python: Pandas data transformation and vectorized operations\n- [ ] PySpark: Dataframe joins, aggregation patterns, and caching\n- [ ] DSA: Sliding window or binary search problem\n\n## 💡 Key Tips & Syntax Learned\n- **SQL CTEs:** Always filter early in the CTE before doing expensive joins.\n- **DuckDB Tip:** You can query CSV files directly with `SELECT * FROM 'data.csv'`.\n\n## 📝 Personal Notes & Questions\n- Need to review partitioning vs clustering performance differences.",
                1
            ),
            (
                "SQL Query Optimization & Performance Tips",
                "SQL",
                today_str,
                "SQL",
                "sql, performance, tips, indexing",
                "# SQL Query Optimization & Performance Tips\n\n> [!TIP]\n> High-impact tips for optimizing SQL queries in production databases and technical interviews.\n\n### 1. Window Functions vs Self-Joins\n- Always prefer `ROW_NUMBER()`, `RANK()`, or `DENSE_RANK()` over self-joins for top-N per group queries.\n\n### 2. SARGable Query Predicates\n- Avoid wrapping indexed columns in functions in the `WHERE` clause:\n  - ❌ `WHERE YEAR(order_date) = 2026`\n  - ✅ `WHERE order_date >= '2026-01-01' AND order_date < '2027-01-01'`\n\n### 3. QUALIFY Clause in Modern Engines\n- Engines like DuckDB, Snowflake, and BigQuery support `QUALIFY` to filter window function results without an extra subquery:\n```sql\nSELECT emp_id, department, salary\nFROM employees\nQUALIFY ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) = 1;\n```",
                1
            ),
            (
                "PySpark Common Patterns & Transformations Cheatsheet",
                "PySpark",
                today_str,
                "PySpark",
                "pyspark, spark, cheatsheet, bigdata",
                "# PySpark Common Patterns & Transformations Cheatsheet\n\n> [!IMPORTANT]\n> Essential PySpark DataFrame operations and best practices.\n\n### 1. Safe Aggregations\n```python\nfrom pyspark.sql import functions as F\nfrom pyspark.sql.window import Window\n\n# Window specification\nwin_spec = Window.partitionBy('department').orderBy(F.col('salary').desc())\n\ndf_ranked = df.withColumn('rank', F.dense_rank().over(win_spec))\n```\n\n### 2. Handling Skewed Joins\n- Use **Broadcast Joins** when one table is small (< 100MB):\n```python\njoined_df = large_df.join(F.broadcast(small_df), 'lookup_id', 'left')\n```",
                0
            ),
            (
                "DSA Patterns & Time Complexity Reference",
                "DSA",
                today_str,
                "DSA",
                "dsa, algorithms, interview, patterns",
                "# DSA Patterns & Time Complexity Reference\n\n> [!TIP]\n> Quick cheat sheet for identifying algorithmic patterns based on problem constraints.\n\n| Input Size (N) | Target Time Complexity | Likely Algorithms / Patterns |\n| :--- | :--- | :--- |\n| $N \\le 10$ | $O(N!), O(2^N)$ | Backtracking, Recursion, Permutations |\n| $N \\le 10^3$ | $O(N^2)$ | 2D Dynamic Programming, Nested Loops |\n| $N \\le 10^5$ | $O(N \\log N)$ | Sorting, Divide & Conquer, Heap / PriorityQueue |\n| $N \\le 10^6$ | $O(N)$ | Two Pointers, Sliding Window, Hash Map, Monotonic Stack |\n| Sorted Array | $O(\\log N)$ | Binary Search |\n\n### Core Templates\n#### Two Pointers (Opposite Ends)\n```python\nleft, right = 0, len(nums) - 1\nwhile left < right:\n    curr_sum = nums[left] + nums[right]\n    if curr_sum == target:\n        return [left, right]\n    elif curr_sum < target:\n        left += 1\n    else:\n        right -= 1\n```",
                1
            )
        ]
        for note in starter_notes:
            cursor.execute("""
                INSERT INTO key_notes (title, category, date_str, technology, tags, content, is_pinned)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, note)

    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    if row:
        return row["value"]
    return default

def set_setting(key, value):
    conn = get_connection()
    conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))
    conn.commit()
    conn.close()

def get_all_settings():
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

def get_or_create_daily_session(session_date_str=None):
    if not session_date_str:
        session_date_str = date.today().isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM daily_sessions WHERE date = ?", (session_date_str,))
    session = cursor.fetchone()
    
    if not session:
        cursor.execute("INSERT INTO daily_sessions (date) VALUES (?)", (session_date_str,))
        session_id = cursor.lastrowid
        
        # Auto-create the 6 technology practice records
        default_templates = {
            "SQL": "-- Query uploaded datasets directly by file name:\nSELECT * FROM sample_employees.csv LIMIT 5;\n\n-- Department summary:\nSELECT department, count(*) AS count, round(avg(salary), 2) AS avg_sal\nFROM sample_employees.csv\nGROUP BY department\nORDER BY avg_sal DESC;",
            "Python": "import pandas as pd\n\n# Uploaded CSV files are accessible directly by filename!\ndf = pd.read_csv('sample_employees.csv')\nprint(df.head())\nprint('\\nDepartment Salary Summary:')\nprint(df.groupby('department')['salary'].mean().round(2))",
            "PySpark": "# Write your PySpark code here\n# Note: SparkSession is available or can be initialized\nfrom pyspark.sql import SparkSession\n\nspark = SparkSession.builder.appName('Practice').getOrCreate()\ndf = spark.createDataFrame([(1, 'Spark'), (2, 'DuckDB')], ['id', 'engine'])\ndf.show()",
            "Databricks": "# Databricks Notebook / Code Practice\n# Technology subtype: Delta Lake / PySpark / SQL / Auto Loader\nprint('Databricks Practice Workspace')",
            "DSA": "# Data Structures & Algorithms Practice\nclass Solution:\n    def solve(self, nums):\n        # Implement optimal solution\n        return nums\n\nif __name__ == '__main__':\n    s = Solution()\n    print(s.solve([1, 2, 3]))",
            "System Design": "# System Design Practice Workspace\n\n## 1. Problem Statement\n\n## 2. Requirements\n### Functional Requirements\n- \n\n### Non-Functional Requirements\n- \n\n## 3. Capacity Estimates\n- \n\n## 4. API Design\n- \n\n## 5. Database Schema\n- \n\n## 6. High-Level Architecture\n```mermaid\ngraph TD\n    Client --> API_Gateway\n    API_Gateway --> App_Service\n    App_Service --> Database[(Database)]\n```\n\n## 7. Trade-offs & Bottlenecks\n- "
        }
        
        for tech in TECHNOLOGIES:
            code_template = default_templates.get(tech, "")
            cursor.execute("""
                INSERT INTO practices (session_id, technology, title, code, status)
                VALUES (?, ?, ?, ?, 'NOT STARTED')
            """, (session_id, tech, f"{tech} Practice - {session_date_str}", code_template))
        
        conn.commit()
        cursor.execute("SELECT * FROM daily_sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        
    session_dict = dict(session)
    
    # Fetch practices for this session
    cursor.execute("SELECT * FROM practices WHERE session_id = ? ORDER BY id ASC", (session_dict["id"],))
    practices = [dict(p) for p in cursor.fetchall()]
    
    conn.close()
    session_dict["practices"] = practices
    return session_dict

def update_session_completion_status(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT status FROM practices WHERE session_id = ?", (session_id,))
    statuses = [r["status"] for r in cursor.fetchall()]
    
    completed_count = sum(1 for s in statuses if s == 'COMPLETED')
    
    if completed_count == 6:
        session_status = 'COMPLETED'
    elif completed_count > 0 or any(s in ['IN PROGRESS', 'SUCCESS', 'FAILED'] for s in statuses):
        session_status = 'IN PROGRESS'
    else:
        session_status = 'NOT STARTED'
        
    cursor.execute("""
        UPDATE daily_sessions 
        SET completed_count = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (completed_count, session_status, session_id))
    
    conn.commit()
    conn.close()
    return completed_count, session_status

def list_key_notes(search=None, category=None, date_str=None, technology=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM key_notes WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if date_str:
        query += " AND date_str = ?"
        params.append(date_str)

    if technology:
        query += " AND technology = ?"
        params.append(technology)

    if search:
        query += " AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])

    query += " ORDER BY is_pinned DESC, updated_at DESC, id DESC"
    cursor.execute(query, params)
    notes = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return notes

def get_key_note_by_id(note_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM key_notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_or_create_daily_note(date_str=None, tech=""):
    if not date_str:
        date_str = date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT * FROM key_notes
        WHERE category = 'Daily Practice' AND date_str = ?
    """, (date_str,)).fetchone()

    if not row:
        default_content = f"""# Daily Practice Notes - {date_str}

> [!NOTE]
> Key learnings, tips, formulas, and interview takeaways for {date_str}.

## 🎯 Today's Focus & Solved Problems
- 

## 💡 Key Tips & Techniques
- 

## ⚠️ Challenges & Bottlenecks
- 

## 📌 Code Snippets & Notes
```sql
-- Useful query pattern
```
"""
        cursor.execute("""
            INSERT INTO key_notes (title, category, date_str, technology, tags, content, is_pinned)
            VALUES (?, 'Daily Practice', ?, ?, 'daily, practice', ?, 0)
        """, (f"Daily Notes - {date_str}", date_str, tech, default_content))
        conn.commit()
        note_id = cursor.lastrowid
        row = cursor.execute("SELECT * FROM key_notes WHERE id = ?", (note_id,)).fetchone()

    note_dict = dict(row)
    conn.close()
    return note_dict

def save_key_note(note_data):
    note_id = note_data.get("id")
    title = (note_data.get("title") or "Untitled Note").strip()
    category = (note_data.get("category") or "Daily Practice").strip()
    date_str = (note_data.get("date_str") or date.today().isoformat()).strip()
    technology = (note_data.get("technology") or "").strip()
    tags = (note_data.get("tags") or "").strip()
    content = note_data.get("content", "")
    is_pinned = 1 if note_data.get("is_pinned") else 0

    conn = get_connection()
    cursor = conn.cursor()

    if note_id:
        cursor.execute("""
            UPDATE key_notes
            SET title = ?, category = ?, date_str = ?, technology = ?, tags = ?, content = ?, is_pinned = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title, category, date_str, technology, tags, content, is_pinned, note_id))
    else:
        cursor.execute("""
            INSERT INTO key_notes (title, category, date_str, technology, tags, content, is_pinned)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, category, date_str, technology, tags, content, is_pinned))
        note_id = cursor.lastrowid

    conn.commit()
    row = cursor.execute("SELECT * FROM key_notes WHERE id = ?", (note_id,)).fetchone()
    saved = dict(row) if row else None
    conn.close()
    return saved

def delete_key_note(note_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM key_notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return True

