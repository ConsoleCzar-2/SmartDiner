from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
import sqlalchemy
from app.database import Base

class DietaryTag(Base):
    __tablename__ = "dietary_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)


class MenuItemTag(Base):
    __tablename__ = "menu_item_tags"

    menu_item_id: Mapped[str] = mapped_column(String(36), sqlalchemy.ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(Integer, sqlalchemy.ForeignKey("dietary_tags.id", ondelete="CASCADE"), primary_key=True)
