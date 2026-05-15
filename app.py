"""
app.py — SchemeMax AI Flask application factory

SETUP NOTES (for Vercel / production):
  1. Set environment variables in the Vercel dashboard (not .env):
       SECRET_KEY, OPENAI_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
  2. The database uses SQLite in-memory on Vercel (stateless environment).
     User data is not persisted between cold starts — this is expected for
     a demo/prototype. For persistence, connect a hosted DB (e.g. PlanetScale,
     Supabase, Neon) and swap db.py for a SQLAlchemy/psycopg2 adapter.
  3. OCR (Tesseract) is disabled on Vercel — users can paste text manually.
  4. Twilio WhatsApp sandbox: the recipient must first send
     `join <sandbox-code>` to whatsapp:+14155238886 before
     they can receive sandbox messages from your app.
"""

import os

from flask import Flask

from config import Config
import db
import seed


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)

    # ── Register teardown ────────────────────────────────────────────────────
    app.teardown_appcontext(db.close_db)

    # ── i18n Helper ──────────────────────────────────────────────────────────
    from services.i18n import t
    import json as _json
    app.jinja_env.globals.update(t=t)
    app.jinja_env.filters['from_json'] = lambda s: _json.loads(s) if s else []

    # ── Register blueprints ──────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.schemes import schemes_bp
    from routes.whatsapp import whatsapp_bp
    from routes.ocr import ocr_bp
    from routes.admin import admin_bp
    from routes.calls import calls_bp
    from routes.nearby import nearby_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(schemes_bp)
    app.register_blueprint(whatsapp_bp)
    app.register_blueprint(ocr_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(calls_bp)
    app.register_blueprint(nearby_bp)

    # ── Initialise DB and seed data inside app context ───────────────────────
    with app.app_context():
        try:
            db.init_db()
            seed.seed_if_empty()
        except Exception as exc:
            app.logger.warning(f"DB init/seed warning (non-fatal): {exc}")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
