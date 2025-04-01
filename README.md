# URL Cutter - Сервис сокращения ссылок

API-сервис для сокращения ссылок, аналогичный TinyURL или Bitly.

## Функциональность

### Основные функции:
- Создание, удаление, изменение и получение информации о коротких ссылках
- Статистика использования ссылок (клики, даты создания/использования)
- Кастомные короткие ссылки (пользовательский алиас)
- Поиск ссылок по оригинальному URL
- Настройка времени жизни ссылок

### Дополнительная функциональность:
- **Создание коротких ссылок без необходимости авторизации**
- Регистрация и авторизация для дополнительных возможностей управления ссылками
- Удаление истекших ссылок

## Технологии

- **Backend**: FastAPI, Python 3.13
- **База данных**: PostgreSQL для хранения ссылок и пользователей
- **Кэширование**: Valkey (совместимый с Redis форк)
- **Контейнеризация**: Docker & Docker Compose

## Срок действия ссылок

У всех ссылок есть срок действия. После истечения этого срока ссылки автоматически становятся недоступными.

### Настройка срока действия ссылок

Есть два способа настроить срок действия ссылок:

1. **Индивидуальная настройка:** При создании ссылки можно указать параметр `expires_at` с конкретной датой и временем истечения срока действия:

```json
{
  "original_url": "https://www.example.com/very/long/url",
  "custom_alias": "mylink",
  "expires_at": "2024-12-31T23:59:00Z"
}
```

2. **Глобальная настройка:** Если время `expires_at` не указано при создании ссылки, используется значение по умолчанию - 180 дней с момента создания. Это значение можно изменить в файле `app/core/config.py`:

```python
# Link settings
LINK_EXPIRATION_DAYS: int = 180  # Срок действия ссылок в днях
```

Администраторы могут вручную удалить все истекшие ссылки с помощью эндпоинта `DELETE /links/cleanup`.

## API Endpoints

### Публичные эндпоинты (без авторизации)

- `POST /links/shorten` - Создание короткой ссылки (с опциональным параметром expires_at)
- `GET /{short_code}` - Перенаправление по короткому коду

### Эндпоинты авторизации

- `POST /auth/register` - Регистрация нового пользователя (возвращает токен доступа)
- `POST /auth/login` - Получение токена доступа для существующего пользователя

### Эндпоинты управления ссылками (требуют авторизацию)

- `GET /links/{short_code}` - Получение информации о ссылке
- `GET /links/{short_code}/stats` - Получение статистики по ссылке
- `PUT /links/{short_code}` - Обновление ссылки
- `DELETE /links/{short_code}` - Удаление ссылки
- `GET /links/search?original_url={url}` - Поиск ссылки по оригинальному URL
- `DELETE /links/cleanup` - Удаление истекших ссылок (админ)

## Примеры запросов

### Создание короткой ссылки (без авторизации)
```bash
curl -X 'POST' \
  'http://localhost:8000/links/shorten' \
  -H 'Content-Type: application/json' \
  -d '{
  "original_url": "https://www.example.com/very/long/url/that/needs/shortening",
  "custom_alias": "mylink",
  "expires_at": "2024-12-31T23:59:00Z"
}'
```

### Регистрация пользователя
```bash
curl -X 'POST' \
  'http://localhost:8000/auth/register' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "username": "testuser",
  "password": "password123"
}'
# Ответ содержит токен доступа, который можно сразу использовать для запросов:
# {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"}
```

### Логин и получение токена
```bash
curl -X 'POST' \
  'http://localhost:8000/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=testuser&password=password123'
```

### Получение статистики (требует авторизации)
```bash
curl -X 'GET' \
  'http://localhost:8000/links/mylink/stats' \
  -H 'Authorization: Bearer {token}'
```

## Запуск проекта

### Предварительные требования
- Docker

### Шаги для запуска

1. Клонирование репозитория:
```bash
git clone https://github.com/yourusername/url_cutter.git
cd url_cutter
```

2. Запуск приложения с помощью Docker Compose:
```bash
docker compose up -d
```

3. Инициализация базы данных:
```bash
docker compose exec app python -m app.db.init_db
```

4. Сервис доступен по адресу: http://localhost:8000

## Структура базы данных

### Пользователи (User)
- id: Первичный ключ
- email: Уникальный email пользователя
- username: Уникальное имя пользователя
- hashed_password: Хэшированный пароль
- is_active: Флаг активности
- is_superuser: Флаг суперпользователя

### Ссылки (Link)
- id: Первичный ключ
- original_url: Оригинальный URL
- short_code: Уникальный короткий код
- user_id: Внешний ключ на пользователя (опционально)
- clicks: Счетчик кликов
- last_used_at: Время последнего использования
- expires_at: Время истечения ссылки (может быть указано пользователем или установлено по умолчанию)
- is_active: Флаг активности
- is_anonymous: Флаг анонимной ссылки 