from flask import Blueprint, render_template, request, jsonify, make_response
from datetime import date
from models.db import (
    list_key_notes,
    get_key_note_by_id,
    get_or_create_daily_note,
    save_key_note,
    delete_key_note,
    TECHNOLOGIES
)

notes_bp = Blueprint("notes", __name__)

NOTE_CATEGORIES = [
    "Key Notes",
    "SQL",
    "Python",
    "PySpark",
    "Databricks",
    "Cloud",
    "DSA",
    "System Design",
    "HR & Behavioral",
    "General"
]

@notes_bp.route("/documentation")
@notes_bp.route("/notes")
def notes_view():
    note_id_arg = request.args.get("id")
    date_arg = request.args.get("date")
    category_arg = request.args.get("category")
    tech_arg = request.args.get("tech")

    notes = list_key_notes()
    active_note = None

    if note_id_arg and note_id_arg.isdigit():
        active_note = get_key_note_by_id(int(note_id_arg))
    elif date_arg:
        active_note = get_or_create_daily_note(date_arg, tech=tech_arg or "")
        # Refresh notes list so newly created note appears
        notes = list_key_notes()
    elif category_arg:
        cat_notes = [n for n in notes if n["category"] == category_arg]
        if cat_notes:
            active_note = cat_notes[0]

    # If no explicit note specified, check cookie for last viewed note
    if not active_note:
        saved_note_id = request.cookies.get("cph_last_note_id")
        if saved_note_id and saved_note_id.isdigit():
            active_note = get_key_note_by_id(int(saved_note_id))

    if not active_note and len(notes) > 0:
        active_note = notes[0]

    resp = make_response(render_template(
        "notes.html",
        notes=notes,
        active_note=active_note,
        categories=NOTE_CATEGORIES,
        technologies=TECHNOLOGIES,
        today_date=date.today().isoformat()
    ))
    if active_note:
        resp.set_cookie("cph_last_note_id", str(active_note["id"]), max_age=30*86400, samesite="Lax")
    return resp

@notes_bp.route("/api/notes/list")
def api_list_notes():
    search = request.args.get("search")
    category = request.args.get("category")
    date_str = request.args.get("date")
    tech = request.args.get("technology")

    notes = list_key_notes(search=search, category=category, date_str=date_str, technology=tech)
    return jsonify({"success": True, "notes": notes, "count": len(notes)})

@notes_bp.route("/api/notes/<int:note_id>")
def api_get_note(note_id):
    note = get_key_note_by_id(note_id)
    if not note:
        return jsonify({"success": False, "error": "Note not found"}), 404
    return jsonify({"success": True, "note": note})

@notes_bp.route("/api/notes/by-date/<date_str>")
def api_get_daily_note(date_str):
    tech = request.args.get("tech", "")
    note = get_or_create_daily_note(date_str=date_str, tech=tech)
    return jsonify({"success": True, "note": note})

@notes_bp.route("/api/notes/save", methods=["POST"])
def api_save_note():
    data = request.get_json() or {}
    try:
        saved = save_key_note(data)
        return jsonify({"success": True, "note": saved, "message": "Note saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@notes_bp.route("/api/notes/delete", methods=["POST"])
def api_delete_note():
    data = request.get_json() or {}
    note_id = data.get("note_id") or data.get("id")
    if not note_id:
        return jsonify({"success": False, "error": "Missing note_id"}), 400

    try:
        delete_key_note(note_id)
        return jsonify({"success": True, "message": "Note deleted successfully", "deleted_id": note_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
