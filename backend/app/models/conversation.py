from sqlalchemy import String, DateTime, Index, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from uuid6 import uuid7
from app.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid7()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    restaurant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("restaurants.id"), nullable=True)
    messages: Mapped[list] = mapped_column(JSONB, default=list)
    current_constraints: Mapped[dict] = mapped_column(JSONB, default=dict)
    current_cart: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(20), default='ACTIVE', nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Constraints and Indexes
    __table_args__ = (
        Index("idx_conversations_user", "user_id", "updated_at"),
        CheckConstraint(
            "status IN ('ACTIVE', 'CHECKED_OUT', 'ABANDONED')",
            name="ck_conversation_valid_status"
        ),
    )

    # Relationships
    user = relationship("User", back_populates="conversations")
