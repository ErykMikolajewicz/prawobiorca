import asyncio
import sys

sys.path.append("")

from sqlalchemy import insert

from src.infrastructure.relational_db.connection import async_session_maker
from src.infrastructure.relational_db.schemas.users import users_table


async def seed_db():
    async with async_session_maker.begin() as session:
        # password is PrawobiorcaPassword1;
        statement = insert(users_table).values(
            [
                {
                    "username": "PrawobiorcaTester",
                    "hashed_password": b"$2b$12$NY0/W4kDgXcfQteV/gnsGeqvqGUaNiy/1K/NXAov0kbpEUAPNWRVG",
                    "is_admin": True,
                },
                {
                    "username": "PrawobiorcaTester2",
                    "hashed_password": b"$2b$12$NY0/W4kDgXcfQteV/gnsGeqvqGUaNiy/1K/NXAov0kbpEUAPNWRVG",
                },
            ]
        )

        await session.execute(statement)


if __name__ == "__main__":
    asyncio.run(seed_db())
