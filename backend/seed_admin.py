"""
Запуск: docker compose exec api python seed_admin.py
"""
import asyncio
import uuid

import asyncpg
from passlib.context import CryptContext

EMAIL    = "admin@admin.com"
PASSWORD = "1234"

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def main():
    import os
    db_url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)

    exists = await conn.fetchval("SELECT id FROM users WHERE email = $1", EMAIL)
    if exists:
        print(f"Пользователь {EMAIL} уже существует.")
        await conn.close()
        return

    hashed = pwd.hash(PASSWORD)
    user_id = uuid.uuid4()

    await conn.execute(
        """
        INSERT INTO users (id, email, password_hash, role, first_name, last_name, middle_name)
        VALUES ($1, $2, $3, 'admin', 'Админ', 'Админов', 'Админович')
        """,
        user_id, EMAIL, hashed,
    )
    await conn.close()
    print(f"Администратор создан: {EMAIL} / {PASSWORD}")


asyncio.run(main())
