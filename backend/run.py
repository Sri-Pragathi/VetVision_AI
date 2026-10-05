"""Entrypoint script for running the VetVision AI Backend."""
import os
from app import create_app
from app.extensions import db

# Create application instance using environment setting
env = os.getenv("FLASK_ENV", "development").lower()
app = create_app(env)

if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            from app.models.symptom import seed_symptoms
            seeded = seed_symptoms()
            if seeded > 0:
                app.logger.info(f"Seeded {seeded} clinical symptoms.")
        except Exception as e:
            app.logger.warning(f"Could not auto-create tables or seed symptoms: {e}")

    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "1") == "1"

    print(f"[*] Starting VetVision AI backend on http://{host}:{port} ({env} mode)")
    app.run(host=host, port=port, debug=debug)
