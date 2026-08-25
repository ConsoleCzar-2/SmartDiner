from sqlalchemy import String, Text, Boolean, DateTime, CheckConstraint, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from uuid6 import uuid7
from app.database import Base

class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid7()))
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    restaurant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("restaurants.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "role IN ('PLATFORM_ADMIN', 'RESTAURANT_ADMIN')",
            name="ck_admin_valid_role"
        ),
        CheckConstraint(
            "(role = 'PLATFORM_ADMIN' AND restaurant_id IS NULL) OR (role = 'RESTAURANT_ADMIN' AND restaurant_id IS NOT NULL)",
            name="ck_admin_scope"
        ),
        Index("idx_admin_restaurant", "restaurant_id"),
    )

    # Relationships
    restaurant = relationship("Restaurant", back_populates="admin_users")
