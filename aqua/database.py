import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "aqua.db")
DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    from aqua.models import User, SensorData
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed default users
    await seed_users()

async def seed_users():
    from aqua.models import User
    from aqua.security import get_password_hash
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        # Check if TheLionBro024 exists
        result = await session.execute(select(User).where(User.username == "TheLionBro024"))
        if not result.scalars().first():
            user1 = User(
                username="TheLionBro024",
                password=get_password_hash("admin123"), # Default password, they can change it later
                is_admin=True,
                is_confirmed=True
            )
            session.add(user1)
            
        # Check if Chengotic exists
        result = await session.execute(select(User).where(User.username == "Chengotic"))
        if not result.scalars().first():
            user2 = User(
                username="Chengotic",
                password=get_password_hash("admin123"), # Default password
                is_admin=True,
                is_confirmed=True
            )
            session.add(user2)
            
        await session.commit()
