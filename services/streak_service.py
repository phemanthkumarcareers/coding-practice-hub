from datetime import datetime, date, timedelta
import sqlite3
from config import SQLITE_PATH, TECHNOLOGIES

class StreakService:
    def get_dashboard_metrics(self):
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        
        # 1. Overall Practice Counts
        p_rows = conn.execute("""
            SELECT status, COUNT(*) as cnt 
            FROM practices 
            GROUP BY status
        """).fetchall()
        
        status_counts = {
            "NOT STARTED": 0,
            "IN PROGRESS": 0,
            "RUNNING": 0,
            "SUCCESS": 0,
            "FAILED": 0,
            "COMPLETED": 0
        }
        for r in p_rows:
            if r["status"] in status_counts:
                status_counts[r["status"]] = r["cnt"]

        total_practices = sum(status_counts.values())
        
        # 2. Total Executions
        exec_stats = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                AVG(duration_ms) as avg_duration
            FROM executions
        """).fetchone()

        total_executions = exec_stats["total"] or 0
        success_executions = exec_stats["success"] or 0
        failed_executions = exec_stats["failed"] or 0
        avg_duration = round(exec_stats["avg_duration"] or 0, 1)

        # 3. Technology Statistics
        tech_rows = conn.execute("""
            SELECT 
                technology,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'IN PROGRESS' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'NOT STARTED' THEN 1 ELSE 0 END) as not_started
            FROM practices
            GROUP BY technology
        """).fetchall()

        tech_map = {t: {"total": 0, "completed": 0, "success": 0, "failed": 0, "in_progress": 0, "not_started": 0} for t in TECHNOLOGIES}
        for r in tech_rows:
            t = r["technology"]
            if t in tech_map:
                tech_map[t] = {
                    "total": r["total"],
                    "completed": r["completed"],
                    "success": r["success"],
                    "failed": r["failed"],
                    "in_progress": r["in_progress"],
                    "not_started": r["not_started"]
                }

        # 4. Streaks & Daily Completion
        # Query distinct daily sessions ordered by date
        sessions = conn.execute("SELECT date, completed_count, status FROM daily_sessions ORDER BY date ASC").fetchall()
        
        session_dates = {s["date"]: s for s in sessions}
        completed_6_dates = {s["date"] for s in sessions if s["completed_count"] == 6}

        # Calculate streaks
        current_streak = 0
        longest_streak = 0
        temp_streak = 0

        # Sort dates for continuous streak computation
        sorted_dates = sorted(list(session_dates.keys()))
        if sorted_dates:
            start_d = datetime.strptime(sorted_dates[0], "%Y-%m-%d").date()
            end_d = date.today()
            
            # Count longest streak of 6/6 days
            curr = start_d
            while curr <= end_d:
                d_str = curr.isoformat()
                if d_str in completed_6_dates:
                    temp_streak += 1
                    if temp_streak > longest_streak:
                        longest_streak = temp_streak
                else:
                    temp_streak = 0
                curr += timedelta(days=1)

            # Count current streak backwards from today (or yesterday if today isn't done yet)
            check_date = date.today()
            if check_date.isoformat() not in completed_6_dates:
                # If today is not 6/6, check if yesterday was part of a streak
                check_date = date.today() - timedelta(days=1)
                
            while check_date.isoformat() in completed_6_dates:
                current_streak += 1
                check_date -= timedelta(days=1)

        # Today's Progress
        today_str = date.today().isoformat()
        today_session = session_dates.get(today_str)
        today_progress = {
            "exists": today_session is not None,
            "completed_count": today_session["completed_count"] if today_session else 0,
            "status": today_session["status"] if today_session else "NOT STARTED",
            "tech_items": {}
        }
        
        if today_session:
            today_p_rows = conn.execute("""
                SELECT technology, status, title, difficulty 
                FROM practices 
                WHERE session_id = (SELECT id FROM daily_sessions WHERE date = ?)
            """, (today_str,)).fetchall()
            for r in today_p_rows:
                today_progress["tech_items"][r["technology"]] = {
                    "status": r["status"],
                    "title": r["title"],
                    "difficulty": r["difficulty"]
                }
        else:
            for t in TECHNOLOGIES:
                today_progress["tech_items"][t] = {
                    "status": "NOT STARTED",
                    "title": "",
                    "difficulty": "Medium"
                }

        # Partial / Missed / Completed 6/6 counts
        days_completed_6 = len(completed_6_dates)
        partial_days = sum(1 for s in sessions if 0 < s["completed_count"] < 6)
        
        conn.close()

        return {
            "total_practices": total_practices,
            "status_counts": status_counts,
            "successful_practices": status_counts["SUCCESS"] + status_counts["COMPLETED"],
            "failed_practices": status_counts["FAILED"],
            "in_progress_practices": status_counts["IN PROGRESS"] + status_counts["RUNNING"],
            "not_started_practices": status_counts["NOT STARTED"],
            "total_executions": total_executions,
            "success_executions": success_executions,
            "failed_executions": failed_executions,
            "avg_execution_duration": avg_duration,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "days_completed_6": days_completed_6,
            "partial_days": partial_days,
            "technology_stats": tech_map,
            "today_progress": today_progress
        }

streak_service = StreakService()
