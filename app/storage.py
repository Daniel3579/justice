import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


from config import ADMIN_EMAILS, DATABASE_URL, RESET_TOKEN_TTL_MINUTES
# БД постгрес, перенос с sqlite
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS chats (
    email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    id TEXT NOT NULL,
    title TEXT NOT NULL,
    messages JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (email, id)
);
CREATE TABLE IF NOT EXISTS password_resets (
    token_hash TEXT PRIMARY KEY,
    email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    kind TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS events_created_at_idx ON events (created_at);
"""

HASH_ITERATIONS = 200_000
RESET_COOLDOWN_SECONDS = 60


def connect() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db(attempts: int = 30):
    for attempt in range(1, attempts + 1):
        try:
            with connect() as conn:
                conn.execute(SCHEMA)
                if ADMIN_EMAILS:
                    conn.execute("UPDATE users SET is_admin = TRUE WHERE email = ANY(%s)", (ADMIN_EMAILS,))
            return
        except psycopg.OperationalError as e:
            if attempt == attempts:
                raise
            logging.warning(f"База данных недоступна ({e}); повтор через 2 с")
            time.sleep(2)


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), HASH_ITERATIONS).hex()


def _user(row: dict | None) -> dict | None:
    if not row:
        return None
    return {"email": row["email"], "created_at": row["created_at"].isoformat(timespec="seconds"), "is_admin": row["is_admin"]}


def create_user(email: str, password: str) -> bool:
    salt = secrets.token_hex(16)
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO users (email, password_hash, salt, is_admin) VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            """,
            (email, _hash(password, salt), salt, email in ADMIN_EMAILS),
        )
        return cur.rowcount == 1


def check_password(email: str, password: str) -> bool:
    with connect() as conn:
        row = conn.execute("SELECT password_hash, salt FROM users WHERE email = %s", (email,)).fetchone()
    return bool(row) and hmac.compare_digest(row["password_hash"], _hash(password, row["salt"]))


def set_password(email: str, password: str):
    salt = secrets.token_hex(16)
    with connect() as conn:
        conn.execute("UPDATE users SET password_hash = %s, salt = %s WHERE email = %s", (_hash(password, salt), salt, email))


def get_user(email: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT email, created_at, is_admin FROM users WHERE email = %s", (email,)).fetchone()
    return _user(row)


def delete_user(email: str):
    with connect() as conn:
        conn.execute("DELETE FROM users WHERE email = %s", (email,))


def create_session(email: str) -> str:
    token = secrets.token_urlsafe(32)
    with connect() as conn:
        conn.execute("INSERT INTO sessions (token, email) VALUES (%s, %s)", (token, email))
    return token


def user_by_token(token: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT u.email, u.created_at, u.is_admin
            FROM sessions s JOIN users u ON u.email = s.email
            WHERE s.token = %s
            """,
            (token,),
        ).fetchone()
    return _user(row)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_password_reset(email: str) -> str | None:
    with connect() as conn:
        user = conn.execute("SELECT 1 FROM users WHERE email = %s", (email,)).fetchone()
        if not user:
            return None
        recent = conn.execute(
            "SELECT 1 FROM password_resets WHERE email = %s AND created_at > now() - make_interval(secs => %s)",
            (email, RESET_COOLDOWN_SECONDS),
        ).fetchone()
        if recent:
            return None
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
        conn.execute(
            "INSERT INTO password_resets (token_hash, email, expires_at) VALUES (%s, %s, %s)",
            (_token_hash(token), email, expires),
        )
    return token


def reset_password(token: str, password: str) -> bool:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT email FROM password_resets
            WHERE token_hash = %s AND used_at IS NULL AND expires_at > now()
            FOR UPDATE
            """,
            (_token_hash(token),),
        ).fetchone()
        if not row:
            return False
        email = row["email"]
        salt = secrets.token_hex(16)
        conn.execute("UPDATE users SET password_hash = %s, salt = %s WHERE email = %s", (_hash(password, salt), salt, email))
        conn.execute("UPDATE password_resets SET used_at = now() WHERE email = %s AND used_at IS NULL", (email,))
        conn.execute("DELETE FROM sessions WHERE email = %s", (email,))
    return True


def list_chats(email: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, title, messages, updated_at FROM chats WHERE email = %s ORDER BY updated_at DESC",
            (email,),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "messages": r["messages"],
            "updatedAt": int(r["updated_at"].timestamp() * 1000),
        }
        for r in rows
    ]


def save_chat(email: str, chat_id: str, title: str, messages: list[dict]):
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO chats (email, id, title, messages, updated_at) VALUES (%s, %s, %s, %s, now())
            ON CONFLICT (email, id) DO UPDATE SET
                title = EXCLUDED.title,
                messages = EXCLUDED.messages,
                updated_at = EXCLUDED.updated_at
            """,
            (email, chat_id, title, Jsonb(messages)),
        )


def delete_chat(email: str, chat_id: str):
    with connect() as conn:
        conn.execute("DELETE FROM chats WHERE email = %s AND id = %s", (email, chat_id))


def log_event(kind: str):
    try:
        with connect() as conn:
            conn.execute("INSERT INTO events (kind) VALUES (%s)", (kind,))
    except psycopg.Error as e:
        logging.warning(f"Не удалось записать событие {kind}: {e}")


def stats() -> dict:
    with connect() as conn:
        totals = conn.execute(
            """
            SELECT
                (SELECT count(*) FROM users) AS users,
                (SELECT count(*) FROM users WHERE created_at > now() - interval '7 days') AS users_week,
                (SELECT count(*) FROM users WHERE is_admin) AS admins,
                (SELECT count(*) FROM chats) AS chats
            """
        ).fetchone()
        events = conn.execute(
            """
            SELECT kind,
                   count(*) AS total,
                   count(*) FILTER (WHERE created_at > now() - interval '7 days') AS week,
                   count(*) FILTER (WHERE created_at >= date_trunc('day', now())) AS today
            FROM events
            GROUP BY kind
            ORDER BY kind
            """
        ).fetchall()
    return {**totals, "events": events}