# Recovery Strategies — лабораторная работа №3

Проект продолжает ЛР №2. Старые HTML-страницы доступны по `/recovery_strategies/feed`, `/recovery_strategies/catalog`, `/recovery_strategies/draft`; новый REST API имеет префикс `/api`. БД та же — PostgreSQL `recovery_strategies_db`, ORM SQLAlchemy. Документация Swagger: `http://127.0.0.1:8000/docs`.

## Запуск

1. Запустить Docker Desktop и контейнеры PostgreSQL, Adminer и MinIO. PostgreSQL: `localhost:5433`; Adminer: `localhost:8080`; MinIO API: `localhost:9000`, консоль: `localhost:9001`.
2. В MinIO создать bucket `recovery-strategies` (если отсутствует); учётные данные по умолчанию для локальной ЛР: `minioadmin` / `minioadmin`. В реальном окружении поменять пароль.
3. В корне проекта: `python -m pip install -r recovery_strategies_requirements.txt`.
4. Запустить `python -m uvicorn main:app --reload --port 8000`.
5. Импортировать `recovery_strategies_postman_collection.json` в Postman. При необходимости изменить переменную `base_url`.

### Настройки MinIO (необязательные переменные окружения)
`RECOVERY_STRATEGIES_MINIO_ENDPOINT=localhost:9000`, `RECOVERY_STRATEGIES_MINIO_USER=minioadmin`, `RECOVERY_STRATEGIES_MINIO_PASSWORD=minioadmin`, `RECOVERY_STRATEGIES_BUCKET=recovery-strategies`.

## REST API (10 методов)

| Метод | URL | Данные | Результат |
|---|---|---|---|
| GET | `/api/recovery_strategies?search=&min_time=&max_time=` | query: поиск и диапазон минут | Список только `published`; `is_creator` 0/1 |
| GET | `/api/recovery_strategies/feed?id=&next=true` | query `id`, `next` необязательные | Одна опубликованная запись; `is_liked` 0/1; циклическая лента |
| GET | `/api/recovery_strategies/draft` | без id | Единственный черновик пользователя или 404 |
| POST | `/api/recovery_strategies` | multipart: `title` (текст), `image` (файл), `video` (файл) | Создаёт черновик; файлы в MinIO, латинские имена в БД; второй черновик → 409 |
| PUT | `/api/recovery_strategies/draft/publish` | JSON: `estimated_time`, `cost`, необязательное `short_description` | Только `draft` → `published`; время и стоимость обязательны |
| DELETE | `/api/recovery_strategies/{strategy_id}` | id в URL | Только своя запись; `status='deleted'`, без физического удаления |
| POST | `/api/recovery_strategies/{strategy_id}/like` | JSON `{"liked":1}` или `{"liked":0}` | Лайк/отмена; не создаёт дубликатов |
| POST | `/api/users/register` | JSON `{"username":"...","password":"..."}` | Новый пользователь; в БД хранится `password_hash` |
| POST | `/api/users/login` | JSON имя/пароль | Заглушка до ЛР4, не создаёт сессию |
| POST | `/api/users/logout` | без тела | Заглушка до ЛР4 |

Дополнительно: GET `/api/recovery_strategies/media/{filename}` отдаёт загруженные файлы из MinIO. В `image_url` и `video_url` новых записей хранится **имя объекта**, а не URL. Пример доступа: `/api/recovery_strategies/media/image_....png`.

## Таблицы БД

- **users**: `id` INTEGER PK; `username` VARCHAR(100) UNIQUE NOT NULL; `password_hash` VARCHAR(255) NULL (старые пользователи могут не иметь пароля).
- **recovery_strategies**: `id` INTEGER PK; `title` VARCHAR(150) NOT NULL; `short_description` VARCHAR(500) NULL; `status` VARCHAR(20) NOT NULL (`draft`, `published`, `deleted`); `image_url` VARCHAR(500) NULL; `video_url` VARCHAR(500) NULL; `estimated_time` INTEGER NULL; `cost` INTEGER NULL; `created_at` TIMESTAMP NOT NULL; `published_at` TIMESTAMP NULL; `creator_id` INTEGER FK(users.id) NOT NULL.
- **recovery_strategy_likes**: `id` INTEGER PK; `user_id` INTEGER FK(users.id) NOT NULL; `recovery_strategy_id` INTEGER FK(recovery_strategies.id) NOT NULL.

## Бизнес-правила и безопасность

- В ЛР3 текущий создатель фиксирован: `CURRENT_CREATOR_ID = 1` через `@lru_cache(maxsize=1)` singleton `current_user_singleton()` и зависимость `current_user_id()`.
- `id`, `status`, `creator_id`, `created_at`, `published_at` не принимаются от клиента при создании/публикации.
- Нельзя вернуть опубликованную запись в черновик. Удалённые записи не выдаются каталогом и лентой. Для удаления требуется совпадение владельца.
- Весь доступ к PostgreSQL в API осуществляется через ORM. Существующий SQL-курсор в HTML-маршруте ЛР2 оставлен ради демонстрации предыдущей лабораторной.
- Регистрация хеширует пароль PBKDF2-SHA256 с индивидуальной солью. Авторизация и деавторизация пока **заглушки**, не проверяют доступ — реальная защита появится в ЛР4.

## Порядок демонстрации

**Скриншоты 1–10 (Postman):** каталог с фильтром; создание multipart с файлами; GET черновика; PUT публикации; GET ленты без id; GET ленты с `id` и `next=true`; POST like; DELETE; POST регистрации; коллекция с 10 методами (login/logout можно показать в коллекции). Важно: сначала создать черновик, затем опубликовать. Для лайка/удаления подставить id созданной записи в переменную Postman `strategy_id`.

**11–13 (Adminer, SQL):**
```sql
SELECT id, title, status, image_url, video_url, estimated_time, cost, creator_id FROM recovery_strategies ORDER BY id DESC;
SELECT id, user_id, recovery_strategy_id FROM recovery_strategy_likes ORDER BY id DESC;
SELECT id, username, password_hash FROM users ORDER BY id DESC;
```
**14–15:** `models.py`, `recovery_strategies_schemas.py`. **16–17:** singleton и его использование в `recovery_strategies_api.py`; этот README. Дополнительно приложить диаграмму классов `recovery_strategies_class_diagram.drawio`.

## Контрольные вопросы (кратко)

- **Веб-сервис:** программный интерфейс для обмена данными по сети.
- **REST:** архитектурный стиль с ресурсными URL, стандартными HTTP-методами, stateless-запросами.
- **RPC:** вызов удалённой процедуры, акцент на действии/методе, а не на ресурсе.
- **HTTP-методы:** GET читает, POST создаёт/выполняет действие, PUT обновляет, DELETE удаляет; заголовки `Content-Type`, `Accept`, `Authorization`, `Cookie` задают метаданные.
- **HTTP:** 1.0, 1.1, 2, 3 (HTTP/3 использует QUIC).
- **HTTPS:** HTTP поверх TLS с шифрованием, проверкой подлинности сервера и целостностью данных.
- **OSI ISO:** 7 уровней: физический, канальный, сетевой, транспортный, сеансовый, представления, прикладной.

**Четвёртая страница:** детальная карточка `/recovery_strategies/{strategy_id}` с изображением, видео, описанием и параметрами. Из плитки доступна по ссылке «Подробнее».
