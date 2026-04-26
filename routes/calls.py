"""
routes/calls.py — Sync & display AI calling agent reports
"""
import json
import threading
import urllib.request
from datetime import datetime

from flask import Blueprint, g, jsonify, render_template, request

from routes.auth import login_required
import db

calls_bp = Blueprint("calls", __name__)

CALLS_CSV_URL = "https://7edb0d31-2c1a-4244-9a72-3a3fe08acfb4-00-iyse5cgciihi.sisko.replit.dev/api/logs.csv"


# ── DB helper ──────────────────────────────────────────────────────────────────
def ensure_call_reports_table():
    """Create call_reports table if it doesn't exist."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS call_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT UNIQUE,
            caller_name TEXT,
            phone TEXT,
            age TEXT,
            state TEXT,
            monthly_income TEXT,
            has_ayushman_card TEXT,
            health_problem TEXT,
            transcript TEXT,
            situation_text TEXT,
            matched_scheme_ids TEXT,
            whatsapp_sent INTEGER DEFAULT 0,
            raw_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Add new columns to existing tables if they don't exist yet
    for col, typedef in [
        ("age", "TEXT"),
        ("state", "TEXT"),
        ("monthly_income", "TEXT"),
        ("has_ayushman_card", "TEXT"),
        ("health_problem", "TEXT"),
    ]:
        try:
            db.execute(f"ALTER TABLE call_reports ADD COLUMN {col} {typedef}")
        except Exception:
            pass  # column already exists


# ── Pull & process latest calls from the CSV endpoint ─────────────────────────
def fetch_and_sync_calls():
    """Fetch /api/logs.csv, parse rows, run LLM matching on new calls, save to DB."""
    import csv
    import io

    try:
        req = urllib.request.Request(CALLS_CSV_URL, headers={"User-Agent": "SchemeMax/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8-sig")  # strip BOM if present
    except Exception as e:
        return {"error": str(e), "synced": 0}

    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    if not rows:
        return {"synced": 0, "total": 0}

    synced = 0
    for row in rows:
        call_id = (row.get("call_sid") or "").strip()
        if not call_id:
            continue

        # Skip if already synced
        existing = db.query(
            "SELECT id FROM call_reports WHERE call_id = ?", (call_id,), one=True
        )
        if existing:
            continue

        caller_name     = (row.get("name") or "Unknown Caller").strip()
        phone           = (row.get("phone_number") or "").strip()
        age             = (row.get("age") or "").strip()
        state           = (row.get("state") or "").strip()
        monthly_income  = (row.get("monthly_income") or "").strip()
        has_ayushman    = (row.get("has_ayushman_card") or "").strip()
        health_problem  = (row.get("health_problem") or "").strip()
        timestamp       = (row.get("timestamp") or "").strip()

        # Build transcript from structured fields for LLM matching
        transcript = (
            f"Name: {caller_name}. Age: {age}. State: {state}. "
            f"Monthly income: {monthly_income}. "
            f"Has Ayushman card: {has_ayushman}. "
            f"Health problem: {health_problem}."
        )

        # Run LLM scheme matching on transcript
        matched_json = "[]"
        try:
            from services.matcher import match_schemes
            system_user = db.query(
                "SELECT id FROM users WHERE email = 'admin@gmail.com'", one=True
            )
            if not system_user:
                system_user = db.query(
                    "SELECT id FROM users ORDER BY id LIMIT 1", one=True
                )
            if system_user:
                situation_id = match_schemes(system_user["id"], transcript)
                if situation_id:
                    sit = db.query(
                        "SELECT matched_scheme_ids FROM situations WHERE id = ?",
                        (situation_id,), one=True
                    )
                    if sit:
                        matched_json = sit["matched_scheme_ids"] or "[]"
        except Exception:
            pass

        db.execute(
            """INSERT OR IGNORE INTO call_reports
               (call_id, caller_name, phone, age, state, monthly_income,
                has_ayushman_card, health_problem, transcript, situation_text,
                matched_scheme_ids, raw_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                call_id, caller_name, phone, age, state, monthly_income,
                has_ayushman, health_problem, transcript, transcript,
                matched_json, json.dumps(dict(row)), timestamp or None,
            ),
        )
        synced += 1

    return {"synced": synced, "total": len(rows)}


# ── Routes ─────────────────────────────────────────────────────────────────────

@calls_bp.route("/api/sync-calls", methods=["POST"])
def sync_calls():
    """Manually trigger a sync of the AI calling agent reports."""
    ensure_call_reports_table()
    result = fetch_and_sync_calls()
    return jsonify(result)


@calls_bp.route("/api/call-reports")
def api_call_reports():
    """Return latest call reports as JSON for live polling."""
    ensure_call_reports_table()
    reports = db.query("SELECT * FROM call_reports ORDER BY id DESC LIMIT 50")
    out = []
    for r in reports:
        rd = dict(r)
        try:
            rd["schemes"] = json.loads(rd.get("matched_scheme_ids") or "[]")
        except:
            rd["schemes"] = []
        out.append(rd)
    return jsonify(out)


@calls_bp.route("/calls")
@login_required
def call_reports_page():
    """Full page showing all synced call reports with matched schemes."""
    ensure_call_reports_table()
    # Trigger a fresh sync every time the page is loaded
    fetch_and_sync_calls()

    reports = db.query("SELECT * FROM call_reports ORDER BY id DESC")
    enriched = []
    for r in reports:
        rd = dict(r)
        matched = []
        try:
            for match in json.loads(rd.get("matched_scheme_ids") or "[]"):
                sc = db.query("SELECT * FROM schemes WHERE id = ?", (match.get("scheme_id"),), one=True)
                if sc:
                    s = dict(sc)
                    s["score"] = match.get("score", 0)
                    s["reasoning"] = match.get("reasoning", "")
                    matched.append(s)
        except:
            pass
        rd["matched_schemes"] = matched
        enriched.append(rd)

    return render_template("call_reports.html", reports=enriched)
