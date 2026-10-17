"""
Flask backend - Docker assignment
Author: Samriddhi Mishra

Receives the form data sent by the Express frontend, validates and processes it,
and stores it. Storage:
  * MongoDB, if MONGO_URI is set (e.g. a MongoDB Atlas connection string)
  * otherwise a JSON file inside the container (data/submissions.json)

Routes
  GET  /health        -> {"status": "ok"}  (used by Docker Compose health check)
  GET  /api           -> JSON list read from data.json
  POST /submit        -> validate + store one form submission
  GET  /submissions   -> all stored submissions
"""
import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
STORE_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
STORE_FILE = os.path.join(STORE_DIR, "submissions.json")
MONGO_URI = os.getenv("MONGO_URI", "").strip()

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
COURSES = ["DevOps", "Python", "Flask", "MongoDB", "Docker"]
_lock = threading.Lock()
_collection = None


# ---------------- storage helpers ----------------
def mongo_collection():
    global _collection
    if _collection is None:
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _collection = client[os.getenv("MONGO_DB_NAME", "docker_assignment")]["submissions"]
    return _collection


def save_submission(record):
    if MONGO_URI:
        mongo_collection().insert_one({**record})
        return "mongodb"
    with _lock:
        os.makedirs(STORE_DIR, exist_ok=True)
        items = load_file_submissions()
        items.append(record)
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
    return "json-file"


def load_file_submissions():
    try:
        with open(STORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# ---------------- routes ----------------
@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "flask-backend"})


@app.route("/api")
def api():
    """Return the JSON list stored in data.json."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/submit", methods=["POST"])
def submit():
    """Handle the form submission sent by the Express frontend."""
    payload = request.get_json(silent=True) or request.form
    data = {
        "name": str(payload.get("name", "")).strip(),
        "email": str(payload.get("email", "")).strip().lower(),
        "course": str(payload.get("course", "")).strip(),
        "message": str(payload.get("message", "")).strip(),
    }

    # 1. Validate
    if not data["name"] or not data["email"] or not data["course"]:
        return jsonify({"error": "Name, email and course are required."}), 400
    if not EMAIL_PATTERN.match(data["email"]):
        return jsonify({"error": "Please enter a valid email address."}), 400
    if data["course"] not in COURSES:
        return jsonify({"error": f"Unknown course '{data['course']}'."}), 400

    # 2. Process: tidy the name, add an id and a timestamp
    record = {
        "id": uuid.uuid4().hex[:12],
        **data,
        "name": data["name"].title(),
        "submitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    # 3. Store
    try:
        storage = save_submission(record)
    except Exception as e:  # database / disk problems are reported to the frontend
        reason = (str(e).strip() or type(e).__name__).splitlines()[0][:300]
        return jsonify({"error": f"Could not save your data: {reason}"}), 500

    record.pop("_id", None)
    app.logger.info("Saved submission %s (%s) using %s", record["id"], record["email"], storage)
    return jsonify({"message": "Data submitted successfully", "storage": storage, "submission": record}), 201


@app.route("/submissions")
def submissions():
    if MONGO_URI:
        items = list(mongo_collection().find({}, {"_id": 0}))
    else:
        items = load_file_submissions()
    return jsonify({"count": len(items), "submissions": items})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
