"""
db.py — JSON-based persistent storage for Story Waver.

Structure of data/stories.json:
{
  "users": {
    "<username>": {
      "password_hash": "<sha256_hex>",
      "salt": "<hex>",
      "created_at": "<iso8601>",
      "stories": [
        {
          "id": "<uuid4>",
          "title": "<first 60 chars of story>",
          "genre": "Romantic",
          "writing_mode": "Beginning",
          "tone": "Dramatic",
          "prompt": "<user prompt>",
          "story": "<full story text>",
          "created_at": "<iso8601>"
        },
        ...
      ]
    }
  }
}
"""

import json
import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/stories.json")


# ── Init ──────────────────────────────────────────────────────────────────────

def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.write_text(json.dumps({"users": {}}, indent=2))


def _load() -> dict:
    init_db()
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Password helpers ──────────────────────────────────────────────────────────

def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


def _new_salt() -> str:
    return os.urandom(16).hex()


# ── User management ───────────────────────────────────────────────────────────

def user_exists(username: str) -> bool:
    data = _load()
    return username.lower() in data["users"]


def create_user(username: str, password: str) -> tuple[bool, str]:
    """Returns (success, message)."""
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password cannot be empty."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    if user_exists(username):
        return False, "Username already taken."

    data = _load()
    salt = _new_salt()
    data["users"][username] = {
        "password_hash": _hash_password(password, salt),
        "salt": salt,
        "created_at": datetime.now().isoformat(),
        "stories": [],
    }
    _save(data)
    return True, "Account created successfully."


def verify_user(username: str, password: str) -> tuple[bool, str]:
    """Returns (success, message)."""
    username = username.strip().lower()
    data = _load()
    user = data["users"].get(username)
    if not user:
        return False, "Username not found."
    expected = _hash_password(password, user["salt"])
    if expected != user["password_hash"]:
        return False, "Incorrect password."
    return True, "Login successful."


def get_user_info(username: str) -> dict:
    data = _load()
    user = data["users"].get(username.lower(), {})
    return {
        "username": username,
        "created_at": user.get("created_at", ""),
        "story_count": len(user.get("stories", [])),
    }


# ── Story management ──────────────────────────────────────────────────────────

def save_story(
    username: str,
    prompt: str,
    story: str,
    genre: str,
    writing_mode: str,
    tone: str,
) -> str:
    """Saves story and returns its ID."""
    username = username.lower()
    data = _load()
    user = data["users"].get(username)
    if not user:
        return ""

    # Auto-title: first sentence or first 60 chars
    title_text = story.strip().replace("\n", " ")
    title = title_text[:60] + ("…" if len(title_text) > 60 else "")

    story_id = str(uuid.uuid4())[:8]
    entry = {
        "id": story_id,
        "title": title,
        "genre": genre,
        "writing_mode": writing_mode,
        "tone": tone,
        "prompt": prompt,
        "story": story,
        "created_at": datetime.now().isoformat(),
    }
    user["stories"].append(entry)
    _save(data)
    return story_id


def get_stories(username: str) -> list[dict]:
    """Returns all stories for a user, newest first."""
    data = _load()
    user = data["users"].get(username.lower(), {})
    stories = user.get("stories", [])
    return list(reversed(stories))


def get_story_by_id(username: str, story_id: str) -> dict | None:
    for s in get_stories(username):
        if s["id"] == story_id:
            return s
    return None


def delete_story(username: str, story_id: str) -> bool:
    username = username.lower()
    data = _load()
    user = data["users"].get(username)
    if not user:
        return False
    before = len(user["stories"])
    user["stories"] = [s for s in user["stories"] if s["id"] != story_id]
    if len(user["stories"]) < before:
        _save(data)
        return True
    return False


def format_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return iso_str
