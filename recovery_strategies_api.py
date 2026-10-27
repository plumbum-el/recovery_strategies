"""REST API лабораторной №3: ORM, singleton, MinIO, бизнес-правила."""
from datetime import datetime
from functools import lru_cache
from hashlib import pbkdf2_hmac
from secrets import token_bytes
import hmac

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from minio.error import S3Error

from database import get_db
from models import User, RecoveryStrategy, RecoveryStrategyLike
from recovery_strategies_schemas import (
    StrategyResponse, PublishRequest, LikeRequest, RegisterRequest, LoginRequest
)
from recovery_strategies_storage import minio_client, BUCKET, save_upload, remove_upload

router = APIRouter(prefix='/api', tags=['Recovery Strategies REST API'])
CURRENT_CREATOR_ID = 1


@lru_cache(maxsize=1)
def current_user_singleton() -> int:
    """Единственный текущий пользователь в лабораторной №3."""
    return CURRENT_CREATOR_ID


def current_user_id() -> int:
    return current_user_singleton()


def strategy_data(item: RecoveryStrategy, db: Session, user_id: int) -> StrategyResponse:
    response = StrategyResponse.model_validate(item)
    response.is_creator = int(item.creator_id == user_id)
    response.is_liked = int(db.query(RecoveryStrategyLike.id).filter(
        RecoveryStrategyLike.recovery_strategy_id == item.id,
        RecoveryStrategyLike.user_id == user_id
    ).first() is not None)
    response.likes_count = db.query(func.count(RecoveryStrategyLike.id)).filter(
        RecoveryStrategyLike.recovery_strategy_id == item.id
    ).scalar() or 0
    return response


@router.get('/recovery_strategies', response_model=list[StrategyResponse], tags=['Strategies'])
def list_strategies(
    search: str | None = None,
    min_time: int | None = Query(None, ge=0),
    max_time: int | None = Query(None, ge=0),
    db: Session = Depends(get_db),
    user_id: int = Depends(current_user_id),
):
    """Опубликованные стратегии, поиск и фильтрация на сервере."""
    if min_time is not None and max_time is not None and min_time > max_time:
        raise HTTPException(422, 'min_time больше max_time')
    query = db.query(RecoveryStrategy).filter(RecoveryStrategy.status == 'published')
    if search and search.strip():
        query = query.filter(RecoveryStrategy.title.ilike(f'%{search.strip()}%'))
    if min_time is not None:
        query = query.filter(RecoveryStrategy.estimated_time >= min_time)
    if max_time is not None:
        query = query.filter(RecoveryStrategy.estimated_time <= max_time)
    return [strategy_data(item, db, user_id) for item in query.order_by(RecoveryStrategy.id).all()]


@router.get('/recovery_strategies/feed', response_model=StrategyResponse, tags=['Strategies'])
def get_feed(id: int | None = Query(None, ge=1), next: bool = False,
             db: Session = Depends(get_db), user_id: int = Depends(current_user_id)):
    query = db.query(RecoveryStrategy).filter(RecoveryStrategy.status == 'published')
    if id is None:
        item = query.order_by(RecoveryStrategy.id).first()
    elif next:
        item = query.filter(RecoveryStrategy.id > id).order_by(RecoveryStrategy.id).first()
        if item is None:
            item = query.order_by(RecoveryStrategy.id).first()
    else:
        item = query.filter(RecoveryStrategy.id == id).first()
    if item is None:
        raise HTTPException(404, 'Опубликованная стратегия не найдена')
    return strategy_data(item, db, user_id)


@router.get('/recovery_strategies/draft', response_model=StrategyResponse, tags=['Strategies'])
def get_draft(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)):
    item = db.query(RecoveryStrategy).filter(
        RecoveryStrategy.creator_id == user_id, RecoveryStrategy.status == 'draft'
    ).order_by(RecoveryStrategy.id).first()
    if item is None:
        raise HTTPException(404, 'Черновик отсутствует')
    return strategy_data(item, db, user_id)


@router.post('/recovery_strategies', response_model=StrategyResponse, status_code=201, tags=['Strategies'])
def create_draft(
    title: str = Form(..., min_length=1, max_length=150),
    image: UploadFile = File(...),
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(current_user_id),
):
    if not title.strip():
        raise HTTPException(422, 'Название обязательно')
    existing = db.query(RecoveryStrategy.id).filter(
        RecoveryStrategy.creator_id == user_id, RecoveryStrategy.status == 'draft'
    ).first()
    if existing:
        raise HTTPException(409, 'У пользователя уже есть черновик; опубликуйте его или удалите')
    image_name = save_upload(image, 'image')
    try:
        video_name = save_upload(video, 'video')
    except Exception:
        remove_upload(image_name)
        raise
    try:
        item = RecoveryStrategy(title=title.strip(), status='draft',
                                creator_id=user_id, created_at=datetime.now(),
                                image_url=image_name, video_url=video_name)
        db.add(item)
        db.commit()
        db.refresh(item)
    except Exception:
        db.rollback()
        remove_upload(image_name)
        remove_upload(video_name)
        raise
    return strategy_data(item, db, user_id)


@router.put('/recovery_strategies/draft/publish', response_model=StrategyResponse, tags=['Strategies'])
def publish_draft(payload: PublishRequest, db: Session = Depends(get_db),
                  user_id: int = Depends(current_user_id)):
    item = db.query(RecoveryStrategy).filter(
        RecoveryStrategy.creator_id == user_id, RecoveryStrategy.status == 'draft'
    ).order_by(RecoveryStrategy.id).first()
    if item is None:
        raise HTTPException(404, 'Черновик не найден; опубликованную стратегию вернуть в черновик нельзя')
    item.estimated_time = payload.estimated_time
    item.cost = payload.cost
    item.short_description = (payload.short_description or '').strip() or None
    item.status = 'published'
    item.published_at = datetime.now()
    db.commit()
    db.refresh(item)
    return strategy_data(item, db, user_id)


@router.delete('/recovery_strategies/{strategy_id}', tags=['Strategies'])
def delete_strategy(strategy_id: int, db: Session = Depends(get_db),
                    user_id: int = Depends(current_user_id)):
    item = db.query(RecoveryStrategy).filter(
        RecoveryStrategy.id == strategy_id,
        RecoveryStrategy.creator_id == user_id,
        RecoveryStrategy.status.in_(['draft', 'published'])
    ).first()
    if item is None:
        raise HTTPException(404, 'Своя активная стратегия не найдена')
    item.status = 'deleted'
    db.commit()
    return {'id': strategy_id, 'status': 'deleted', 'message': 'Логическое удаление выполнено'}


@router.post('/recovery_strategies/{strategy_id}/like', tags=['Strategies'])
def set_like(strategy_id: int, payload: LikeRequest,
             db: Session = Depends(get_db), user_id: int = Depends(current_user_id)):
    item = db.query(RecoveryStrategy.id).filter(
        RecoveryStrategy.id == strategy_id, RecoveryStrategy.status == 'published'
    ).first()
    if item is None:
        raise HTTPException(404, 'Опубликованная стратегия не найдена')
    existing = db.query(RecoveryStrategyLike).filter(
        RecoveryStrategyLike.user_id == user_id,
        RecoveryStrategyLike.recovery_strategy_id == strategy_id
    ).first()
    if payload.liked == 1 and existing is None:
        db.add(RecoveryStrategyLike(user_id=user_id, recovery_strategy_id=strategy_id))
    elif payload.liked == 0 and existing is not None:
        db.delete(existing)
    db.commit()
    return {'strategy_id': strategy_id, 'liked': payload.liked,
            'likes_count': db.query(func.count(RecoveryStrategyLike.id)).filter(
                RecoveryStrategyLike.recovery_strategy_id == strategy_id).scalar() or 0}


def hash_password(password: str) -> str:
    salt = token_bytes(16)
    digest = pbkdf2_hmac('sha256', password.encode(), salt, 300_000)
    return f'pbkdf2_sha256$300000${salt.hex()}${digest.hex()}'


@router.post('/users/register', status_code=201, tags=['Users'])
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    username = payload.username.strip()
    if len(username) < 3:
        raise HTTPException(422, 'Имя пользователя слишком короткое')
    if db.query(User.id).filter(User.username == username).first():
        raise HTTPException(409, 'Имя пользователя занято')
    user = User(username=username, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Имя пользователя занято')
    return {'id': user.id, 'username': user.username}


@router.post('/users/login', tags=['Users'])
def login_stub(payload: LoginRequest):
    """ЛР3: заглушка. Проверка пароля и сессии появятся в ЛР4."""
    return {'message': 'Заглушка авторизации: реализация в ЛР4', 'authenticated': False}


@router.post('/users/logout', tags=['Users'])
def logout_stub():
    """ЛР3: заглушка. Сессии появятся в ЛР4."""
    return {'message': 'Заглушка деавторизации: реализация в ЛР4', 'authenticated': False}


@router.get('/recovery_strategies/media/{filename}', tags=['Media'])
def get_media(filename: str):
    """Получение файла из закрытого bucket через API (имя хранится в БД)."""
    if not filename.startswith(('image_', 'video_')):
        raise HTTPException(404, 'Файл не найден')
    try:
        response = minio_client().get_object(BUCKET, filename)
    except S3Error:
        raise HTTPException(404, 'Файл не найден')
    except Exception as exc:
        raise HTTPException(503, f'MinIO недоступен: {exc}')
    mime = 'video/mp4' if filename.endswith('.mp4') else ('video/webm' if filename.endswith('.webm') else 'image/png' if filename.endswith('.png') else 'image/jpeg')
    def chunks():
        try:
            for chunk in response.stream(32 * 1024):
                yield chunk
        finally:
            response.close()
            response.release_conn()
    return StreamingResponse(chunks(), media_type=mime)
