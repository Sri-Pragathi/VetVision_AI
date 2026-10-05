"""Token blocklist model for JWT revocation on logout."""
from datetime import datetime, timezone
from app.extensions import db


class TokenBlocklist(db.Model):
    """Stores revoked JWT token identifiers (jti)."""
    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    token_type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<TokenBlocklist {self.jti} ({self.token_type})>"
