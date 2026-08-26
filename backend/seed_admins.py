import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.admin_user import AdminUser
from app.models.restaurant import Restaurant
from app.services.auth import get_password_hash

async def seed_admins():
    async with AsyncSessionLocal() as session:
        # Check if platform admin exists
        result = await session.execute(select(AdminUser).where(AdminUser.email == "platform@smartdiner.com"))
        platform_admin = result.scalars().first()
        if not platform_admin:
            platform_admin = AdminUser(
                email="platform@smartdiner.com",
                password_hash=get_password_hash("admin123"),
                role="PLATFORM_ADMIN",
                restaurant_id=None
            )
            session.add(platform_admin)

        # Get first restaurant
        result = await session.execute(select(Restaurant).limit(1))
        restaurant = result.scalars().first()

        if restaurant:
            # Check if restaurant admin exists
            result = await session.execute(select(AdminUser).where(AdminUser.email == "manager@smartdiner.com"))
            restaurant_admin = result.scalars().first()
            if not restaurant_admin:
                restaurant_admin = AdminUser(
                    email="manager@smartdiner.com",
                    password_hash=get_password_hash("manager123"),
                    role="RESTAURANT_ADMIN",
                    restaurant_id=str(restaurant.id)
                )
                session.add(restaurant_admin)
        
        await session.commit()
        print("Admin users seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_admins())
