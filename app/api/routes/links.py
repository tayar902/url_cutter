from typing import Any, List, Optional
import logging
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import valkey.asyncio as redis

from app.db.session import get_db
from app.db.redis import get_redis
from app.core.config import settings
from app.core.deps import get_current_active_user, get_optional_current_user
from app.models.user import User
from app.schemas.link import Link, LinkCreate, LinkUpdate, LinkStats, LinkSearch
from app.crud import link as link_crud

router = APIRouter()
logger = logging.Logger('links_api')


# Редирект по короткой ссылке (публичный доступ)
@router.get("/{short_code}", 
          summary="Переход по короткой ссылке",
          description="Перенаправляет на оригинальный URL по короткому коду")
async def redirect_to_original_url(
    short_code: str = Path(..., description="Короткий код ссылки (например, 'abc123')"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> Any:
    """
    Перенаправление на оригинальный URL по короткому коду.
    
    - **short_code**: короткий код ссылки, созданной ранее
    
    При успешном поиске перенаправляет на оригинальный URL. Увеличивает счетчик кликов.
    Если ссылка не найдена или срок ее действия истек, возвращает ошибку 404.
    """
    # Сначала проверяем кэш Redis
    cached_url = await redis_client.get(f"link:{short_code}")
    logger.info(f'ABOBA')
    if cached_url:
        logger.info(f'Найден url в кэше: {cached_url}')
        link = await link_crud.get_by_short_code(db, short_code=short_code)
        if link:
            # Инкрементируем счетчик переходов и обновляем дату последнего использования
            await link_crud.increment_clicks(db, link)
        
        # Декодируем URL, если он в байтах, или используем как есть, если он уже строка
        url = cached_url.decode() if isinstance(cached_url, bytes) else cached_url
        return RedirectResponse(url=url)
    
    # Если нет в кэше, ищем в БД
    link = await link_crud.get_by_short_code(db, short_code=short_code)
    if not link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена или срок ее действия истек",
        )
    
    # Инкрементируем счетчик переходов и обновляем дату последнего использования
    await link_crud.increment_clicks(db, link)
    
    # Кэшируем URL в Redis на 1 час
    await redis_client.setex(f"link:{short_code}", 3600, link.original_url)
    
    return RedirectResponse(url=link.original_url)


# Создание короткой ссылки (публичный доступ)
@router.post("/links/shorten", response_model=Link,
          summary="Создание короткой ссылки (доступно без авторизации)",
          description="Создаёт короткую ссылку для оригинального URL. Можно указать срок действия ссылки.")
async def create_short_link(
    link_in: LinkCreate = Body(..., example={
        "original_url": "https://www.example.com/very/long/url/that/needs/shortening",
        "custom_alias": "mylink",
        "expires_at": "2026-12-31T23:59:00Z"
    }),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Any:
    """
    Создание короткой ссылки для оригинального URL.
    
    - **original_url**: исходный URL, который нужно сократить (обязательно)
    - **custom_alias**: пользовательский алиас для короткой ссылки (опционально)
    - **expires_at**: дата и время истечения срока действия ссылки в формате ISO 8601 (опционально)
    
    **Авторизация не требуется** - вы можете создавать короткие ссылки без регистрации и авторизации.
    Если вы авторизованы, ссылка будет привязана к вашему аккаунту.
    
    Если custom_alias не указан, будет сгенерирован случайный короткий код.
    
    Если expires_at не указан, срок действия ссылки будет установлен в {settings.LINK_EXPIRATION_DAYS} дней 
    с момента создания (глобальная настройка). После истечения срока действия ссылка автоматически станет недоступной.
    """
    try:
        link = await link_crud.create(db=db, obj_in=link_in, user=current_user)
        
        # Добавляем полный URL в ответ
        setattr(link, "short_url", f"{settings.BASE_URL}/{link.short_code}")
        
        return link
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


# Поиск ссылки по оригинальному URL
@router.get("/links/search", response_model=List[LinkSearch],
          summary="Поиск ссылки по URL",
          description="Ищет короткие ссылки по оригинальному URL")
async def search_link(
    original_url: str = Query(..., description="Оригинальный URL для поиска"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Any:
    """
    Поиск короткой ссылки по оригинальному URL.
    
    - **original_url**: оригинальный URL для поиска
    
    Возвращает список всех коротких ссылок, созданных для указанного оригинального URL.
    Если пользователь не авторизован, возвращает только анонимные ссылки.
    """
    links = await link_crud.search_by_original_url(
        db, original_url=original_url, 
        user_id=current_user.id if current_user else None
    )
    
    # Если пользователь не авторизован, возвращаем только анонимные ссылки
    if not current_user:
        links = [link for link in links if link.is_anonymous]
    
    return links


# Получение информации о ссылке
@router.get("/links/{short_code}", response_model=Link,
          summary="Получение информации о ссылке",
          description="Возвращает детальную информацию о короткой ссылке")
async def get_link_info(
    short_code: str = Path(..., description="Короткий код ссылки"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Any:
    """
    Получение информации о короткой ссылке.
    
    - **short_code**: короткий код ссылки
    
    Возвращает полную информацию о ссылке: оригинальный URL, дату создания,
    количество кликов и другие параметры.
    """
    link = await link_crud.get_by_short_code(db, short_code=short_code)
    if not link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )
    
    # Проверяем, принадлежит ли ссылка текущему пользователю
    if link.user_id and current_user and link.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="У вас нет доступа к этой ссылке",
        )
    
    # Добавляем полный URL в ответ
    setattr(link, "short_url", f"{settings.BASE_URL}/{link.short_code}")
    
    return link


# Получение статистики по ссылке
@router.get("/links/{short_code}/stats", response_model=LinkStats,
          summary="Статистика по ссылке",
          description="Возвращает статистику использования короткой ссылки")
async def get_link_stats(
    short_code: str = Path(..., description="Короткий код ссылки"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Any:
    """
    Получение статистики использования короткой ссылки.
    
    - **short_code**: короткий код ссылки
    
    Возвращает статистику по ссылке: количество переходов, дату создания, 
    дату последнего использования и другие параметры.
    """
    link = await link_crud.get_by_short_code(db, short_code=short_code)
    if not link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )
    
    # Анонимные пользователи могут получать статистику только по анонимным ссылкам
    if not current_user and not link.is_anonymous:
        raise HTTPException(
            status_code=403,
            detail="Для получения статистики по этой ссылке необходимо авторизоваться",
        )
    
    # Авторизованные пользователи могут получать статистику только по своим ссылкам
    if current_user and link.user_id and link.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="У вас нет доступа к статистике этой ссылки",
        )
    
    return {
        "original_url": link.original_url,
        "short_code": link.short_code,
        "short_url": f"{settings.BASE_URL}/{link.short_code}",
        "clicks": link.clicks,
        "created_at": link.created_at,
        "last_used_at": link.last_used_at,
        "expires_at": link.expires_at,
    }


# Обновление ссылки (только для авторизованных пользователей)
@router.put("/links/{short_code}", response_model=Link,
          summary="Обновление ссылки",
          description="Обновляет оригинальный URL для существующей короткой ссылки")
async def update_link(
    short_code: str = Path(..., description="Короткий код ссылки"),
    link_in: LinkUpdate = Body(..., example={"original_url": "https://www.new-example.com/updated/url"}),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Обновление оригинального URL для короткой ссылки.
    
    - **short_code**: короткий код ссылки, которую нужно обновить
    - **original_url**: новый оригинальный URL
    
    Доступно только для авторизованных пользователей, которые являются владельцами ссылки.
    """
    link = await link_crud.get_by_short_code(db, short_code=short_code)
    if not link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )
    
    # Проверяем, принадлежит ли ссылка текущему пользователю
    if link.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="У вас нет прав для обновления этой ссылки",
        )
    
    link = await link_crud.update(db=db, db_obj=link, obj_in=link_in)
    
    # Обновляем кэш в Redis
    if link_in.original_url:
        await redis_client.setex(f"link:{short_code}", 3600, link.original_url)
    
    # Добавляем полный URL в ответ
    setattr(link, "short_url", f"{settings.BASE_URL}/{link.short_code}")
    
    return link


# Удаление ссылки (только для авторизованных пользователей)
@router.delete("/links/{short_code}", status_code=status.HTTP_204_NO_CONTENT,
             summary="Удаление ссылки",
             description="Удаляет короткую ссылку")
async def delete_link(
    short_code: str = Path(..., description="Короткий код ссылки для удаления"),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    Удаление короткой ссылки.
    
    - **short_code**: короткий код ссылки, которую нужно удалить
    
    Доступно только для авторизованных пользователей, которые являются владельцами ссылки.
    При успешном удалении возвращает статус 204 No Content.
    """
    link = await link_crud.get_by_short_code(db, short_code=short_code)
    if not link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )
    
    # Проверяем, принадлежит ли ссылка текущему пользователю
    if link.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="У вас нет прав для удаления этой ссылки",
        )
    
    await link_crud.remove_by_short_code(db, short_code=short_code)
    
    # Удаляем из кэша Redis
    await redis_client.delete(f"link:{short_code}")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
