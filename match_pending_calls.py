"""
Run scheme matching directly on call_reports rows that have no matches yet.
Uses the LLM rank_schemes pipeline but saves results to call_reports table directly.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
app = create_app()

with app.app_context():
    import db
    from services.llm import llm_client

    pending = db.query(
        "SELECT id, caller_name, situation_text FROM call_reports "
        "WHERE matched_scheme_ids IS NULL OR matched_scheme_ids = '[]'"
    )

    if not pending:
        print("No pending reports to match.")
    else:
        for row in pending:
            rid  = row["id"]
            name = row["caller_name"]
            text = row["situation_text"] or ""
            print(f"Matching report #{rid} for {name}...")

            try:
                row_d = dict(row)
                # Extract context from the situation text
                extracted = llm_client.extract_context(text)

                # Build a synthetic user context from call data
                user_context = {
                    "user_profile": {
                        "full_name": name,
                        "state": extracted.get("state_hint", "Telangana"),
                        "age": extracted.get("age_hint"),
                        "income_bracket": None,
                        "phone": row_d.get("phone", ""),
                    },
                    "extracted_situation": extracted,
                    "raw_text": text
                }

                # Get all schemes (limit to 15 most relevant categories)
                all_schemes = db.query("SELECT * FROM schemes LIMIT 15")
                schemes_list = [dict(s) for s in all_schemes]

                # Rank with LLM
                ranked = llm_client.rank_schemes(user_context, schemes_list)

                # Keep matches with score >= 40
                final = [r for r in ranked if r.get("score", 0) >= 40]
                if not final and ranked:
                    final = ranked[:3]  # fallback: top 3

                db.execute(
                    "UPDATE call_reports SET matched_scheme_ids = ? WHERE id = ?",
                    (json.dumps(final), rid)
                )
                print(f"  -> {len(final)} schemes matched.")

            except Exception as e:
                import traceback
                print(f"  -> ERROR: {e}")
                traceback.print_exc()

    print("All done.")
