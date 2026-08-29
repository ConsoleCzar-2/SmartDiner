from sqlalchemy import String, Text, Boolean, Integer, Numeric, DateTime, CheckConstraint, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from uuid6 import uuid7
from app.database import Base

class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid7()))
    restaurant_id: Mapped[str] = mapped_column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    dietary_preference: Mapped[str] = mapped_column(String(30), default="Non-Vegetarian", nullable=False)
    spice_level: Mapped[str] = mapped_column(String(20), nullable=False)
    cuisine: Mapped[str] = mapped_column(String(50), nullable=False)
    serving_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(2, 1), default=4.0)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_menu_items_price_nonneg"),
        CheckConstraint("serving_size > 0", name="ck_menu_items_serving_positive"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_menu_items_rating_range"),
        CheckConstraint(
            "category IN ('Starter', 'Main Course', 'Bread', 'Rice', 'Beverage', 'Dessert', 'Side', 'Combo', 'Fast Food')",
            name="ck_menu_items_valid_category"
        ),
        CheckConstraint(
            "spice_level IN ('None', 'Low', 'Medium', 'High', 'Extreme')",
            name="ck_menu_items_valid_spice"
        ),
        CheckConstraint(
            "cuisine IN ('North Indian', 'South Indian', 'Chinese', 'Indo-Chinese', 'Italian', 'Continental', 'Fast Food', 'American', 'Beverages', 'Desserts', 'Other')",
            name="ck_menu_items_valid_cuisine"
        ),
        CheckConstraint(
            "dietary_preference IN ('Vegetarian', 'Vegan', 'Non-Vegetarian')",
            name="ck_menu_items_valid_dietary"
        ),
        Index("idx_menu_filter", "restaurant_id", "is_available", "dietary_preference", "spice_level", "price"),
        Index("idx_menu_category", "category"),
        Index("idx_menu_cuisine", "cuisine"),
    )

    # Relationships
    restaurant = relationship("Restaurant", back_populates="menu_items")
    ingredients = relationship("Ingredient", secondary="menu_item_ingredients", backref="menu_items")
    dietary_tags = relationship("DietaryTag", secondary="menu_item_tags", backref="menu_items")
    direct_allergens = relationship("Allergen", secondary="menu_item_allergens", backref="menu_items_direct")
    order_items = relationship("OrderItem", back_populates="menu_item")
