"""
routes/schemes.py — /situation  /results/<id>  /scheme/<id>
"""
import json
from flask import Blueprint, g, render_template, request, redirect, url_for, flash

from routes.auth import login_required
import db
from services.matcher import match_schemes
from services.llm import llm_client

schemes_bp = Blueprint("schemes", __name__)

@schemes_bp.route("/situation", methods=["GET", "POST"])
@login_required
def situation():
    if request.method == "POST":
        situation_text = request.form.get("description", "").strip()
        
        # Optional overrides
        state = request.form.get("state", "").strip()
        age_raw = request.form.get("age", "").strip()
        income = request.form.get("income_bracket", "").strip()
        
        # If user provided overrides, update their profile temporarily
        if state or age_raw or income:
            age = int(age_raw) if age_raw.isdigit() else g.user["age"]
            st = state if state else g.user["state"]
            inc = income if income else g.user["income_bracket"]
            db.execute(
                "UPDATE users SET state=?, age=?, income_bracket=? WHERE id=?",
                (st, age, inc, g.user["id"])
            )
            # Reload g.user
            g.user = db.query("SELECT * FROM users WHERE id = ?", (g.user["id"],), one=True)
            
        if not situation_text:
            flash("Please describe your situation.", "warning")
            return render_template("situation.html")
            
        situation_id = match_schemes(g.user["id"], situation_text)
        if not situation_id:
            flash("Error processing situation.", "error")
            return redirect(url_for("main.dashboard"))
            
        return redirect(url_for("schemes.results", situation_id=situation_id))
        
    return render_template("situation.html")


@schemes_bp.route("/results/<int:situation_id>")
@login_required
def results(situation_id):
    sit = db.query("SELECT * FROM situations WHERE id = ? AND user_id = ?", (situation_id, g.user["id"]), one=True)
    if not sit:
        flash("Situation not found.", "error")
        return redirect(url_for("main.dashboard"))
        
    try:
        matched_data = json.loads(sit["matched_scheme_ids"]) # list of {scheme_id, score, reasoning}
    except:
        matched_data = []
        
    schemes_details = []
    for match in matched_data:
        scheme_id = match.get("scheme_id")
        scheme_info = db.query("SELECT * FROM schemes WHERE id = ?", (scheme_id,), one=True)
        if scheme_info:
            s_dict = dict(scheme_info)
            s_dict["score"] = match.get("score")
            s_dict["reasoning"] = match.get("reasoning")
            schemes_details.append(s_dict)
            
    return render_template("results.html", situation=sit, schemes=schemes_details)


@schemes_bp.route("/scheme/<int:scheme_id>")
@login_required
def scheme_detail(scheme_id):
    situation_id = request.args.get("situation")
    scheme = db.query("SELECT * FROM schemes WHERE id = ?", (scheme_id,), one=True)
    
    if not scheme:
        flash("Scheme not found.", "error")
        return redirect(url_for("main.dashboard"))
        
    scheme_dict = dict(scheme)
    checklist = json.loads(scheme_dict.get("required_documents", "[]"))
    sit = None
    
    if situation_id:
        sit = db.query("SELECT * FROM situations WHERE id = ? AND user_id = ?", (situation_id, g.user["id"]), one=True)
        if sit:
            try:
                user_context = {
                    "profile": dict(g.user),
                    "situation": json.loads(sit["extracted_context"])
                }
                checklist = llm_client.generate_checklist(scheme_dict, user_context)
            except Exception as e:
                pass
                
    return render_template("scheme_detail.html", scheme=scheme_dict, checklist=checklist, situation=sit)
