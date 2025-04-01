from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query, status, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import valkey.asyncio as redis

from app.core.config import settings
from app.core.deps import get_db, get_current_active_user, get_optional_current_user
from app.db.redis import get_redis
from app.models.user import User
from app.crud import link as link_crud
from app.schemas.link import Link, LinkCreate, LinkUpdate, LinkStats, LinkSearch

router = APIRouter()

@router.get("/{short_code}", 
          summary="Переход по короткой ссылке",
          description="Перенаправляет на оригинальный URL по короткому коду")
async def redirect_to_original_url(
    short_code: str = Path(..., description="Короткий код ссылки (например, 'abc123')"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> Any:
    """Перенаправление на оригинальный URL по короткому коду"""
    cached_url = await redis_client.get(f"link:{short_code}")
    if cached_url:
        link = await link_crud.get_by_short_code(db, short_code=short_code)
        if link:
            await link_crud.increment_clicks(db, link)
        
        url = cached_url.decode() if isinstance(cached_url, bytes) else cached_url
        return RedirectResponse(url=url)
    
    link = await link_crud.get_by_short_code(db, short_code=short_code)
    if not link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена или срок ее действия истек",
        )
    
    await link_crud.increment_clicks(db, link)
    await redis_client.setex(f"link:{short_code}", 3600, link.original_url)
    
    return RedirectResponse(url=link.original_url)

@router.post("/shorten", response_model=Link,
          summary="Создание короткой ссылки (доступно без авторизации)",
          description="Создаёт короткую ссылку для оригинального URL. Можно указать срок действия ссылки.")
async def create_short_link(
    link_in: LinkCreate = Body(..., example={
        "original_url": "https://www.example.com/very/long/url/that/needs/shortening",
        "custom_alias": "mylink",
        "expires_at": "2023-12-31T23:59:00Z"
    }),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Any:
    """Создание короткой ссылки для оригинального URL"""
    try:
        link = await link_crud.create(db=db, obj_in=link_in, user=current_user)
        setattr(link, "short_url", f"{settings.BASE_URL}/{link.short_code}")
        return link
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

@router.get("/search", response_model=List[LinkSearch],
          summary="Поиск ссылки по URL",
          description="Ищет короткие ссылки по оригинальному URL")
async def search_link(
    original_url: str = Query(..., description="Оригинальный URL для поиска"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Any:
    """Поиск короткой ссылки по оригинальному URL"""
    links = await link_crud.search_by_original_url(
        db, original_url=original_url, 
        user_id=current_user.id if current_user else None
    )
    
    if not current_user:
        links = [link for link in links if link.is_anonymous]
    
    return links

@router.get("/{short_code}", response_model=Link,
          summary="Получение информации о ссылке",
          description="Возвращает детальную информацию о короткой ссылке")
async def get_link_info(
    short_code: str = Path(..., description="Короткий код ссылки"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Any:
    """Получение информации о короткой ссылке"""
    link = await link_crud.get_by_short_code(db, short_code=short_code)
    if not link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )
    
    if link.user_id and current_user and link.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="У вас нет доступа к этой ссылке",
        )
    
    setattr(link, "short_url", f"{settings.BASE_URL}/{link.short_code}")
    return link

@router.get("/{short_code}/stats", response_model=LinkStats,
          summary="Статистика по ссылке",
          description="Возвращает статистику использования короткой ссылки")
async def get_link_stats(
    short_code: str = Path(..., description="Короткий код ссылки"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Any:
    """Получение статистики использования короткой ссылки"""
    link = await link_crud.get_by_short_code(db, short_code=short_code)
    if not link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )
    
    if not current_user and not link.is_anonymous:
        raise HTTPException(
            status_code=403,
            detail="Для получения статистики по этой ссылке необходимо авторизоваться",
        )
    
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

@router.put("/{short_code}", response_model=Link,
          summary="Обновление ссылки",
          description="Обновляет оригинальный URL для существующей короткой ссылки")
async def update_link(
    short_code: str = Path(..., description="Короткий код ссылки"),
    link_in: LinkUpdate = Body(..., example={"original_url": "https://www.new-example.com/updated/url"}),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Обновление оригинального URL для короткой ссылки"""
    link = await link_crud.get_by_short_code(db, short_code=short_code)
    if not link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )
    
    if link.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="У вас нет прав для обновления этой ссылки",
        )
    
    link = await link_crud.update(db=db, db_obj=link, obj_in=link_in)
    
    if link_in.original_url:
        await redis_client.setex(f"link:{short_code}", 3600, link.original_url)
    
    setattr(link, "short_url", f"{settings.BASE_URL}/{link.short_code}")
    return link

@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT,
             summary="Удаление ссылки",
             description="Удаляет короткую ссылку")
async def delete_link(
    short_code: str = Path(..., description="Короткий код ссылки для удаления"),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """Удаление короткой ссылки"""
    link = await link_crud.get_by_short_code(db, short_code=short_code)
    if not link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )
    
    if link.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="У вас нет прав для удаления этой ссылки",
        )
    
    await link_crud.remove_by_short_code(db, short_code=short_code)
    await redis_client.delete(f"link:{short_code}")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.delete("/cleanup", status_code=status.HTTP_200_OK,
             summary="Удаление истекших ссылок",
             description="Удаляет все истекшие ссылки из базы данных (только для администраторов)")
async def cleanup_unused_links(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Удаление всех истекших ссылок из базы данных"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="У вас нет прав для выполнения этой операции",
        )
    
    deleted_count = await link_crud.remove_expired_links(db)
    return {"deleted_count": deleted_count} 