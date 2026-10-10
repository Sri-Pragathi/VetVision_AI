"""User model representing pet owners and system users."""
import uuid
from datetime import datetime, timezone
from app.extensions import db
from app.utils.security import hash_password, check_password


class User(db.Model):
    """User database entity."""
    __tablename__ = "users"

    ROLE_PET_OWNER = "pet_owner"
    ROLE_DOCTOR = "doctor"
    VALID_ROLES = {ROLE_PET_OWNER, ROLE_DOCTOR}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.String(20),
        nullable=False,
        default=ROLE_PET_OWNER,
        server_default=ROLE_PET_OWNER,
    )
    
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

    # Relationship: 1 User has many Pets
    pets = db.relationship(
        "Pet",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __init__(self, name: str, email: str, password: str, role: str = ROLE_PET_OWNER, id: str = None):
        if id:
            self.id = id
        self.name = name.strip()
        self.email = email.strip().lower()
        self.role = role if role in self.VALID_ROLES else self.ROLE_PET_OWNER
        self.set_password(password)

    def set_password(self, password: str) -> None:
        """Hash and set user password."""
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        """Verify user password."""
        return check_password(password, self.password_hash)

    def to_dict(self) -> dict:
        """Serialize user object to safe dictionary (never includes password_hash)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role or self.ROLE_PET_OWNER,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.email}>"
