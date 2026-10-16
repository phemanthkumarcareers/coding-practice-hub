import os
import sys
from flask import Flask
from config import BASE_DIR
from models.db import init_db
from services.duckdb_service import duckdb_service

# Import blueprints
from routes.dashboard import dashboard_bp
from routes.practice import practice_bp
from routes.history import history_bp
from routes.datasets import datasets_bp
from routes.reports import reports_bp
from routes.settings import settings_bp

def create_app():
    # Detect & initialize database and required directories
    init_db()
    
    # Initialize DuckDB and sync dataset views
    duckdb_service.sync_dataset_views()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "coding-practice-hub-secret-key-2026"
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024 # 100MB max dataset upload

    # Register blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(practice_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(datasets_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print(" Coding Practice Hub - Local Daily Coding Practice")
    print(" Port: 5000 | URL: http://localhost:5000")
    print(" Daily target: 6 practices (SQL, Python, PySpark, Databricks, DSA, System Design)")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
