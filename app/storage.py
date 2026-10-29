import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone

from config import APP_DB_PATH

# БД SQLite, файл в data/app.db
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS chats (
    email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    id TEXT NOT NULL,
    title TEXT NOT NULL,
    messages TEXT NOT NULL,
    updated_at REAL NOT NULL,
    PRIMARY KEY (email, id)
);
"""

HASH_ITERATIONS = 200_000


def connect() -> sqlite3.Connection:
    APP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(APP_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with closing(connect()) as conn, conn:
        conn.executescript(SCHEMA)


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), HASH_ITERATIONS).hex()


def create_user(email: str, password: str) -> bool:
    salt = secrets.token_hex(16)
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with closing(connect()) as conn, conn:
            conn.execute(
                "INSERT INTO users (email, password_hash, salt, created_at) VALUES (?, ?, ?, ?)",
                (email, _hash(password, salt), salt, created),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def check_password(email: str, password: str) -> bool:
    with closing(connect()) as conn:
        row = conn.execute("SELECT password_hash, salt FROM users WHERE email = ?", (email,)).fetchone()
    return bool(row) and hmac.compare_digest(row["password_hash"], _hash(password, row["salt"]))


def set_password(email: str, password: str):
    salt = secrets.token_hex(16)
    with closing(connect()) as conn, conn:
        conn.execute("UPDATE users SET password_hash = ?, salt = ? WHERE email = ?", (_hash(password, salt), salt, email))


def get_user(email: str) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT email, created_at FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def delete_user(email: str):
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM users WHERE email = ?", (email,))


def create_session(email: str) -> str:
    token = secrets.token_urlsafe(32)
    with closing(connect()) as conn, conn:
        conn.execute("INSERT INTO sessions (token, email, created_at) VALUES (?, ?, ?)", (token, email, time.time()))
    return token


def user_by_token(token: str) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT u.email, u.created_at FROM sessions s JOIN users u ON u.email = s.email WHERE s.token = ?",
            (token,),
        ).fetchone()
    return dict(row) if row else None


def list_chats(email: str) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT id, title, messages, updated_at FROM chats WHERE email = ? ORDER BY updated_at DESC",
            (email,),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "messages": json.loads(r["messages"]),
            "updatedAt": int(r["updated_at"] * 1000),
        }
        for r in rows
    ]


def save_chat(email: str, chat_id: str, title: str, messages: list[dict]):
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO chats (email, id, title, messages, updated_at) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(email, id) DO UPDATE SET
                title = excluded.title,
                messages = excluded.messages,
                updated_at = excluded.updated_at
            """,
            (email, chat_id, title, json.dumps(messages, ensure_ascii=False), time.time()),
        )


def delete_chat(email: str, chat_id: str):
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM chats WHERE email = ? AND id = ?", (email, chat_id))