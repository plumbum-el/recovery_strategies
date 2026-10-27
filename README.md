# ЛР №4 — Recovery Strategies: cookie-сессии и Redis

## Что изменено

- `POST /api/users/register`: регистрация, пароль хранится в виде PBKDF2-SHA256 хеша.
- `POST /api/users/login`: проверка пароля, создание Redis-сессии на 8 часов и cookie `recovery_session` (HttpOnly, SameSite=Lax).
- `POST /api/users/logout`: удаление сессии из Redis и cookie.
- `GET /api/users/me`: проверка входа.
- Публичные GET каталога, ленты, файлов доступны без cookie.
- GET черновика, POST создания, PUT публикации, DELETE и POST лайка требуют действующую сессию (иначе HTTP 401).
- Автор создаваемой стратегии устанавливается сервером из Redis-сессии; чужие стратегии нельзя удалять.
- HTML-страница `/recovery_strategies/login` добавлена; HTML-методы изменения также защищены.
- Все остальные страницы ЛР2/ЛР3 сохранены. Порт FastAPI: 8000.

## Запуск в Windows PowerShell

1. Откройте Docker Desktop.
2. В папке проекта выполните `docker compose up -d` (НЕ используйте `down -v` — это удалит данные PostgreSQL).
3. Выполните `python -m pip install -r recovery_strategies_requirements.txt`.
4. Выполните `python -m uvicorn main:app --reload --port 8000`.
5. Откройте http://127.0.0.1:8000/docs, в режиме инкогнито.

Redis: `docker exec -it recovery_strategies_redis redis-cli`. Список сессий: `SCAN 0 MATCH recovery:session:* COUNT 100`; значение конкретного ключа: `GET recovery:session:<token>` (токен копируется из cookie браузера). TTL: `TTL recovery:session:<token>`.

### Как сделать скриншоты 1–9

1. В инкогнито Swagger POST `/api/users/login` с учётными данными ранее зарегистрированного пользователя; нажать `Execute`. В ответе 200 и `Set-Cookie`.
2. Swagger GET `/api/recovery_strategies`, нажать `Execute`, увидеть список опубликованных стратегий.
3. Chrome DevTools → Application → Cookies → `http://127.0.0.1:8000` → `recovery_session`, показать значение cookie (не публиковать в открытом интернете).
4. Postman GET `/api/recovery_strategies` **без Cookie**: 200.
5. Postman GET `/api/recovery_strategies` **с Cookie**: 200. Заголовок `Cookie: recovery_session=<значение>`.
6. Postman PUT `/api/recovery_strategies/draft/publish` без Cookie: 401.
7. Postman PUT с Cookie, JSON `{"estimated_time":55,"cost":102,"short_description":"Публикация через Redis-сессию"}`: 200, статус `published`. Сначала создать черновик через POST `/api/recovery_strategies` с Cookie и multipart файлами; если уже есть черновик — используйте его.
8. CMD: `docker exec -it recovery_strategies_redis redis-cli`, затем `SCAN 0 MATCH recovery:session:* COUNT 100`, `GET recovery:session:<token>`; ответ — числовой ID пользователя.
9. StarUML: диаграмма последовательности, у сообщений `signature` должен ссылаться на операции из диаграммы классов. В ZIP есть редактируемый шаблон `recovery_strategies_sequence.drawio` для ориентира; это НЕ файл StarUML и НЕ доказывает переиспользование `signature`.

### Примечания

- `Secure=False` у cookie допустимо **только для локального HTTP**. Для развёртывания на HTTPS установите `secure=True`, используйте отдельные пароли БД и Redis и ограничьте доступ к Redis.
- После перезапуска Redis сессии сохраняются через AOF в Docker volume `redis-data`.
- Старые пользователи без `password_hash` не смогут войти, зарегистрируйте нового через `/api/users/register`.
- В Swagger кнопка `Authorize` для cookie не обязательна: cookie браузера автоматически отправляется на тот же домен после входа.
- Полный РПЗ и отчёт со скриншотами нужно составлять по реальным результатам запуска. 
