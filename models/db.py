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

    CREATE INDEX IF NOT EXISTS idx_practices_session ON practices(session_id);
    CREATE INDEX IF NOT EXISTS idx_practices_tech ON practices(technology);
    CREATE INDEX IF NOT EXISTS idx_practices_status ON practices(status);
    CREATE INDEX IF NOT EXISTS idx_executions_practice ON executions(practice_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_date ON daily_sessions(date);
    """)

    # Populate default settings if not exists
    for key, val in DEFAULT_SETTINGS.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

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
