import os
import uuid
import tempfile
from flask import Blueprint, request, jsonify
from routes.auth import login_required
from services.ocr import extract_text

ocr_bp = Blueprint("ocr", __name__)

@ocr_bp.route("/api/ocr/upload", methods=["POST"])
@login_required
def upload_ocr():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"}), 400
        
    # Generate unique filename to avoid conflicts
    ext = os.path.splitext(file.filename)[1]
    temp_name = f"{uuid.uuid4().hex}{ext}"
    
    # Save to OS temp directory
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, temp_name)
    
    try:
        file.save(temp_path)
        extracted_text = extract_text(temp_path)
    finally:
        # Always delete the file to prevent filling up disk
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
                
    return jsonify({"success": True, "text": extracted_text})


@ocr_bp.route("/api/ocr/analyse", methods=["POST"])
@login_required
def analyse_ocr():
    """
    Takes raw OCR-extracted text and asks the LLM to produce a
    structured eligibility profile report.
    """
    data = request.get_json()
    if not data or not data.get("text"):
        return jsonify({"success": False, "error": "No text provided"}), 400

    raw_text = data["text"].strip()
    if not raw_text:
        return jsonify({"success": False, "error": "Empty text"}), 400

    try:
        from openai import OpenAI
        import os

        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        system_prompt = (
            "You are an expert Indian government welfare scheme advisor. "
            "A user has submitted scanned document text (OCR-extracted). "
            "Analyse it and produce a concise eligibility profile with:\n"
            "- Full name, age, gender (if found)\n"
            "- State / district / address\n"
            "- Occupation and income details\n"
            "- Family details (dependants, BPL/APL status)\n"
            "- Any scheme-relevant flags (disability, widow, farmer, SC/ST/OBC, etc.)\n"
            "- A plain-language summary (2-3 sentences) of which category of schemes "
            "  they are most likely eligible for\n\n"
            "Be concise. If information is missing, say 'Not mentioned'. "
            "Output in readable plain text (no markdown)."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": f"Document text:\n\n{raw_text[:3000]}"}
            ],
            temperature=0.3,
            max_tokens=600,
        )

        report = response.choices[0].message.content.strip()
        return jsonify({"success": True, "report": report})

    except Exception as e:
        # Graceful fallback — return the raw OCR text so the flow doesn't break
        return jsonify({
            "success": True,
            "report": (
                f"[Auto-extracted from document]\n\n{raw_text}\n\n"
                f"(LLM analysis unavailable: {str(e)[:120]})"
            )
        })
