from datetime import datetime
from typing import Optional, List, Union, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, func, or_, and_

from app.core.security import generate_short_code
from app.core.config import settings
from app.models.link import Link
from app.models.user import User
from app.schemas.link import LinkCreate, LinkUpdate


async def get(db: AsyncSession, link_id: int) -> Optional[Link]:
    result = await db.execute(select(Link).where(Link.id == link_id))
    return result.scalars().first()


async def get_by_short_code(db: AsyncSession, short_code: str) -> Optional[Link]:
    result = await db.execute(select(Link).where(
        and_(
            Link.short_code == short_code,
            or_(
                Link.expires_at > datetime.now(),
                Link.expires_at == None
            ),
            Link.is_active == True
        )
    ))
    return result.scalars().first()


async def get_multi(
    db: AsyncSession, *, user_id: Optional[int] = None, skip: int = 0, limit: int = 100
) -> List[Link]:
    query = select(Link).offset(skip).limit(limit)
    if user_id:
        query = query.where(Link.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()


async def search_by_original_url(
    db: AsyncSession, *, original_url: str, user_id: Optional[int] = None
) -> List[Link]:
    query = select(Link).where(Link.original_url == original_url)
    if user_id:
        query = query.where(Link.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()


async def create(
    db: AsyncSession, *, obj_in: LinkCreate, user: Optional[User] = None, 
    custom_short_code: Optional[str] = None
) -> Link:
    short_code = custom_short_code or obj_in.custom_alias
    
    # Если не задан кастомный код, генерируем случайный
    if not short_code:
        while True:
            short_code = generate_short_code(settings.SHORT_CODE_LENGTH)
            # Проверяем, что такой код не существует
            result = await db.execute(select(Link).where(Link.short_code == short_code))
            if not result.scalars().first():
                break
    else:
        # Проверяем, что такой кастомный код не существует
        result = await db.execute(select(Link).where(Link.short_code == short_code))
        if result.scalars().first():
            raise ValueError(f"Короткий код '{short_code}' уже используется")
    
    # Используем переданное время истечения или глобальную настройку
    from datetime import datetime, timedelta
    expires_at = obj_in.expires_at
    
    # Если время истечения не указано, используем глобальную настройку
    if expires_at is None:
        expires_at = datetime.now() + timedelta(days=settings.LINK_EXPIRATION_DAYS)
    
    db_obj = Link(
        original_url=obj_in.original_url,
        short_code=short_code,
        user_id=user.id if user else None,
        expires_at=expires_at,
        is_anonymous=user is None,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update(
    db: AsyncSession, *, db_obj: Link, obj_in: Union[LinkUpdate, Dict[str, Any]]
) -> Link:
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)
    
    for field in update_data.keys():
        if field in update_data:
            setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def remove(db: AsyncSession, *, link_id: int) -> Optional[Link]:
    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalars().first()
    if link:
        await db.delete(link)
        await db.commit()
    return link


async def remove_by_short_code(db: AsyncSession, *, short_code: str, user_id: Optional[int] = None) -> Optional[Link]:
    query = select(Link).where(Link.short_code == short_code)
    if user_id is not None:
        query = query.where(Link.user_id == user_id)
    
    result = await db.execute(query)
    link = result.scalars().first()
    if link:
        await db.delete(link)
        await db.commit()
    return link


async def increment_clicks(db: AsyncSession, link: Link) -> Link:
    link.clicks += 1
    link.last_used_at = datetime.now()
    await db.commit()
    await db.refresh(link)
    return link


async def remove_expired_links(db: AsyncSession) -> int:
    """Удаляет все истекшие ссылки"""
    query = delete(Link).where(
        and_(
            Link.expires_at != None,
            Link.expires_at < datetime.now()
        )
    )
    result = await db.execute(query)
    await db.commit()
    return result.rowcount


async def count_links(db: AsyncSession, user_id: Optional[int] = None) -> int:
    """Подсчитывает количество ссылок пользователя"""
    query = select(func.count(Link.id))
    if user_id:
        query = query.where(Link.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one() 