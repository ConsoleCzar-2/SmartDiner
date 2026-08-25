"""Database models package — import all models for Alembic autogenerate"""
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.allergen import Allergen, MenuItemAllergen
from app.models.dietary_tag import DietaryTag, MenuItemTag
from app.models.user import User
from app.models.admin_user import AdminUser
from app.models.order import Order, OrderItem
from app.models.conversation import Conversation

__all__ = [
    "Restaurant",
    "MenuItem",
    "Allergen",
    "MenuItemAllergen",
    "DietaryTag",
    "MenuItemTag",
    "User",
    "AdminUser",
    "Order",
    "OrderItem",
    "Conversation",
]