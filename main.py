from datetime import datetime

from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import RecoveryStrategy, RecoveryStrategyLike


app = FastAPI(title="Recovery Strategies App")


# =========================================================
# СТАТИЧЕСКИЕ ФАЙЛЫ И ШАБЛОНЫ
# =========================================================

app.mount(
    "/recovery_strategies_static",
    StaticFiles(directory="recovery_strategies_static"),
    name="recovery_strategies_static"
)

templates = Jinja2Templates(
    directory="recovery_strategies_templates"
)

# Поддержка медиа из MinIO (ЛР3) и прежних URL (ЛР2).
def recovery_strategies_media_url(value, fallback):
    if not value:
        return fallback
    if value.startswith(('image_', 'video_')) and '/' not in value:
        return '/api/recovery_strategies/media/' + value
    return value

templates.env.globals['recovery_strategies_media_url'] = recovery_strategies_media_url



# =========================================================
# ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
# Авторизация в данной лабораторной не реализуется.
# Используем пользователя с id = 1.
# =========================================================

CURRENT_USER_ID = 1


# =========================================================
# ЛЕНТА
# GET /recovery_strategies/feed
#
# БД сразу возвращает только одну стратегию.
# =========================================================

@app.get("/")
@app.get("/recovery_strategies/feed")
def get_recovery_feed(
    request: Request,
    id: int | None = None,
    next: bool = False,
    db: Session = Depends(get_db)
):

    if id is None:
        recovery_strategy = (
            db.query(RecoveryStrategy)
            .filter(
                RecoveryStrategy.status == "published"
            )
            .order_by(RecoveryStrategy.id)
            .first()
        )

    elif next:
        recovery_strategy = (
            db.query(RecoveryStrategy)
            .filter(
                RecoveryStrategy.status == "published",
                RecoveryStrategy.id > id
            )
            .order_by(RecoveryStrategy.id)
            .first()
        )

        # Если дошли до конца — возвращаемся к первой карточке
        if recovery_strategy is None:
            recovery_strategy = (
                db.query(RecoveryStrategy)
                .filter(
                    RecoveryStrategy.status == "published"
                )
                .order_by(RecoveryStrategy.id)
                .first()
            )

    else:
        recovery_strategy = (
            db.query(RecoveryStrategy)
            .filter(
                RecoveryStrategy.id == id,
                RecoveryStrategy.status == "published"
            )
            .first()
        )

    # Удалённую или несуществующую карточку не показываем
    if recovery_strategy is None:
        return templates.TemplateResponse(
            request=request,
            name="recovery_feed.html",
            context={
                "recovery_strategy": None,
                "likes_count": 0
            },
            status_code=404
        )

    # Количество лайков получаем из БД через ORM
    likes_count = (
        db.query(func.count(RecoveryStrategyLike.id))
        .filter(
            RecoveryStrategyLike.recovery_strategy_id
            == recovery_strategy.id
        )
        .scalar()
    )

    return templates.TemplateResponse(
        request=request,
        name="recovery_feed.html",
        context={
            "recovery_strategy": recovery_strategy,
            "likes_count": likes_count
        }
    )



@app.get("/recovery_strategies/draft")
def get_recovery_draft(
    request: Request,
    db: Session = Depends(get_db)
):

    draft_recovery_strategy = (
        db.query(RecoveryStrategy)
        .filter(
            RecoveryStrategy.creator_id == CURRENT_USER_ID,
            RecoveryStrategy.status == "draft"
        )
        .first()
    )

    return templates.TemplateResponse(
        request=request,
        name="recovery_draft.html",
        context={
            "recovery_strategy": draft_recovery_strategy
        }
    )


# =========================================================
# ПЛИТКА
# GET /recovery_strategies/catalog
#
# Получение, фильтрация и поиск выполняются через ORM.
# =========================================================

@app.get("/recovery_strategies/catalog")
def get_recovery_catalog(
    request: Request,
    min_time: int | None = None,
    max_time: int | None = None,
    search: str | None = None,
    db: Session = Depends(get_db)
):

    # Минимальное и максимальное время среди опубликованных стратегий
    time_limits = (
        db.query(
            func.min(RecoveryStrategy.estimated_time),
            func.max(RecoveryStrategy.estimated_time)
        )
        .filter(
            RecoveryStrategy.status == "published"
        )
        .first()
    )

    absolute_min_time = time_limits[0] or 0
    absolute_max_time = time_limits[1] or 0

    selected_min_time = (
        min_time
        if min_time is not None
        else absolute_min_time
    )

    selected_max_time = (
        max_time
        if max_time is not None
        else absolute_max_time
    )

    # Без фильтров показываем все опубликованные стратегии, включая NULL во времени.
    query = db.query(RecoveryStrategy).filter(
        RecoveryStrategy.status == "published"
    )

    if min_time is not None:
        query = query.filter(RecoveryStrategy.estimated_time >= min_time)

    if max_time is not None:
        query = query.filter(RecoveryStrategy.estimated_time <= max_time)

    # Поиск по названию через ORM
    if search:
        query = query.filter(
            RecoveryStrategy.title.ilike(
                f"%{search.strip()}%"
            )
        )

    recovery_strategies = (
        query
        .order_by(RecoveryStrategy.id)
        .all()
    )

    # Количество лайков также получаем из БД
    for recovery_strategy in recovery_strategies:
        recovery_strategy.likes_count = (
            db.query(func.count(RecoveryStrategyLike.id))
            .filter(
                RecoveryStrategyLike.recovery_strategy_id
                == recovery_strategy.id
            )
            .scalar()
        )

    return templates.TemplateResponse(
        request=request,
        name="recovery_catalog.html",
        context={
            "recovery_strategies": recovery_strategies,
            "absolute_min_time": absolute_min_time,
            "absolute_max_time": absolute_max_time,
            "selected_min_time": selected_min_time,
            "selected_max_time": selected_max_time,
            "search": search or ""
        }
    )


# =========================================================
# СОЗДАНИЕ ЧЕРНОВИКА ЧЕРЕЗ ORM
# POST /recovery_strategies/draft/create
# =========================================================

@app.post("/recovery_strategies/draft/create")
def create_recovery_draft(
    title: str = Form(...),
    db: Session = Depends(get_db)
):

    # Проверяем, есть ли уже черновик у текущего пользователя
    existing_draft = (
        db.query(RecoveryStrategy)
        .filter(
            RecoveryStrategy.creator_id == CURRENT_USER_ID,
            RecoveryStrategy.status == "draft"
        )
        .first()
    )

    # Если черновика нет — создаём его через ORM
    if existing_draft is None:
        recovery_strategy = RecoveryStrategy(
            title=title,
            status="draft",
            creator_id=CURRENT_USER_ID,
            created_at=datetime.now()
        )

        db.add(recovery_strategy)
        db.commit()

    return RedirectResponse(
        url="/recovery_strategies/draft",
        status_code=303
    )


# =========================================================
# ПУБЛИКАЦИЯ ЧЕРНОВИКА ЧЕРЕЗ ORM
# POST /recovery_strategies/draft/publish
# =========================================================

@app.post("/recovery_strategies/draft/publish")
def publish_recovery_draft(
    short_description: str | None = Form(None),
    estimated_time: int = Form(..., ge=0),
    cost: int = Form(..., ge=0),
    db: Session = Depends(get_db)
):

    # Получаем черновик через ORM
    recovery_strategy = (
        db.query(RecoveryStrategy)
        .filter(
            RecoveryStrategy.creator_id == CURRENT_USER_ID,
            RecoveryStrategy.status == "draft"
        )
        .first()
    )

    # Заполняем поля и меняем статус на published
    if recovery_strategy is not None:
        recovery_strategy.short_description = short_description.strip() or None if short_description is not None else None
        recovery_strategy.estimated_time = estimated_time
        recovery_strategy.cost = cost

        recovery_strategy.status = "published"
        recovery_strategy.published_at = datetime.now()

        db.commit()

    return RedirectResponse(
        url="/recovery_strategies/catalog",
        status_code=303
    )


# =========================================================
# ЛОГИЧЕСКОЕ УДАЛЕНИЕ ЧЕРЕЗ SQL-КУРСОР
#
# ВАЖНО:
# ORM для изменения RecoveryStrategy здесь НЕ используется.
#
# Получаем DBAPI-соединение и создаём SQL-курсор:
# connection.cursor()
#
# Затем выполняем обычный SQL UPDATE через cursor.execute().
#
# POST /recovery_strategies/delete
# =========================================================

@app.post("/recovery_strategies/delete")
def delete_recovery_strategy(
    id: int = Form(...),
    db: Session = Depends(get_db)
):

    connection = db.connection().connection


    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE recovery_strategies
            SET status = 'deleted'
            WHERE id = %s
            """,
            (id,)
        )

        # Сохраняем изменение
        connection.commit()

    finally:
        # Закрываем курсор
        cursor.close()

    return RedirectResponse(
        url="/recovery_strategies/catalog",
        status_code=303
    )


# ЛР №3: REST API; старые страницы ЛР №2 остаются доступны.
from recovery_strategies_api import router as recovery_strategies_router
app.include_router(recovery_strategies_router)

# Четвёртая страница фронтенда для диаграммы классов ЛР3.
@app.get('/recovery_strategies/{strategy_id}', include_in_schema=False)
def get_recovery_strategies_detail(strategy_id: int, request: Request,
                                   db: Session = Depends(get_db)):
    item = db.query(RecoveryStrategy).filter(
        RecoveryStrategy.id == strategy_id,
        RecoveryStrategy.status == 'published'
    ).first()
    if item is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail='Стратегия не найдена')
    likes_count = db.query(func.count(RecoveryStrategyLike.id)).filter(
        RecoveryStrategyLike.recovery_strategy_id == item.id
    ).scalar() or 0
    return templates.TemplateResponse(request=request,
        name='recovery_strategies_detail.html',
        context={'recovery_strategy': item, 'likes_count': likes_count})
