"""
routes/main.py — /  /dashboard  /api/set-language
"""
from flask import Blueprint, g, jsonify, redirect, render_template, request, session, url_for

from routes.auth import login_required
import db

main_bp = Blueprint("main", __name__)

ALLOWED_LANGS = {"en", "hi", "te"}


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    uid = g.user["id"]
    situations = db.query("SELECT * FROM situations WHERE user_id = ? ORDER BY id DESC", (uid,))

    # ── Real stats ───────────────────────────────────────────────────
    import json as _json

    # Total unique schemes matched across all situations
    total_matches = 0
    for sit in situations:
        try:
            matches = _json.loads(sit["matched_scheme_ids"] or "[]")
            total_matches += len([m for m in matches if isinstance(m, dict) and m.get("score", 0) >= 40])
        except:
            pass

    # Situations count = how many times user has run scheme matching
    total_searches = len(situations)

    # Documents: count situations that have an extracted_context (came from OCR scan)
    docs_scanned = sum(
        1 for sit in situations
        if dict(sit).get("extracted_context") and dict(sit).get("extracted_context") != "{}"
    )

    # Action items: situations from the last 7 days with matches (needs follow-up)
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=7)
    action_items = 0
    for sit in situations:
        try:
            ca = sit["created_at"]
            ts = ca if isinstance(ca, datetime) else datetime.strptime(str(ca)[:19], "%Y-%m-%d %H:%M:%S")
            if ts >= cutoff:
                matches = _json.loads(sit["matched_scheme_ids"] or "[]")
                if matches:
                    action_items += 1
        except:
            pass

    stats = {
        "total_matches":  total_matches,
        "total_searches": total_searches,
        "docs_scanned":   docs_scanned,
        "action_items":   action_items,
    }

    # ── Recommended schemes ──────────────────────────────────────────
    recommended = []
    if situations and situations[0]["matched_scheme_ids"]:
        try:
            matches = _json.loads(situations[0]["matched_scheme_ids"])
            for match in matches[:2]:
                sc = db.query("SELECT * FROM schemes WHERE id = ?", (match["scheme_id"],), one=True)
                if sc:
                    sc_dict = dict(sc)
                    sc_dict["score"] = match.get("score", 95)
                    recommended.append(sc_dict)
        except:
            pass

    if not recommended:
        fallback_schemes = db.query("SELECT * FROM schemes LIMIT 2")
        for sc in fallback_schemes:
            sc_dict = dict(sc)
            sc_dict["score"] = 98
            recommended.append(sc_dict)

    return render_template("dashboard.html", situations=situations, recommended=recommended, stats=stats)


@main_bp.route("/api/set-language", methods=["POST"])
def set_language():
    lang = request.form.get("lang") or request.json.get("lang", "en") if request.is_json else request.form.get("lang", "en")
    if lang not in ALLOWED_LANGS:
        lang = "en"
    session["lang"] = lang
    # Persist to DB if logged in
    if g.user:
        db.execute("UPDATE users SET preferred_language = ? WHERE id = ?", (lang, g.user["id"]))
    referrer = request.referrer or url_for("main.index")
    return redirect(referrer)

@main_bp.route("/api/translations/<lang>")
def get_translations(lang):
    if lang not in ALLOWED_LANGS:
        lang = "en"
    from services.i18n import load_translations
    return jsonify(load_translations(lang))


@main_bp.route("/vault")
@login_required
def vault():
    """Document Vault — shows uploaded docs associated with the user's situations."""
    situations = db.query(
        "SELECT * FROM situations WHERE user_id = ? ORDER BY id DESC",
        (g.user["id"],)
    )
    return render_template("vault.html", situations=situations)


@main_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Profile settings — user can update their details."""
    from flask import flash
    if request.method == "POST":
        full_name  = request.form.get("full_name", "").strip()
        phone      = request.form.get("phone", "").strip()
        state      = request.form.get("state", "").strip()
        age_raw    = request.form.get("age", "").strip()
        income     = request.form.get("income_bracket", "").strip()
        lang       = request.form.get("preferred_language", "en").strip()

        age = int(age_raw) if age_raw.isdigit() else g.user["age"]
        if lang not in ALLOWED_LANGS:
            lang = "en"

        db.execute(
            """UPDATE users
               SET full_name=?, phone=?, state=?, age=?,
                   income_bracket=?, preferred_language=?
               WHERE id=?""",
            (full_name, phone, state, age, income, lang, g.user["id"])
        )
        session["lang"] = lang
        flash("Profile updated successfully! ✅", "success")
        return redirect(url_for("main.settings"))

    return render_template("settings.html")
