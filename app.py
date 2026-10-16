import os
import sys
import threading
from flask import Flask
from werkzeug.serving import run_simple
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

def serve_on_port(application, port):
    try:
        run_simple("0.0.0.0", port, application, threaded=True)
    except Exception as e:
        print(f" * Notice: Port {port} could not be bound ({e})")

if __name__ == "__main__":
    app = create_app()

    print("=" * 65)
    print(" [Coding Practice Hub] Local Daily Coding Practice Application")
    print(" Active Access URLs:")
    print("  -> http://localhost:5000/")
    print("  -> http://localhost/")
    print("  -> http://127.0.0.1:5000/")
    print("  -> http://coding-practice-hub/ (requires hosts entry)")
    print(" Daily Target: 6 practices (SQL, Python, PySpark, Databricks, DSA, Design)")
    print("=" * 65)

    # Start Port 80 in a background daemon thread
    t80 = threading.Thread(target=serve_on_port, args=(app, 80), daemon=True)
    t80.start()

    # Serve Port 5000 on main thread
    serve_on_port(app, 5000)
