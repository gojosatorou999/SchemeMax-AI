import json
from flask import Blueprint, render_template, current_app, redirect, url_for, flash, g
from routes.auth import login_required
import db

admin_bp = Blueprint("admin", __name__)

@admin_bp.before_request
@login_required
def require_admin():
    admin_email = current_app.config.get("ADMIN_EMAIL")
    if not g.user or g.user["email"] != admin_email:
        flash("Unauthorized access.", "error")
        return redirect(url_for("main.dashboard"))

@admin_bp.route("/admin/dashboard")
def dashboard():
    # Basic metrics
    users_count_row = db.query("SELECT COUNT(*) as count FROM users", one=True)
    users_count = users_count_row["count"] if users_count_row else 0
    
    situations_count_row = db.query("SELECT COUNT(*) as count FROM situations", one=True)
    situations_count = situations_count_row["count"] if situations_count_row else 0
    
    # Aggregating most common matched schemes
    # Since matched_scheme_ids is a JSON array of dicts in SQLite, we do this in Python
    all_situations = db.query("SELECT matched_scheme_ids FROM situations")
    
    scheme_counts = {}
    for row in all_situations:
        try:
            matches = json.loads(row["matched_scheme_ids"])
            for match in matches:
                scheme_id = match.get("scheme_id")
                if scheme_id:
                    scheme_counts[scheme_id] = scheme_counts.get(scheme_id, 0) + 1
        except:
            pass
            
    # Resolve scheme IDs to names
    top_schemes = []
    if scheme_counts:
        # Sort by count descending
        sorted_counts = sorted(scheme_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for s_id, count in sorted_counts:
            scheme = db.query("SELECT name FROM schemes WHERE id = ?", (s_id,), one=True)
            if scheme:
                top_schemes.append({
                    "name": scheme["name"],
                    "count": count
                })
                
    return render_template("admin_dashboard.html", 
                           users_count=users_count, 
                           situations_count=situations_count,
                           top_schemes=top_schemes)
