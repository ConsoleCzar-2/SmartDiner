from sqlalchemy import String, Integer, DateTime
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Allergen(Base):
    __tablename__ = "allergens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)


class MenuItemAllergen(Base):
    __tablename__ = "menu_item_allergens"

    menu_item_id: Mapped[str] = mapped_column(String(36), sqlalchemy.ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True)
    allergen_id: Mapped[int] = mapped_column(Integer, sqlalchemy.ForeignKey("allergens.id", ondelete="CASCADE"), primary_key=True)
