# URL Cutter

Сервис для сокращения длинных URL-адресов с возможностью:
- Создания коротких ссылок без авторизации
- Указания срока действия ссылок
- Просмотра статистики переходов
- Управления ссылками через API

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone git@github.com:tayar902/url_cutter.git
cd url-cutter
```

2. Установите зависимости:
```bash

pip install -r requirements.txt
```

3. Создайте файл `.env` и настройте переменные окружения:

4. Запустите приложение:
```bash
uvicorn app.main:app --reload
```

Приложение будет доступно по адресу: http://localhost:8000

## API Endpoints

### Публичные эндпоинты (без авторизации)
- `POST /api/v1/links/shorten` - Создание короткой ссылки
- `GET /{short_code}` - Переход по короткой ссылке

### Защищенные эндпоинты (требуется авторизация)
- `POST /api/v1/auth/register` - Регистрация
- `POST /api/v1/auth/login` - Вход
- `GET /api/v1/links/search` - Поиск ссылок
- `GET /api/v1/links/{short_code}` - Информация о ссылке
- `GET /api/v1/links/{short_code}/stats` - Статистика переходов
- `PUT /api/v1/links/{short_code}` - Обновление ссылки
- `DELETE /api/v1/links/{short_code}` - Удаление ссылки

## Документация API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 