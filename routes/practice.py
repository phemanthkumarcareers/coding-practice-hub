import json
from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from models.db import (
    get_connection,
    get_or_create_daily_session,
    update_session_completion_status,
    TECHNOLOGIES,
    STATUSES
)
from services.duckdb_service import duckdb_service
from services.code_executor import code_executor
from services.pyspark_service import pyspark_service

practice_bp = Blueprint("practice", __name__)

@practice_bp.route("/practice")
def practice_workspace():
    date_arg = request.args.get("date")
    practice_id_arg = request.args.get("practice_id")
    target_tech = request.args.get("tech")

    conn = get_connection()
    session = None
    initial_practice_id = None

    if practice_id_arg:
        p_row = conn.execute("SELECT * FROM practices WHERE id = ?", (practice_id_arg,)).fetchone()
        if p_row:
            s_row = conn.execute("SELECT * FROM daily_sessions WHERE id = ?", (p_row["session_id"],)).fetchone()
            if s_row:
                session_dict = dict(s_row)
                p_rows = conn.execute("SELECT * FROM practices WHERE session_id = ? ORDER BY id ASC", (session_dict["id"],)).fetchall()
                session_dict["practices"] = [dict(p) for p in p_rows]
                session = session_dict
                initial_practice_id = int(practice_id_arg)
                target_tech = p_row["technology"]

    if not session:
        session_date = date_arg if date_arg else date.today().isoformat()
        session = get_or_create_daily_session(session_date)

    conn.close()

    if not target_tech:
        target_tech = "SQL"

    # Get databases for SQL selector
    databases = duckdb_service.list_databases()

    return render_template(
        "practice.html",
        session=session,
        technologies=TECHNOLOGIES,
        statuses=STATUSES,
        selected_tech=target_tech,
        initial_practice_id=initial_practice_id,
        databases=databases
    )

@practice_bp.route("/api/practice/databases")
def get_databases():
    return jsonify({
        "success": True,
        "databases": duckdb_service.list_databases()
    })

@practice_bp.route("/api/practice/database/create", methods=["POST"])
@practice_bp.route("/api/practice/create_database", methods=["POST"])
def create_database():
    data = request.get_json() or {}
    db_name = data.get("name", "")
    res = duckdb_service.create_database(db_name)
    if res.get("success"):
        res["databases"] = duckdb_service.list_databases()
        res["schemas"] = duckdb_service.get_explorer_schema()
        return jsonify(res)
    return jsonify(res), 400

@practice_bp.route("/api/practice/save", methods=["POST"])
def save_practice():
    data = request.get_json() or {}
    practice_id = data.get("id")
    if not practice_id:
        return jsonify({"success": False, "error": "Practice ID required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    title = data.get("title", "")
    difficulty = data.get("difficulty", "Medium")
    topic = data.get("topic", "")
    tags = data.get("tags", "")
    question = data.get("question", "")
    code = data.get("code", "")
    notes = data.get("notes", "")
    status = data.get("status", "IN PROGRESS")
    extra_metadata = json.dumps(data.get("extra_metadata", {}))

    completed_at = datetime.now().isoformat() if status == "COMPLETED" else None

    cursor.execute("""
        UPDATE practices
        SET title = ?,
            difficulty = ?,
            topic = ?,
            tags = ?,
            question = ?,
            code = ?,
            notes = ?,
            status = ?,
            extra_metadata = ?,
            updated_at = CURRENT_TIMESTAMP,
            completed_at = COALESCE(?, completed_at)
        WHERE id = ?
    """, (title, difficulty, topic, tags, question, code, notes, status, extra_metadata, completed_at, practice_id))

    cursor.execute("SELECT session_id, technology FROM practices WHERE id = ?", (practice_id,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()

    if row:
        session_id = row["session_id"]
        completed_count, session_status = update_session_completion_status(session_id)
        return jsonify({
            "success": True,
            "message": "Practice saved successfully",
            "session_id": session_id,
            "completed_count": completed_count,
            "session_status": session_status
        })

    return jsonify({"success": True, "message": "Saved"})

@practice_bp.route("/api/practice/run", methods=["POST"])
def run_practice():
    data = request.get_json() or {}
    practice_id = data.get("id")
    code = data.get("code", "")
    technology = data.get("technology", "Python")
    active_db = data.get("active_db", "main")
    files = data.get("files")  # Multi-file support: {"main.py": "...", "utils.py": "..."}
    entry_file = data.get("entry_file", "main.py")

    if not practice_id:
        return jsonify({"success": False, "error": "Practice ID required"}), 400

    output_text = ""
    error_text = ""
    run_status = "SUCCESS"
    duration_ms = 0
    structured_result = None
    updated_schemas = None

    full_code = data.get("code", "")
    if files and isinstance(files, dict) and entry_file in files:
        full_code = files[entry_file]

    selected_code = data.get("selected_code")
    if selected_code and selected_code.strip():
        code_to_run = selected_code.strip()
    else:
        code_to_run = full_code

    if technology == "SQL":
        duckdb_service.sync_dataset_views()
        res = duckdb_service.execute_query(code_to_run, active_db=active_db)
        run_status = res["status"]
        duration_ms = res["duration_ms"]
        structured_result = res
        if res["error"]:
            error_text = res["error"]
            output_text = ""
        else:
            output_text = f"Executed in {duration_ms} ms. Rows returned: {res['row_count']}"
        
        # Refresh schemas so newly created tables/views show up immediately
        updated_schemas = duckdb_service.get_explorer_schema()

    elif technology in ("Python", "DSA"):
        if selected_code and selected_code.strip():
            res = code_executor.execute_python(code_to_run, tech=technology)
        elif files and isinstance(files, dict) and len(files) > 0:
            res = code_executor.execute_python_project(files, entry_file=entry_file, tech=technology)
        else:
            res = code_executor.execute_python(code_to_run, tech=technology)
        run_status = res["status"]
        duration_ms = res["duration_ms"]
        output_text = res["stdout"]
        error_text = res["stderr"]

    elif technology == "PySpark":
        res = pyspark_service.execute_pyspark(code_to_run)
        run_status = res["status"]
        duration_ms = res["duration_ms"]
        output_text = res["stdout"]
        error_text = res["stderr"]

    elif technology == "Databricks":
        subtype = data.get("extra_metadata", {}).get("subtype", "Python")
        if subtype == "SQL":
            duckdb_service.sync_dataset_views()
            res = duckdb_service.execute_query(code_to_run, active_db=active_db)
            run_status = res["status"]
            duration_ms = res["duration_ms"]
            structured_result = res
            error_text = res.get("error", "")
            output_text = f"Databricks SQL simulated on DuckDB. Rows: {res['row_count']}"
            updated_schemas = duckdb_service.get_explorer_schema()
        elif subtype in ["PySpark", "Structured Streaming", "Delta Lake"]:
            res = pyspark_service.execute_pyspark(code_to_run)
            run_status = res["status"]
            duration_ms = res["duration_ms"]
            output_text = res["stdout"]
            error_text = res["stderr"]
        else:
            if selected_code and selected_code.strip():
                res = code_executor.execute_python(code_to_run, tech="databricks")
            elif files and isinstance(files, dict) and len(files) > 0:
                res = code_executor.execute_python_project(files, entry_file=entry_file, tech="databricks")
            else:
                res = code_executor.execute_python(code_to_run, tech="databricks")
            run_status = res["status"]
            duration_ms = res["duration_ms"]
            output_text = res["stdout"]
            error_text = res["stderr"]

    else:
        output_text = "System Design workspace updated."
        run_status = "SUCCESS"

    # Persist execution snapshot in database
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO executions (practice_id, code_snapshot, output, error_output, status, duration_ms)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (practice_id, code_to_run, output_text, error_text, run_status, duration_ms))

    cursor.execute("SELECT status FROM practices WHERE id = ?", (practice_id,))
    cur_p = cursor.fetchone()
    new_status = cur_p["status"]
    if cur_p["status"] != "COMPLETED":
        new_status = run_status

    cursor.execute("""
        UPDATE practices
        SET code = ?,
            latest_output = ?,
            latest_error = ?,
            duration_ms = ?,
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (full_code, output_text, error_text, duration_ms, new_status, practice_id))

    cursor.execute("SELECT session_id FROM practices WHERE id = ?", (practice_id,))
    s_row = cursor.fetchone()
    conn.commit()
    conn.close()

    if s_row:
        update_session_completion_status(s_row["session_id"])

    return jsonify({
        "success": True,
        "status": run_status,
        "duration_ms": duration_ms,
        "output": output_text,
        "error": error_text,
        "structured_result": structured_result,
        "practice_status": new_status,
        "updated_schemas": updated_schemas
    })

@practice_bp.route("/api/practice/executions/<int:practice_id>")
def get_executions(practice_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, practice_id, code_snapshot, output, error_output, status, duration_ms, created_at
        FROM executions
        WHERE practice_id = ?
        ORDER BY id DESC
    """, (practice_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# Starter Templates Catalog
STARTER_TEMPLATES = {
    "SQL": [
        {
            "name": "01_select_filter_joins.sql",
            "description": "SELECT, INNER/LEFT JOIN & WHERE filtering",
            "content": "-- Basic SELECT, JOIN & WHERE Filter Template\nSELECT \n    e.id, \n    e.name, \n    d.department_name, \n    e.salary\nFROM employees e\nLEFT JOIN departments d ON e.dept_id = d.id\nWHERE e.salary > 50000\nORDER BY e.salary DESC;\n"
        },
        {
            "name": "02_window_functions_rank_lead_lag.sql",
            "description": "ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD",
            "content": "-- Window Functions: ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD\nSELECT \n    department, \n    employee_name, \n    salary,\n    ROW_NUMBER() OVER(PARTITION BY department ORDER BY salary DESC) as row_num,\n    DENSE_RANK() OVER(PARTITION BY department ORDER BY salary DESC) as dense_rank_val,\n    LAG(salary, 1, 0) OVER(PARTITION BY department ORDER BY salary) as prev_salary,\n    LEAD(salary, 1, 0) OVER(PARTITION BY department ORDER BY salary) as next_salary\nFROM salaries;\n"
        },
        {
            "name": "03_cte_and_aggregations.sql",
            "description": "Common Table Expressions (CTE) & Aggregations",
            "content": "-- Common Table Expressions (CTE) & Aggregations\nWITH monthly_revenue AS (\n    SELECT \n        strftime(order_date, '%Y-%m') as order_month,\n        SUM(order_amount) as total_revenue,\n        COUNT(DISTINCT customer_id) as active_customers\n    FROM orders\n    GROUP BY 1\n)\nSELECT \n    order_month,\n    total_revenue,\n    active_customers,\n    ROUND(total_revenue / NULLIF(active_customers, 0), 2) as avg_revenue_per_user\nFROM monthly_revenue\nORDER BY order_month DESC;\n"
        },
        {
            "name": "04_duckdb_direct_file_queries.sql",
            "description": "Query CSV / Parquet datasets directly without loading",
            "content": "-- DuckDB Direct File Queries\n-- Query any uploaded CSV/Parquet dataset directly:\nSELECT * FROM read_csv_auto('sample_data.csv') LIMIT 15;\n-- Or Parquet files:\n-- SELECT * FROM read_parquet('transactions.parquet') WHERE amount > 1000;\n"
        }
    ],
    "Python": [
        {
            "name": "01_main_template.py",
            "description": "Standard Python execution entry point",
            "content": "# Python Entry Point\nimport sys\nimport json\nfrom datetime import datetime\n\ndef main():\n    print(\"Python Execution Workspace Started.\")\n    data = {\"timestamp\": datetime.now().isoformat(), \"version\": sys.version}\n    print(json.dumps(data, indent=2))\n\nif __name__ == '__main__':\n    main()\n"
        },
        {
            "name": "02_data_processing_pandas.py",
            "description": "Pandas Dataframe & Groupby Aggregations",
            "content": "# Data Processing with Pandas\nimport pandas as pd\n\ndata = {\n    'id': [101, 102, 103, 104],\n    'category': ['Electronics', 'Clothing', 'Electronics', 'Home'],\n    'price': [299.99, 49.50, 899.00, 120.00],\n    'units_sold': [15, 80, 5, 22]\n}\n\ndf = pd.DataFrame(data)\ndf['revenue'] = df['price'] * df['units_sold']\nsummary = df.groupby('category').agg({'revenue': 'sum', 'units_sold': 'sum'})\nprint(summary)\n"
        }
    ],
    "PySpark": [
        {
            "name": "01_pyspark_starter.py",
            "description": "PySpark SparkSession & DataFrame Operations",
            "content": "from pyspark.sql import SparkSession\nfrom pyspark.sql.functions import col, avg, count\n\nspark = SparkSession.builder \\\n    .appName(\"DailyPySparkPractice\") \\\n    .master(\"local[*]\") \\\n    .getOrCreate()\n\ndata = [(1, \"Alice\", \"Engineering\", 95000), (2, \"Bob\", \"Engineering\", 105000), (3, \"Charlie\", \"Marketing\", 70000)]\ncolumns = [\"id\", \"name\", \"dept\", \"salary\"]\n\ndf = spark.createDataFrame(data, schema=columns)\ndf.show()\n\ndf.groupBy(\"dept\").agg(avg(\"salary\").alias(\"avg_salary\"), count(\"*\").alias(\"total_heads\")).show()\nspark.stop()\n"
        }
    ],
    "Databricks": [
        {
            "name": "01_databricks_starter.py",
            "description": "Databricks Notebook & Delta Lake simulation",
            "content": "# Databricks Local Simulation Workspace\nprint(\"Databricks Notebook Initialized.\")\n# Supports PySpark, Delta Lake patterns, and SQL simulations\n"
        }
    ],
    "DSA": [
        {
            "name": "01_dsa_template.py",
            "description": "Standard DSA algorithm template with test cases",
            "content": "class Solution:\n    def solve(self, nums: list[int], target: int) -> list[int]:\n        seen = {}\n        for i, val in enumerate(nums):\n            comp = target - val\n            if comp in seen:\n                return [seen[comp], i]\n            seen[val] = i\n        return []\n\nif __name__ == '__main__':\n    s = Solution()\n    res = s.solve([2, 7, 11, 15], 9)\n    print(f\"Result: {res} | Expected: [0, 1]\")\n"
        }
    ],
    "System Design": [
        {
            "name": "01_microservices_architecture.md",
            "description": "Architecture notes with live Mermaid flowchart",
            "content": "# System Architecture\n\n## 1. Requirements\n- High availability (99.99%)\n- Sub-50ms read latency\n\n## 2. Architecture Diagram\n```mermaid\nflowchart LR\n    Client[Client App] --> API[API Gateway]\n    API --> Cache[(Redis Cache)]\n    API --> Service[Core Microservice]\n    Service --> DB[(Primary Database)]\n```\n"
        }
    ]
}

@practice_bp.route("/api/practice/files/tree")
def get_files_tree():
    tech = request.args.get("tech", "SQL")
    practice_id = request.args.get("practice_id", type=int)

    conn = get_connection()

    # Fetch past practices for this tech across daily sessions
    rows = conn.execute("""
        SELECT p.id, p.title, p.code, p.extra_metadata, p.updated_at, s.date as session_date
        FROM practices p
        JOIN daily_sessions s ON p.session_id = s.id
        WHERE p.technology = ?
        ORDER BY s.date DESC, p.id DESC
        LIMIT 30
    """, (tech,)).fetchall()

    past_sessions = []
    current_files_map = {}

    for r in rows:
        p_dict = dict(r)
        extra = {}
        try:
            extra = json.loads(p_dict["extra_metadata"] or "{}")
        except Exception:
            extra = {}

        p_files = extra.get("files", {})
        if not p_files and p_dict["code"]:
            default_fname = "query.sql" if tech == "SQL" else ("architecture.md" if tech == "System Design" else "main.py")
            p_files = { default_fname: p_dict["code"] }

        files_list = []
        for fname, content in p_files.items():
            files_list.append({
                "name": fname,
                "size": len(content or ""),
                "snippet": (content or "")[:120]
            })

        if practice_id and p_dict["id"] == practice_id:
            current_files_map = p_files
        else:
            if files_list:
                past_sessions.append({
                    "practice_id": p_dict["id"],
                    "date": p_dict["session_date"],
                    "title": p_dict["title"] or f"{tech} Practice",
                    "files": files_list
                })

    conn.close()

    starters = STARTER_TEMPLATES.get(tech, STARTER_TEMPLATES.get("SQL", []))

    return jsonify({
        "success": True,
        "tech": tech,
        "past_sessions": past_sessions,
        "starter_templates": starters
    })

@practice_bp.route("/api/practice/files/get_content", methods=["POST"])
def get_file_content():
    data = request.get_json() or {}
    source_practice_id = data.get("source_practice_id")
    file_name = data.get("file_name", "")
    template_name = data.get("template_name")
    tech = data.get("tech", "SQL")

    if template_name:
        starters = STARTER_TEMPLATES.get(tech, [])
        for t in starters:
            if t["name"] == template_name:
                return jsonify({
                    "success": True,
                    "file_name": t["name"],
                    "content": t["content"]
                })
        return jsonify({"success": False, "error": "Template not found"}), 404

    if source_practice_id:
        conn = get_connection()
        row = conn.execute("SELECT code, extra_metadata FROM practices WHERE id = ?", (source_practice_id,)).fetchone()
        conn.close()
        if not row:
            return jsonify({"success": False, "error": "Practice not found"}), 404

        extra = {}
        try:
            extra = json.loads(row["extra_metadata"] or "{}")
        except Exception:
            extra = {}

        files = extra.get("files", {})
        if file_name in files:
            return jsonify({
                "success": True,
                "file_name": file_name,
                "content": files[file_name]
            })
        elif row["code"]:
            return jsonify({
                "success": True,
                "file_name": file_name or "main.py",
                "content": row["code"]
            })

    return jsonify({"success": False, "error": "File not found"}), 404

@practice_bp.route("/api/practice/files/delete", methods=["POST"])
def delete_practice_file():
    data = request.get_json() or {}
    practice_id = data.get("practice_id")
    filename = data.get("filename")

    if not practice_id or not filename:
        return jsonify({"success": False, "error": "Missing practice_id or filename"}), 400

    conn = get_connection()
    row = conn.execute("SELECT id, extra_metadata FROM practices WHERE id = ?", (practice_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "Practice not found"}), 404

    extra = {}
    try:
        extra = json.loads(row["extra_metadata"] or "{}")
    except Exception:
        extra = {}

    files = extra.get("files", {})
    if filename in files:
        del files[filename]

    open_tabs = extra.get("open_tabs", [])
    if filename in open_tabs:
        open_tabs = [f for f in open_tabs if f != filename]

    if extra.get("active_file") == filename:
        extra["active_file"] = open_tabs[-1] if open_tabs else None

    extra["files"] = files
    extra["open_tabs"] = open_tabs

    if extra.get("active_file") and extra["active_file"] in files:
        new_code = files[extra["active_file"]]
        conn.execute("UPDATE practices SET code = ?, extra_metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_code, json.dumps(extra), practice_id))
    elif files:
        first_file = next(iter(files.values()))
        conn.execute("UPDATE practices SET code = ?, extra_metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (first_file, json.dumps(extra), practice_id))
    else:
        conn.execute("UPDATE practices SET code = '', extra_metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (json.dumps(extra), practice_id))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "deleted": filename, "remaining_files": list(files.keys())})

