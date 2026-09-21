from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(
        String(255),
        nullable=False,
        index=True,
    )
    description = Column(
        Text,
        nullable=False,
    )
    status = Column(
        String(50),
        nullable=False,
        index=True,
        server_default="open",
    )
    priority = Column(
        String(50),
        nullable=False,
        index=True,
        server_default="medium",
    )
    is_resolved = Column(
        Boolean,
        nullable=False,
        server_default="false",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    tenant = relationship(
        "Tenant",
        back_populates="tickets",
    )
    user = relationship(
        "User",
        back_populates="tickets",
    )
    conversation = relationship(
        "Conversation",
    )