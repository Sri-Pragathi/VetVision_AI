"""Pet model representing animals registered by users."""
import uuid
from datetime import datetime, date, timezone
from typing import Optional
from app.extensions import db


class Pet(db.Model):
    """Pet database entity."""
    __tablename__ = "pets"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    owner_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)  # e.g., Dog, Cat, Bird
    breed = db.Column(db.String(100), nullable=True)
    sex = db.Column(db.String(20), nullable=True)        # Male, Female, Neutered, Spayed
    date_of_birth = db.Column(db.Date, nullable=True)
    weight = db.Column(db.Float, nullable=True)          # in kilograms or pounds
    allergies = db.Column(db.Text, nullable=True)
    existing_conditions = db.Column(db.Text, nullable=True)
    current_medications = db.Column(db.Text, nullable=True)
    vaccination_status = db.Column(db.String(50), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owner = db.relationship("User", back_populates="pets")
    health_assessments = db.relationship(
        "HealthAssessment",
        back_populates="pet",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def age(self) -> Optional[int]:
        """Calculate pet age in years if date_of_birth is set."""
        if not self.date_of_birth:
            return None
        today = date.today()
        years = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            years -= 1
        return max(0, years)

    def to_dict(self) -> dict:
        """Serialize pet entity to dictionary."""
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "sex": self.sex,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age": self.age,
            "weight": self.weight,
            "allergies": self.allergies,
            "existing_conditions": self.existing_conditions,
            "current_medications": self.current_medications,
            "vaccination_status": self.vaccination_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Pet {self.name} ({self.species})>"
