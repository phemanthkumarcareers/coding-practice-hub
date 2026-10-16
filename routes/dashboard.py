from flask import Blueprint, render_template, jsonify, request
from services.streak_service import streak_service
from models.db import get_connection, get_or_create_daily_session
from datetime import date
from config import TECHNOLOGIES

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def index():
    metrics = streak_service.get_dashboard_metrics()
    today_str = date.today().isoformat()
    return render_template(
        "dashboard.html",
        metrics=metrics,
        today=today_str,
        technologies=TECHNOLOGIES
    )

@dashboard_bp.route("/api/dashboard/metrics")
def get_metrics():
    metrics = streak_service.get_dashboard_metrics()
    return jsonify(metrics)
