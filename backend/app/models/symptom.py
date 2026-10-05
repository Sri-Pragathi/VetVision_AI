"""Symptom vocabulary model representing clinical symptoms."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.extensions import db


class Symptom(db.Model):
    """Symptom reference entity for structured health assessments."""
    __tablename__ = "symptoms"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    assessment_associations = db.relationship(
        "AssessmentSymptom",
        back_populates="symptom",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize symptom to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Symptom {self.name} ({self.category})>"


# Seed vocabulary of common clinical symptoms
COMMON_SYMPTOMS_SEED = [
    # Digestive
    {"name": "vomiting", "category": "Digestive", "description": "Forceful expulsion of stomach contents."},
    {"name": "diarrhea", "category": "Digestive", "description": "Frequent, loose, or watery bowel movements."},
    {"name": "loss of appetite", "category": "Digestive", "description": "Refusal or marked reduction in food intake (anorexia)."},
    {"name": "excessive thirst", "category": "Digestive", "description": "Abnormally high water consumption (polydipsia)."},
    # Respiratory
    {"name": "coughing", "category": "Respiratory", "description": "Sudden, noisy expulsion of air from lungs."},
    {"name": "sneezing", "category": "Respiratory", "description": "Frequent involuntary expulsion of air through nose and mouth."},
    {"name": "difficulty breathing", "category": "Respiratory", "description": "Labored, rapid, or shallow breathing (dyspnea)."},
    # General
    {"name": "lethargy", "category": "General", "description": "Drowsiness, sluggishness, or abnormal lack of energy."},
    {"name": "fever", "category": "General", "description": "Elevated body temperature."},
    # Skin
    {"name": "itching", "category": "Skin", "description": "Persistent scratching, biting, or licking of skin or paws (pruritus)."},
    {"name": "hair loss", "category": "Skin", "description": "Thinning fur or bald patches on coat (alopecia)."},
    {"name": "skin redness", "category": "Skin", "description": "Flushed, irritated, or inflamed skin patches (erythema)."},
    {"name": "swelling", "category": "Skin", "description": "Abnormal enlargement or fluid buildup under the skin."},
    # Musculoskeletal
    {"name": "limping", "category": "Musculoskeletal", "description": "Impaired walking, stiffness, or reluctance to bear weight on a limb."},
    # Eyes
    {"name": "eye discharge", "category": "Eyes", "description": "Watery, mucus, or purulent drainage from one or both eyes."},
    # Ears
    {"name": "ear discharge", "category": "Ears", "description": "Odor, wax buildup, or liquid drainage accompanied by head shaking."},
    # Neurological
    {"name": "seizures", "category": "Neurological", "description": "Uncontrolled shaking, tremors, twitching, or loss of consciousness."},
    # Urinary
    {"name": "excessive urination", "category": "Urinary", "description": "Unusually frequent or large volume urination (polyuria)."},
    {"name": "difficulty urinating", "category": "Urinary", "description": "Straining, crying out, or frequent unsuccessful attempts to urinate."},
    # Behavioural
    {"name": "abnormal behaviour", "category": "Behavioural", "description": "Uncharacteristic aggression, hiding, restlessness, or vocalization."},
]


def seed_symptoms() -> int:
    """Seed symptom vocabulary into the database if not already present."""
    count = 0
    for item in COMMON_SYMPTOMS_SEED:
        existing = Symptom.query.filter_by(name=item["name"]).first()
        if not existing:
            symptom = Symptom(
                name=item["name"],
                category=item["category"],
                description=item["description"],
            )
            db.session.add(symptom)
            count += 1
    if count > 0:
        db.session.commit()
    return count
