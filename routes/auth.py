"""
routes/auth.py — /signup  /login  /logout  +  @login_required decorator
"""
from functools import wraps

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import db

auth_bp = Blueprint("auth", __name__)


# ─── Decorator ────────────────────────────────────────────────────────────────

def login_required(f):
    """Redirect to /login if the user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ─── Load current user into g ─────────────────────────────────────────────────

@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        # Check DB first
        user = db.query("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
        if user:
            g.user = dict(user)
        else:
            # Vercel fallback: restore from session cookie if DB was wiped
            g.user = {
                "id": user_id,
                "email": session.get("user_email", ""),
                "full_name": session.get("user_full_name", ""),
                "phone": session.get("user_phone", ""),
                "state": session.get("user_state", ""),
                "age": session.get("user_age", ""),
                "income_bracket": session.get("user_income_bracket", ""),
                "preferred_language": session.get("lang", "en"),
                "created_at": None
            }


# ─── Signup ────────────────────────────────────────────────────────────────────

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        state = request.form.get("state", "").strip()
        age_raw = request.form.get("age", "").strip()
        income_bracket = request.form.get("income_bracket", "").strip()
        preferred_language = request.form.get("preferred_language", "en")

        # Basic validation
        error = None
        if not email:
            error = "Email is required."
        elif not password:
            error = "Password is required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif db.query("SELECT id FROM users WHERE email = ?", (email,), one=True):
            error = "An account with this email already exists."

        if error:
            flash(error, "error")
            return render_template("signup.html")

        age = int(age_raw) if age_raw.isdigit() else None

        db.execute(
            """
            INSERT INTO users
                (email, password_hash, full_name, phone, state, age, income_bracket, preferred_language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email,
                generate_password_hash(password),
                full_name,
                phone,
                state,
                age,
                income_bracket,
                preferred_language,
            ),
        )

        user = db.query("SELECT * FROM users WHERE email = ?", (email,), one=True)
        session.clear()
        session["user_id"] = user["id"]
        session["user_email"] = user["email"]
        session["user_full_name"] = user["full_name"]
        session["user_phone"] = user["phone"]
        session["user_state"] = user["state"]
        session["user_age"] = user["age"]
        session["user_income_bracket"] = user["income_bracket"]
        session["lang"] = preferred_language

        flash("Welcome to SchemeMax AI! Your account has been created.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("signup.html")


# ─── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        error = None
        user = db.query("SELECT * FROM users WHERE email = ?", (email,), one=True)

        if user is None:
            error = "No account found with that email."
        elif not check_password_hash(user["password_hash"], password):
            error = "Incorrect password."

        if error:
            flash(error, "error")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["user_email"] = user["email"]
        session["user_full_name"] = user["full_name"]
        session["user_phone"] = user["phone"]
        session["user_state"] = user["state"]
        session["user_age"] = user["age"]
        session["user_income_bracket"] = user["income_bracket"]
        session["lang"] = user["preferred_language"] or "en"

        flash(f"Welcome back, {user['full_name'] or user['email']}!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


# ─── Logout ────────────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
