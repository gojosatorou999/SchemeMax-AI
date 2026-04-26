"""
seed.py — Insert 20+ real Indian schemes on first run (table must be empty).
Full seed data is in data/schemes_seed.json; see Phase 2 for the JSON.
This stub is wired up in app.py; the real JSON is added in Phase 2.
"""
import json
import os


def seed_if_empty():
    """Seed schemes table if it is empty. Safe to call on every startup."""
    from db import query, execute  # import here to avoid circular at module load

    count_row = query("SELECT COUNT(*) as cnt FROM schemes", one=True)
    if count_row and count_row["cnt"] > 0:
        return  # already seeded

    seed_path = os.path.join(os.path.dirname(__file__), "data", "schemes_seed.json")
    if not os.path.exists(seed_path):
        return  # seed file not yet present (Phase 1 stub)

    with open(seed_path, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    for s in schemes:
        execute(
            """
            INSERT INTO schemes
                (name, short_description, full_description, benefit_amount,
                 eligibility_json, required_documents, application_link,
                 helpline, issuing_body, category, last_verified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                s.get("name"),
                s.get("short_description"),
                s.get("full_description"),
                s.get("benefit_amount"),
                json.dumps(s.get("eligibility_json", {})),
                json.dumps(s.get("required_documents", [])),
                s.get("application_link"),
                s.get("helpline"),
                s.get("issuing_body"),
                s.get("category"),
                s.get("last_verified"),
            ),
        )
