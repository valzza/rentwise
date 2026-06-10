from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

# ── PostgreSQL ──────────────────────────────────────────────────────────────
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# ── MongoDB ─────────────────────────────────────────────────────────────────
# Short server-selection timeout so the app degrades gracefully (fails fast)
# instead of hanging ~30s when MongoDB is not running.
motor_client: AsyncIOMotorClient = AsyncIOMotorClient(
    settings.MONGO_URI,
    serverSelectionTimeoutMS=2000,
    connectTimeoutMS=2000,
)
mongo_db: AsyncIOMotorDatabase = motor_client[settings.MONGO_DB_NAME]
