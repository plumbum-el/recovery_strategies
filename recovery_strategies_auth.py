"""ЛР4: Redis-сессии с HttpOnly cookie, без фиктивного пользователя."""
import os
import hmac
from hashlib import pbkdf2_hmac
from secrets import token_urlsafe
from fastapi import Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session
import redis
from database import get_db
from models import User

SESSION_COOKIE = 'recovery_session'
SESSION_TTL = 60 * 60 * 8
REDIS_URL = os.getenv('RECOVERY_REDIS_URL', 'redis://localhost:6379/0')

def redis_client():
    return redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=3)

def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        algorithm, rounds, salt, expected = stored.split('$')
        if algorithm != 'pbkdf2_sha256':
            return False
        actual = pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False

def create_session(response: Response, user_id: int):
    token = token_urlsafe(32)
    try:
        redis_client().setex(f'recovery:session:{token}', SESSION_TTL, str(user_id))
    except redis.RedisError:
        raise HTTPException(503, 'Redis недоступен: запустите docker compose up -d')
    response.set_cookie(SESSION_COOKIE, token, max_age=SESSION_TTL,
                        httponly=True, secure=False, samesite='lax', path='/')
    return token

def clear_session(response: Response, token: str | None):
    if token:
        try:
            redis_client().delete(f'recovery:session:{token}')
        except redis.RedisError:
            raise HTTPException(503, 'Redis недоступен')
    response.delete_cookie(SESSION_COOKIE, path='/')

def optional_user_id(recovery_session: str | None = Cookie(None, alias=SESSION_COOKIE),
                     db: Session = Depends(get_db)) -> int | None:
    if not recovery_session:
        return None
    try:
        value = redis_client().get(f'recovery:session:{recovery_session}')
    except redis.RedisError:
        raise HTTPException(503, 'Redis недоступен')
    if not value:
        return None
    try:
        user_id = int(value)
    except ValueError:
        return None
    if db.get(User, user_id) is None:
        return None
    return user_id

def require_user_id(user_id: int | None = Depends(optional_user_id)) -> int:
    if user_id is None:
        raise HTTPException(status_code=401, detail='Требуется вход в систему')
    return user_id
