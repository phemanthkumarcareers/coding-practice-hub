from flask import Blueprint, render_template, request, jsonify
from models.db import get_connection, TECHNOLOGIES, STATUSES
from datetime import datetime, date, timedelta

history_bp = Blueprint("history", __name__)

@history_bp.route("/history")
def history_view():
    conn = get_connection()
    
    # Fetch all sessions with practices
    sessions_rows = conn.execute("SELECT * FROM daily_sessions ORDER BY date DESC").fetchall()
    
    sessions_list = []
    for s in sessions_rows:
        s_dict = dict(s)
        p_rows = conn.execute("""
            SELECT id, technology, title, status, difficulty, topic, tags 
            FROM practices 
            WHERE session_id = ?
        """, (s["id"],)).fetchall()
        
        tech_map = {r["technology"]: dict(r) for r in p_rows}
        s_dict["tech_practices"] = tech_map
        sessions_list.append(s_dict)

    # Fetch unique topics and tags for filters
    topics = [r[0] for r in conn.execute("SELECT DISTINCT topic FROM practices WHERE topic != ''").fetchall()]
    all_tags_raw = conn.execute("SELECT tags FROM practices WHERE tags != ''").fetchall()
    tag_set = set()
    for row in all_tags_raw:
        for t in row[0].split(","):
            if t.strip():
                tag_set.add(t.strip())

    conn.close()

    return render_template(
        "history.html",
        sessions=sessions_list,
        technologies=TECHNOLOGIES,
        statuses=STATUSES,
        topics=topics,
        tags=sorted(list(tag_set))
    )

@history_bp.route("/history/tech/<tech_name>")
def tech_view(tech_name):
    # Validate tech
    matched_tech = None
    for t in TECHNOLOGIES:
        if t.lower().replace(" ", "") == tech_name.lower().replace(" ", ""):
            matched_tech = t
            break

    if not matched_tech:
        matched_tech = "SQL"

    conn = get_connection()
    practices = conn.execute("""
        SELECT p.*, s.date as session_date,
               (SELECT COUNT(*) FROM executions WHERE practice_id = p.id) as execution_count
        FROM practices p
        JOIN daily_sessions s ON p.session_id = s.id
        WHERE p.technology = ?
        ORDER BY s.date DESC
    """, (matched_tech,)).fetchall()

    conn.close()

    return render_template(
        "tech_view.html",
        tech_name=matched_tech,
        practices=[dict(p) for p in practices],
        technologies=TECHNOLOGIES
    )

@history_bp.route("/api/history/filter", methods=["POST"])
def filter_history():
    data = request.get_json() or {}
    techs = data.get("technologies", [])
    statuses = data.get("statuses", [])
    difficulties = data.get("difficulties", [])
    topics = data.get("topics", [])
    tags = data.get("tags", [])
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    group_by = data.get("group_by", "date")

    query = """
        SELECT p.*, s.date as session_date,
               (SELECT COUNT(*) FROM executions WHERE practice_id = p.id) as execution_count
        FROM practices p
        JOIN daily_sessions s ON p.session_id = s.id
        WHERE 1=1
    """
    params = []

    if techs:
        placeholders = ",".join(["?"] * len(techs))
        query += f" AND p.technology IN ({placeholders})"
        params.extend(techs)

    if statuses:
        placeholders = ",".join(["?"] * len(statuses))
        query += f" AND p.status IN ({placeholders})"
        params.extend(statuses)

    if difficulties:
        placeholders = ",".join(["?"] * len(difficulties))
        query += f" AND p.difficulty IN ({placeholders})"
        params.extend(difficulties)

    if topics:
        placeholders = ",".join(["?"] * len(topics))
        query += f" AND p.topic IN ({placeholders})"
        params.extend(topics)

    if start_date:
        query += " AND s.date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND s.date <= ?"
        params.append(end_date)

    query += " ORDER BY s.date DESC, p.id ASC"

    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = [dict(r) for r in rows]

    # Filter tags in python if specified
    if tags:
        tag_set = set(t.lower() for t in tags)
        filtered = []
        for r in results:
            p_tags = [t.strip().lower() for t in (r["tags"] or "").split(",") if t.strip()]
            if any(t in tag_set for t in p_tags):
                filtered.append(r)
        results = filtered

    # Handle grouping
    grouped_data = {}
    for item in results:
        key = "Other"
        if group_by == "date":
            key = item.get("session_date", "Unknown")
        elif group_by == "technology":
            key = item.get("technology", "Unknown")
        elif group_by == "status":
            key = item.get("status", "Unknown")
        elif group_by == "difficulty":
            key = item.get("difficulty", "Unknown")
        elif group_by == "topic":
            key = item.get("topic") or "Uncategorized"

        if key not in grouped_data:
            grouped_data[key] = []
        grouped_data[key].append(item)

    return jsonify({
        "success": True,
        "count": len(results),
        "group_by": group_by,
        "grouped": grouped_data,
        "items": results
    })
