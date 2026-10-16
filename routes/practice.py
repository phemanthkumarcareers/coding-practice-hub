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
        # Load session for this practice
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

    # Pre-select initial tech tab
    if not target_tech:
        target_tech = "SQL"

    return render_template(
        "practice.html",
        session=session,
        technologies=TECHNOLOGIES,
        statuses=STATUSES,
        selected_tech=target_tech,
        initial_practice_id=initial_practice_id
    )

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

    # Retrieve session_id
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

    if not practice_id:
        return jsonify({"success": False, "error": "Practice ID required"}), 400

    output_text = ""
    error_text = ""
    run_status = "SUCCESS"
    duration_ms = 0
    structured_result = None

    if technology == "SQL":
        # Make sure dataset views are up to date
        duckdb_service.sync_dataset_views()
        res = duckdb_service.execute_query(code)
        run_status = res["status"]
        duration_ms = res["duration_ms"]
        structured_result = res
        if res["error"]:
            error_text = res["error"]
            output_text = ""
        else:
            # Build pretty ASCII table summary for text logs
            output_text = f"Executed in {duration_ms} ms. Rows returned: {res['row_count']}"

    elif technology == "Python" or technology == "DSA":
        res = code_executor.execute_python(code, tech=technology)
        run_status = res["status"]
        duration_ms = res["duration_ms"]
        output_text = res["stdout"]
        error_text = res["stderr"]

    elif technology == "PySpark":
        res = pyspark_service.execute_pyspark(code)
        run_status = res["status"]
        duration_ms = res["duration_ms"]
        output_text = res["stdout"]
        error_text = res["stderr"]

    elif technology == "Databricks":
        subtype = data.get("extra_metadata", {}).get("subtype", "Python")
        if subtype == "SQL":
            duckdb_service.sync_dataset_views()
            res = duckdb_service.execute_query(code)
            run_status = res["status"]
            duration_ms = res["duration_ms"]
            structured_result = res
            error_text = res.get("error", "")
            output_text = f"Databricks SQL simulated on DuckDB. Rows: {res['row_count']}"
        elif subtype in ["PySpark", "Structured Streaming", "Delta Lake"]:
            res = pyspark_service.execute_pyspark(code)
            run_status = res["status"]
            duration_ms = res["duration_ms"]
            output_text = res["stdout"]
            error_text = res["stderr"]
        else:
            res = code_executor.execute_python(code, tech="databricks")
            run_status = res["status"]
            duration_ms = res["duration_ms"]
            output_text = res["stdout"]
            error_text = res["stderr"]

    else:
        # System Design doesn't execute code
        output_text = "System Design workspace updated."
        run_status = "SUCCESS"

    # Persist execution snapshot in database
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO executions (practice_id, code_snapshot, output, error_output, status, duration_ms)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (practice_id, code, output_text, error_text, run_status, duration_ms))

    # Update practice latest execution details
    # Do not downgrade COMPLETED to SUCCESS/FAILED if already completed, unless user changes it
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
    """, (code, output_text, error_text, duration_ms, new_status, practice_id))

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
        "practice_status": new_status
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
