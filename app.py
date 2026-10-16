import os
import sys
import socket
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

def find_preferred_port():
    # Check environment variable
    if os.environ.get("PORT"):
        try:
            return int(os.environ["PORT"])
        except ValueError:
            pass

    # Check CLI arguments e.g. python app.py --port 5000
    for i, arg in enumerate(sys.argv):
        if arg in ("--port", "-p") and i + 1 < len(sys.argv):
            try:
                return int(sys.argv[i + 1])
            except ValueError:
                pass

    # Attempt to bind port 80 so http://coding-practice-hub/ works without specifying a port number
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("0.0.0.0", 80))
        s.close()
        return 80
    except Exception:
        return 5000

if __name__ == "__main__":
    app = create_app()
    port = find_preferred_port()

    domain_display = "http://coding-practice-hub" if port == 80 else f"http://coding-practice-hub:{port}"
    localhost_display = "http://localhost" if port == 80 else f"http://localhost:{port}"

    print("=" * 65)
    print(" [Coding Practice Hub] Local Daily Coding Practice Application")
    print(f" * Localhost URL:     {localhost_display}/")
    print(f" * Custom Domain URL: {domain_display}/")
    print(" * Daily Target: 6 practices (SQL, Python, PySpark, Databricks, DSA, Design)")
    print("=" * 65)
    app.run(host="0.0.0.0", port=port, debug=False)
