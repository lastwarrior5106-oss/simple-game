import asyncio

from sqlmodel import SQLModel

from src.database.session import engine, async_session
from src.models.team import Team
from src.models.user import User
from src.utils.security import SecurityUtils
from src.constants import UserConstant
from src.configs import BusinessLogicConfig
async def seed_database():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session() as session:
        # 🔹 Önce users oluştur (owner olacaklar)
        owner1 = User(
            email="owner1@mail.com",
            hashed_password=SecurityUtils.bcrypt("12345678"),
            role=UserConstant.Role.USER.value,
            level=100,
            coins=100000,
        )

        owner2 = User(
            email="owner2@mail.com",
            hashed_password=SecurityUtils.bcrypt("12345678"),
            role=UserConstant.Role.USER.value,
            level=80,
            coins=50000,
        )

        owner3 = User(
            email="owner3@mail.com",
            hashed_password=SecurityUtils.bcrypt("12345678"),
            role=UserConstant.Role.USER.value,
            level=10,
            coins=10000,
        )

        session.add_all([owner1, owner2, owner3])
        await session.flush()  # 🔥 ID'leri al

        # 🔹 Teams (artık owner_id var)
        team_veterans = Team(
            name="Efsaneler Kulübü",
            owner_id=owner1.id,
            member_count=1
        )

        team_broke = Team(
            name="Züğürtler",
            owner_id=owner2.id,
            member_count=1
        )

        team_rookies = Team(
            name="Yeni Çaylaklar",
            owner_id=owner3.id,
            member_count=1
        )

        session.add_all([team_veterans, team_broke, team_rookies])
        await session.flush()

        # 🔹 Diğer users
        users = [
            User(
                email="broke1@mail.com",
                hashed_password=SecurityUtils.bcrypt("12345678"),
                role=UserConstant.Role.USER.value,
                level=85,
                coins=15,
                team_id=team_broke.id,
            ),
            User(
                email="veteran1@mail.com",
                hashed_password=SecurityUtils.bcrypt("12345678"),
                role=UserConstant.Role.USER.value,
                level=150,
                coins=500000,
                team_id=team_veterans.id,
            ),
            User(
                email="rookie1@mail.com",
                hashed_password=SecurityUtils.bcrypt("12345678"),
                role=UserConstant.Role.USER.value,
                level=5,
                coins=5000,
                team_id=team_rookies.id,
            ),
            User(
                email="admin@mail.com",
                hashed_password=SecurityUtils.bcrypt("12345678"),
                role=UserConstant.Role.ADMIN.value,
                level=10,
                coins=999999,
            ),
        ]

        session.add_all(users)
        await session.commit()

        # 🔹 member_count güncelle
        team_veterans.member_count = 2
        team_broke.member_count = 2
        team_rookies.member_count = 2

        session.add_all([team_veterans, team_broke, team_rookies])
        await session.commit()

        print("✅ DB düzgün seed edildi")