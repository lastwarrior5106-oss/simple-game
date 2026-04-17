from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from collections.abc import AsyncGenerator
from src.configs import AppConfig

engine = create_async_engine(AppConfig.DATABASE_URL, echo=False)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def init_db():
    # modeller metadata'ya kayıt olsun diye import
    from src.models.user import User
    from src.models.team import Team

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)