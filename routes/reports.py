from flask import Blueprint, render_template, request, jsonify
from models.db import get_connection, TECHNOLOGIES
from services.streak_service import streak_service
from datetime import datetime, date, timedelta

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/reports")
def reports_view():
    metrics = streak_service.get_dashboard_metrics()
    conn = get_connection()

    # Calculate overall completion rate & success rate
    total_p = metrics["total_practices"]
    comp_p = metrics["status_counts"]["COMPLETED"]
    succ_p = metrics["status_counts"]["SUCCESS"] + comp_p
    completion_rate = round((comp_p / total_p * 100) if total_p > 0 else 0, 1)
    success_rate = round((succ_p / total_p * 100) if total_p > 0 else 0, 1)

    # By-technology completion % & success %
    tech_stats = metrics["technology_stats"]
    for t, data in tech_stats.items():
        t_total = data["total"]
        data["completion_pct"] = round((data["completed"] / t_total * 100) if t_total > 0 else 0, 1)
        data["success_pct"] = round(((data["success"] + data["completed"]) / t_total * 100) if t_total > 0 else 0, 1)

    # Difficulty breakdown
    diff_rows = conn.execute("""
        SELECT difficulty, COUNT(*) as cnt
        FROM practices
        GROUP BY difficulty
    """).fetchall()
    difficulty_breakdown = {r["difficulty"]: r["cnt"] for r in diff_rows}

    # Trend: Practices per day for the last 14 days
    today = date.today()
    trend_days = []
    trend_counts = []
    for i in range(13, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        trend_days.append(d)
        cnt = conn.execute("""
            SELECT COUNT(*) FROM practices p
            JOIN daily_sessions s ON p.session_id = s.id
            WHERE s.date = ? AND p.status IN ('COMPLETED', 'SUCCESS', 'IN PROGRESS')
        """, (d,)).fetchone()[0]
        trend_counts.append(cnt)

    # Average attempts before success
    # Find practices that have at least one success execution
    attempts_row = conn.execute("""
        SELECT AVG(attempts) as avg_att
        FROM (
            SELECT practice_id, COUNT(*) as attempts
            FROM executions
            GROUP BY practice_id
            HAVING SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) > 0
        )
    """).fetchone()
    avg_attempts_before_success = round(attempts_row["avg_att"] or 1.0, 1)

    conn.close()

    return render_template(
        "reports.html",
        metrics=metrics,
        completion_rate=completion_rate,
        success_rate=success_rate,
        tech_stats=tech_stats,
        difficulty_breakdown=difficulty_breakdown,
        trend_days=trend_days,
        trend_counts=trend_counts,
        avg_attempts_before_success=avg_attempts_before_success
    )

@reports_bp.route("/api/search")
def global_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})

    conn = get_connection()
    like_q = f"%{q}%"

    results = conn.execute("""
        SELECT 
            p.id, 
            p.technology, 
            p.title, 
            p.status, 
            p.difficulty, 
            p.topic, 
            p.tags,
            p.question,
            p.notes,
            s.date as session_date
        FROM practices p
        JOIN daily_sessions s ON p.session_id = s.id
        WHERE p.title LIKE ? 
           OR p.question LIKE ? 
           OR p.code LIKE ? 
           OR p.notes LIKE ? 
           OR p.tags LIKE ? 
           OR p.topic LIKE ?
           OR p.technology LIKE ?
        ORDER BY s.date DESC
        LIMIT 50
    """, (like_q, like_q, like_q, like_q, like_q, like_q, like_q)).fetchall()

    conn.close()
    return jsonify({"results": [dict(r) for r in results]})
