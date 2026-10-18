import os
import sys
import shutil
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from models.db import get_all_settings, set_setting, get_setting
from config import (
    SQLITE_PATH,
    DUCKDB_PATH,
    UPLOADS_DIR,
    WORKSPACE_DIR,
    BACKUPS_DIR,
    DEFAULT_SETTINGS
)
from services.pyspark_service import pyspark_service
from services.backup_service import backup_service

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("/settings")
def settings_view():
    current_settings = get_all_settings()
    env_info = pyspark_service.check_environment()

    # Auto-populate java_home and spark_home if not yet set in database
    detected_java = env_info.get("detected_java_home") or env_info.get("java_home", "")
    detected_spark = env_info.get("detected_spark_home") or env_info.get("spark_home", "")

    if not current_settings.get("java_home") and detected_java:
        current_settings["java_home"] = detected_java
        set_setting("java_home", detected_java)

    if not current_settings.get("spark_home") and detected_spark:
        current_settings["spark_home"] = detected_spark
        set_setting("spark_home", detected_spark)

    env_info["detected_java_home"] = detected_java
    env_info["detected_spark_home"] = detected_spark
    env_info["detected_python"] = sys.executable
    env_info["python_version"] = sys.version.split()[0]
    env_info["sqlite_path"] = str(SQLITE_PATH)
    env_info["duckdb_path"] = str(DUCKDB_PATH)
    env_info["uploads_dir"] = str(UPLOADS_DIR)
    env_info["workspace_dir"] = str(WORKSPACE_DIR)

    # List existing backups
    backups = []
    if BACKUPS_DIR.exists():
        for b in sorted(BACKUPS_DIR.glob("*.zip"), key=os.path.getmtime, reverse=True):
            backups.append({
                "filename": b.name,
                "size_kb": round(b.stat().st_size / 1024, 1),
                "modified": os.path.getmtime(b)
            })

    return render_template(
        "settings.html",
        settings=current_settings,
        env_info=env_info,
        backups=backups
    )

@settings_bp.route("/api/settings/save", methods=["POST"])
def save_settings():
    data = request.get_json() or {}
    for key, val in data.items():
        set_setting(key, val)
    return jsonify({"success": True, "message": "Settings saved successfully"})

@settings_bp.route("/api/settings/detect_env")
def detect_env():
    env_info = pyspark_service.check_environment()
    env_info["detected_python"] = sys.executable
    env_info["python_version"] = sys.version.split()[0]
    return jsonify({"success": True, "env": env_info})

@settings_bp.route("/api/backup/list", methods=["GET"])
def list_backups_api():
    backups = []
    if BACKUPS_DIR.exists():
        for b in sorted(BACKUPS_DIR.glob("*.zip"), key=os.path.getmtime, reverse=True):
            backups.append({
                "filename": b.name,
                "size_kb": round(b.stat().st_size / 1024, 1),
                "modified": os.path.getmtime(b)
            })
    return jsonify({"success": True, "backups": backups})

@settings_bp.route("/api/backup/create", methods=["POST"])
def create_backup_api():
    try:
        backup_file = backup_service.create_backup()
        return jsonify({
            "success": True,
            "filename": backup_file.name,
            "download_url": f"/api/backup/download/{backup_file.name}",
            "message": "Backup created successfully!"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@settings_bp.route("/api/backup/download/<filename>")
def download_backup_api(filename):
    safe_name = secure_filename(filename)
    backup_file = BACKUPS_DIR / safe_name
    if not backup_file.exists():
        return "Backup not found", 404
    return send_file(str(backup_file), as_attachment=True, download_name=safe_name)

@settings_bp.route("/api/backup/restore", methods=["POST"])
def restore_backup_api():
    if "backup_file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["backup_file"]
    if not file.filename.endswith(".zip"):
        return jsonify({"success": False, "error": "Backup must be a .zip file"}), 400

    temp_path = BACKUPS_DIR / f"temp_upload_{secure_filename(file.filename)}"
    try:
        file.save(str(temp_path))
        res = backup_service.restore_backup(temp_path)
        if res.get("success"):
            return jsonify(res)
        else:
            return jsonify(res), 500
    finally:
        if temp_path.exists():
            temp_path.unlink()

@settings_bp.route("/api/backup/restore_existing/<filename>", methods=["POST"])
def restore_existing_backup_api(filename):
    safe_name = secure_filename(filename)
    backup_file = BACKUPS_DIR / safe_name
    if not backup_file.exists():
        return jsonify({"success": False, "error": f"Backup file '{filename}' not found."}), 404

    res = backup_service.restore_backup(backup_file)
    if res.get("success"):
        return jsonify(res)
    else:
        return jsonify(res), 500
