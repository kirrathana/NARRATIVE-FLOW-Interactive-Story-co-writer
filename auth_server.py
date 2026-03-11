import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_from_directory, session

app = Flask(__name__, static_folder=".")
app.secret_key = os.urandom(24)

USERS_FILE = Path("data/stories.json")
STREAMLIT_URL = "http://localhost:8501"


# ── helpers ──────────────────────────────────────────────────────────────────

def load_users():
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": {}}


def save_users(data):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = os.urandom(16).hex()
    pw_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return pw_hash, salt


# ── routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "login.html")


@app.route("/api/register", methods=["POST"])
def register():
    data     = request.get_json(force=True)
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"success": False, "message": "All fields are required."}), 400

    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400

    db = load_users()
    if email in db.get("users", {}):
        return jsonify({"success": False, "message": "An account with this email already exists."}), 409

    pw_hash, salt = hash_password(password)
    db.setdefault("users", {})[email] = {
        "name":          name,
        "password_hash": pw_hash,
        "salt":          salt,
        "created_at":    datetime.now().isoformat(),
        "stories":       [],
    }
    save_users(db)
    return jsonify({"success": True, "message": f"Account created for {name}!"})


@app.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json(force=True)
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    db   = load_users()
    user = db.get("users", {}).get(email)

    if not user:
        return jsonify({"success": False, "message": "No account found with that email."}), 401

    pw_hash, _ = hash_password(password, user["salt"])
    if pw_hash != user["password_hash"]:
        return jsonify({"success": False, "message": "Incorrect password."}), 401

    session["user_email"] = email
    session["user_name"]  = user["name"]
    return jsonify({"success": True, "name": user["name"], "redirect": STREAMLIT_URL})


@app.route("/api/check-email", methods=["POST"])
def check_email():
    """Tells the frontend whether an email is registered (for UX hint only)."""
    email = request.get_json(force=True).get("email", "").strip().lower()
    db    = load_users()
    exists = email in db.get("users", {})
    return jsonify({"exists": exists})


@app.route("/api/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/api/status")
def status():
    if "user_email" in session:
        return jsonify({"logged_in": True,
                        "email":     session["user_email"],
                        "name":      session["user_name"]})
    return jsonify({"logged_in": False})


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Auth server running → http://localhost:5000")
    print("After login you will be redirected → " + STREAMLIT_URL)
    app.run(port=5000, debug=True)
