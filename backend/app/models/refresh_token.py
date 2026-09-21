from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked = Column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    user = relationship(
        "User",
    )