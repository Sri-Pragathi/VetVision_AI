"""Entrypoint script for running the VetVision AI Backend."""
import os
from app import create_app
from app.extensions import db

# Create application instance using environment setting
env = os.getenv("FLASK_ENV", "development").lower()
app = create_app(env)

def init_database(flask_app, current_env):
    """Seed vocabularies and ensure demo profiles exist upon initial boot."""
    with flask_app.app_context():
        try:
            db.create_all()
            from app.models.symptom import seed_symptoms
            from app.models.question_bank import seed_follow_up_questions
            from app.models.user import User
            from app.models.pet import Pet

            seeded_sym = seed_symptoms()
            if seeded_sym > 0:
                flask_app.logger.info(f"Seeded {seeded_sym} clinical symptoms.")

            seeded_q = seed_follow_up_questions()
            if seeded_q > 0:
                flask_app.logger.info(f"Seeded {seeded_q} clinical follow-up questions.")

            # Seed demo accounts if not already in database
            demo_email = "john.doe@vetvision.ai"
            demo_user = User.query.filter_by(email=demo_email).first()
            if not demo_user:
                demo_password = os.getenv("DEV_DEMO_PASSWORD", "Password123!")
                demo_user = User(
                    name="John Doe",
                    email=demo_email,
                    password=demo_password,
                )
                db.session.add(demo_user)
                db.session.commit()
            elif demo_user.name and ("Dr." in demo_user.name or "Dr " in demo_user.name):
                demo_user.name = demo_user.name.replace("Dr. ", "").replace("Dr ", "").strip()
                db.session.commit()
                # Add initial demo pet
                demo_pet = Pet(
                    owner_id=demo_user.id,
                    name="Max",
                    species="Dog",
                    breed="Golden Retriever",
                    sex="male",
                    weight=31.5,
                    allergies="None known",
                    existing_conditions="None reported",
                )
                db.session.add(demo_pet)
                db.session.commit()
                flask_app.logger.info("Initialized demo user and pet profile.")

            # Seed doctor account if missing
            demo_doc_email = os.getenv("DEV_DOCTOR_EMAIL", "doctor@vetvision.ai")
            demo_doctor = User.query.filter_by(email=demo_doc_email).first()
            if not demo_doctor:
                demo_doc_password = os.getenv("DEV_DOCTOR_PASSWORD", "Doctor123!Secure")
                demo_doctor = User(
                    name="Dr. Sarah Smith, DVM",
                    email=demo_doc_email,
                    password=demo_doc_password,
                    role=User.ROLE_DOCTOR,
                )
                db.session.add(demo_doctor)
                db.session.commit()
                flask_app.logger.info("Initialized doctor account.")
        except Exception as e:
            flask_app.logger.warning(f"Could not complete database initialization: {e}")

# Run database setup on startup
init_database(app, env)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "1") == "1"

    print(f"[*] Starting VetVision AI backend on http://{host}:{port} ({env} mode)")
    app.run(host=host, port=port, debug=debug)
