import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.db.base import Base, engine
from app.db.session import get_db
from app.schemas.user import UserCreate
from app.schemas.link import LinkCreate
from app.core.config import settings
from app.crud import user as user_crud
from app.crud import link as link_crud



async def init_db(db: AsyncSession) -> None:
    print("Начинаем инициализацию базы данных...")
    
    # Пересоздаем все таблицы
    async with engine.begin() as conn:
        # Удаляем таблицы, если существуют
        await conn.run_sync(Base.metadata.drop_all)
        print("Существующие таблицы удалены.")
        
        # Создаем таблицы заново
        await conn.run_sync(Base.metadata.create_all)
        print("Таблицы созданы успешно.")

    # Создаем суперпользователя
    user_in = UserCreate(
        email="admin@example.com",
        username="admin",
        password="admin",
    )
    admin_user = await user_crud.create(db, obj_in=user_in)
    admin_user.is_superuser = True
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)
    print(f"Суперпользователь создан: id={admin_user.id}, username={admin_user.username}")
    
    # Создаем тестового пользователя
    user_in = UserCreate(
        email="user@example.com",
        username="testuser",
        password="password",
    )
    test_user = await user_crud.create(db, obj_in=user_in)
    print(f"Тестовый пользователь создан: id={test_user.id}, username={test_user.username}")
    
    # Создаем тестовые ссылки
    # 1. Ссылка для админа
    link_in = LinkCreate(
        original_url="https://www.example.com/admin",
        custom_alias="admin-link",
        expires_at=datetime.now() + timedelta(days=30)
    )
    admin_link = await link_crud.create(db, obj_in=link_in, user=admin_user)
    print(f"Создана ссылка для админа: short_code={admin_link.short_code}")
    
    # 2. Ссылка для тестового пользователя
    link_in = LinkCreate(
        original_url="https://www.example.com/user",
        custom_alias="user-link",
        expires_at=datetime.now() + timedelta(days=30)
    )
    user_link = await link_crud.create(db, obj_in=link_in, user=test_user)
    print(f"Создана ссылка для пользователя: short_code={user_link.short_code}")
    
    # 3. Анонимная ссылка
    link_in = LinkCreate(
        original_url="https://www.example.com/anonymous",
        custom_alias="anon-link",
        expires_at=datetime.now() + timedelta(days=7)
    )
    anon_link = await link_crud.create(db, obj_in=link_in, user=None)
    print(f"Создана анонимная ссылка: short_code={anon_link.short_code}")
    
    print("Инициализация базы данных завершена.")


async def main() -> None:
    print("Запуск инициализации...")
    async for db in get_db():
        try:
            await init_db(db)
            print("База данных успешно инициализирована!")
            break
        except Exception as e:
            print(f"Ошибка при инициализации базы данных: {e}")
            raise
    print("Завершено.")


if __name__ == "__main__":
    print("Запуск скрипта инициализации базы данных...")
    asyncio.run(main()) 