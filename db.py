"""
db.py — SQLite connection helpers for SchemeMax AI
"""
import sqlite3
import os
import datetime
from flask import g, current_app


def _parse_timestamp(val):
    """
    Robust TIMESTAMP converter for SQLite PARSE_DECLTYPES.
    Handles both:
      - Standard SQLite format:  '2026-04-25 08:03:58'
      - ISO-8601 format:         '2026-04-25T08:03:58.882Z'
    Returns a datetime.datetime or the raw string if unparseable.
    """
    if isinstance(val, bytes):
        val = val.decode("utf-8", errors="replace")
    val = val.strip().replace("Z", "").replace("T", " ")
    # Strip sub-seconds
    val = val.split(".")[0]
    try:
        return datetime.datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.datetime.strptime(val, "%Y-%m-%d")
        except ValueError:
            return val  # return as-is rather than crash


# Register the converter so it applies globally
sqlite3.register_converter("TIMESTAMP", _parse_timestamp)
sqlite3.register_converter("timestamp", _parse_timestamp)


def get_db():
    """Return a database connection scoped to the current Flask application context."""
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """Teardown: close the db connection if it was opened."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Run schema.sql against the database (CREATE TABLE IF NOT EXISTS is idempotent)."""
    from flask import current_app  # local import to avoid circular
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()


def query(sql, args=(), one=False):
    """Helper: execute a SELECT query and return Row(s)."""
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def execute(sql, args=()):
    """Helper: execute an INSERT/UPDATE/DELETE, commit, and return lastrowid."""
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid
