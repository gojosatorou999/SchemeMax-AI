import json
from flask import Blueprint, request, jsonify, g
from routes.auth import login_required
import db
from services.whatsapp import send_whatsapp_message

whatsapp_bp = Blueprint("whatsapp", __name__)

@whatsapp_bp.route("/api/whatsapp/share", methods=["POST"])
@login_required
def share_scheme():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid payload"}), 400
        
    scheme_id = data.get("scheme_id")
    to_number = data.get("to_number")
    
    if not scheme_id or not to_number:
        return jsonify({"success": False, "error": "Missing scheme_id or to_number"}), 400
        
    scheme = db.query("SELECT * FROM schemes WHERE id = ?", (scheme_id,), one=True)
    if not scheme:
        return jsonify({"success": False, "error": "Scheme not found"}), 404
        
    # Format message
    message = (
        f"🏥 *SchemeMax AI*\n\n"
        f"You might be eligible for: *{scheme['name']}*\n\n"
        f"Benefit: {scheme['benefit_amount']}\n"
        f"{scheme['short_description']}\n\n"
        f"Helpline: {scheme['helpline']}\n"
        f"Apply here: {scheme['application_link']}\n"
    )
    
    result = send_whatsapp_message(to_number, message)
    if result.get("success"):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": result.get("error")}), 500

@whatsapp_bp.route("/api/whatsapp/share_report", methods=["POST"])
@login_required
def share_report():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid payload"}), 400
        
    situation_id = data.get("situation_id")
    to_number = data.get("to_number")
    
    if not situation_id or not to_number:
        return jsonify({"success": False, "error": "Missing situation_id or to_number"}), 400
        
    sit = db.query("SELECT * FROM situations WHERE id = ? AND user_id = ?", (situation_id, g.user["id"]), one=True)
    if not sit:
        return jsonify({"success": False, "error": "Situation not found"}), 404
        
    try:
        matched_data = json.loads(sit["matched_scheme_ids"])
    except:
        matched_data = []
        
    if not matched_data:
        return jsonify({"success": False, "error": "No matched schemes found in report"}), 400
        
    message_lines = ["🏥 *SchemeMax AI Report*\nHere are the top schemes for your situation:\n"]
    
    # We'll just include the top 5 to avoid WhatsApp message length limits
    for match in matched_data[:5]:
        scheme_id = match.get("scheme_id")
        scheme = db.query("SELECT * FROM schemes WHERE id = ?", (scheme_id,), one=True)
        if scheme:
            message_lines.append(f"✅ *{scheme['name']}*")
            message_lines.append(f"Benefit: {scheme['benefit_amount']}")
            message_lines.append(f"Match: {match.get('score', 'N/A')}/100")
            message_lines.append(f"Info: {scheme['application_link']}\n")
            
    message_lines.append("Log in to SchemeMax AI to view personalized document checklists and reasoning.")
    
    result = send_whatsapp_message(to_number, "\n".join(message_lines))
    if result.get("success"):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": result.get("error")}), 500


@whatsapp_bp.route("/api/whatsapp/share-call-report", methods=["POST"])
def share_call_report():
    """Send a call report's matched schemes to WhatsApp."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid payload"}), 400

    report_id = data.get("report_id")
    to_number = data.get("to_number")

    if not report_id or not to_number:
        return jsonify({"success": False, "error": "Missing report_id or to_number"}), 400

    report = db.query("SELECT * FROM call_reports WHERE id = ?", (report_id,), one=True)
    if not report:
        return jsonify({"success": False, "error": "Report not found"}), 404

    try:
        matched_data = json.loads(report["matched_scheme_ids"] or "[]")
    except:
        matched_data = []

    message_lines = [
        f"📞 *SchemeMax AI – Call Report*",
        f"Caller: {report['caller_name']}",
        f"Situation: {str(report['situation_text'])[:200]}...\n",
        "🎯 *Matched Schemes:*\n"
    ]

    for match in matched_data[:5]:
        scheme = db.query("SELECT * FROM schemes WHERE id = ?", (match.get("scheme_id"),), one=True)
        if scheme:
            message_lines.append(f"✅ *{scheme['name']}*")
            message_lines.append(f"   Benefit: {scheme['benefit_amount']}")
            message_lines.append(f"   Score: {match.get('score', 'N/A')}/100")
            message_lines.append(f"   Apply: {scheme['application_link']}\n")

    message_lines.append("Visit SchemeMax AI for detailed eligibility checklists.")

    result = send_whatsapp_message(to_number, "\n".join(message_lines))
    if result.get("success"):
        db.execute("UPDATE call_reports SET whatsapp_sent = 1 WHERE id = ?", (report_id,))
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": result.get("error")}), 500
