import os
import re
import json
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
from models.db import get_connection
from config import CSV_UPLOADS, JSON_UPLOADS, PARQUET_UPLOADS, UPLOADS_DIR
from services.duckdb_service import duckdb_service

datasets_bp = Blueprint("datasets", __name__)

ALLOWED_EXTENSIONS = {"csv", "json", "parquet"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_table_name(filename):
    base = filename.rsplit(".", 1)[0]
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", base).lower()
    if cleaned and cleaned[0].isdigit():
        cleaned = "t_" + cleaned
    return cleaned or "dataset_table"

@datasets_bp.route("/datasets")
def datasets_view():
    conn = get_connection()
    datasets = conn.execute("SELECT * FROM datasets ORDER BY uploaded_at DESC").fetchall()
    conn.close()
    
    schema_explorer = duckdb_service.get_explorer_schema()

    return render_template(
        "datasets.html",
        datasets=[dict(d) for d in datasets],
        schema_explorer=schema_explorer
    )

@datasets_bp.route("/api/datasets/upload", methods=["POST"])
def upload_dataset():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "File type not supported. Use CSV, JSON, or Parquet."}), 400

    original_name = file.filename
    ext = original_name.rsplit(".", 1)[1].lower()
    
    # Save destination
    if ext == "csv":
        dest_dir = CSV_UPLOADS
    elif ext == "json":
        dest_dir = JSON_UPLOADS
    else:
        dest_dir = PARQUET_UPLOADS

    safe_name = secure_filename(original_name)
    file_path = dest_dir / safe_name
    
    # Handle filename collision
    idx = 1
    base_stem = file_path.stem
    while file_path.exists():
        safe_name = f"{base_stem}_{idx}.{ext}"
        file_path = dest_dir / safe_name
        idx += 1

    file.save(str(file_path))
    file_size = os.path.getsize(str(file_path))

    # Inspect schema and row count using DuckDB
    table_name = sanitize_table_name(safe_name)
    row_count = 0
    column_count = 0
    columns = []

    try:
        conn_duck = duckdb_service.get_connection()
        posix_path = file_path.as_posix()
        if ext == "csv":
            read_sql = f"read_csv_auto('{posix_path}')"
        elif ext == "parquet":
            read_sql = f"read_parquet('{posix_path}')"
        else:
            read_sql = f"read_json_auto('{posix_path}')"

        row_count = conn_duck.execute(f"SELECT count(*) FROM {read_sql}").fetchone()[0]
        col_info = conn_duck.execute(f"DESCRIBE SELECT * FROM {read_sql}").fetchall()
        column_count = len(col_info)
        columns = [{"name": c[0], "type": c[1]} for c in col_info]
        
        # Create view in DuckDB
        conn_duck.execute(f"CREATE OR REPLACE VIEW \"{table_name}\" AS SELECT * FROM {read_sql};")
        conn_duck.close()
    except Exception as e:
        print(f"Error inspecting dataset: {e}")

    # Insert into SQLite
    conn = get_connection()
    cursor = conn.cursor()
    # Check if table_name is unique
    existing = cursor.execute("SELECT id FROM datasets WHERE table_name = ?", (table_name,)).fetchone()
    if existing:
        table_name = f"{table_name}_{int(os.path.getmtime(str(file_path)))}"

    cursor.execute("""
        INSERT INTO datasets (file_name, original_name, file_type, file_size, file_path, table_name, row_count, column_count, columns_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (safe_name, original_name, ext, file_size, str(file_path), table_name, row_count, column_count, json.dumps(columns)))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "success": True,
        "id": new_id,
        "table_name": table_name,
        "row_count": row_count,
        "column_count": column_count,
        "message": f"Successfully uploaded {original_name}"
    })

@datasets_bp.route("/api/datasets/preview/<int:dataset_id>")
def preview_dataset(dataset_id):
    conn = get_connection()
    dataset = conn.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
    conn.close()

    if not dataset:
        return jsonify({"success": False, "error": "Dataset not found"}), 404

    d_dict = dict(dataset)
    tbl = d_dict["table_name"]

    # Ensure view is registered and query top 20 rows
    duckdb_service.sync_dataset_views()
    query_res = duckdb_service.execute_query(f"SELECT * FROM \"{tbl}\" LIMIT 20;")

    # Provide ready-to-use snippets
    snippets = {
        "sql": f"SELECT * FROM {tbl} LIMIT 10;",
        "python": (
            "import pandas as pd\n"
            f"# Dataset file path: {Path(d_dict['file_path']).as_posix()}\n"
            f"df = pd.read_{d_dict['file_type']}('{Path(d_dict['file_path']).as_posix()}')\n"
            "print(df.head())\n"
            "print(df.info())"
        ),
        "pyspark": (
            "from pyspark.sql import SparkSession\n"
            "spark = SparkSession.builder.appName('DatasetDemo').getOrCreate()\n"
            f"df = spark.read.{d_dict['file_type']}('{Path(d_dict['file_path']).as_posix()}')\n"
            "df.show(5)\n"
            "df.printSchema()"
        )
    }

    return jsonify({
        "success": True,
        "dataset": d_dict,
        "preview": query_res,
        "snippets": snippets
    })

@datasets_bp.route("/api/datasets/delete/<int:dataset_id>", methods=["POST"])
def delete_dataset(dataset_id):
    conn = get_connection()
    dataset = conn.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
    if not dataset:
        conn.close()
        return jsonify({"success": False, "error": "Dataset not found"}), 404

    tbl = dataset["table_name"]
    fpath = Path(dataset["file_path"])

    conn.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
    conn.commit()
    conn.close()

    # Drop view from DuckDB
    try:
        conn_duck = duckdb_service.get_connection()
        conn_duck.execute(f"DROP VIEW IF EXISTS \"{tbl}\";")
        conn_duck.close()
    except Exception as e:
        print(f"Error dropping view: {e}")

    # Remove physical file
    try:
        if fpath.exists():
            fpath.unlink()
    except Exception as e:
        print(f"Error deleting file: {e}")

    return jsonify({"success": True, "message": "Dataset deleted successfully"})

@datasets_bp.route("/api/datasets/duckdb_explorer")
def duckdb_explorer_api():
    duckdb_service.sync_dataset_views()
    schemas = duckdb_service.get_explorer_schema()
    return jsonify({"success": True, "schemas": schemas})
