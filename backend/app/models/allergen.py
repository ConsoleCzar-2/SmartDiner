from sqlalchemy import String, Integer, DateTime
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Allergen(Base):
    __tablename__ = "allergens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    ingredients = relationship("Ingredient", secondary="ingredient_allergens", backref="allergens")
