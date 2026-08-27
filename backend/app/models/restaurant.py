from sqlalchemy import String, Text, Boolean, DateTime
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from uuid6 import uuid7
from app.database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid7()))
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    cuisine_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())

    # Constraints
    __table_args__ = (
        sqlalchemy.CheckConstraint(
            "cuisine_type IN ('North Indian', 'South Indian', 'Chinese', 'Indo-Chinese', 'Italian', 'Continental', 'Fast Food', 'American', 'Beverages', 'Desserts', 'Other') OR cuisine_type IS NULL",
            name="ck_restaurant_valid_cuisine"
        ),
    )

    # Relationships
    menu_items = relationship("MenuItem", back_populates="restaurant")
    admin_users = relationship("AdminUser", back_populates="restaurant")
    orders = relationship("Order", back_populates="restaurant")
