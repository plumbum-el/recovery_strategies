"""Хранилище файлов MinIO для REST API."""
import os
from io import BytesIO
from uuid import uuid4
from pathlib import Path
from minio import Minio
from fastapi import HTTPException, UploadFile

BUCKET = os.getenv('RECOVERY_STRATEGIES_BUCKET', 'recovery-strategies')


def minio_client():
    return Minio(
        os.getenv('RECOVERY_STRATEGIES_MINIO_ENDPOINT', 'localhost:9000'),
        access_key=os.getenv('RECOVERY_STRATEGIES_MINIO_USER', 'minioadmin'),
        secret_key=os.getenv('RECOVERY_STRATEGIES_MINIO_PASSWORD', 'minioadmin'),
        secure=False,
    )


def save_upload(upload: UploadFile, kind: str) -> str:
    allowed = {'image': {'.jpg', '.jpeg', '.png', '.webp'},
               'video': {'.mp4', '.webm', '.mov'}}[kind]
    suffix = Path(upload.filename or '').suffix.lower()
    if suffix not in allowed:
        raise HTTPException(422, f'Недопустимый формат {kind}: {suffix}')
    mime = upload.content_type or ''
    if not mime.startswith(f'{kind}/'):
        raise HTTPException(422, f'Ожидался файл {kind}')
    data = upload.file.read(101 * 1024 * 1024)
    if not data or len(data) > 100 * 1024 * 1024:
        raise HTTPException(422, 'Файл должен быть непустым и не больше 100 МБ')
    name = f'{kind}_{uuid4().hex}{suffix}'  # только латиница
    client = minio_client()
    try:
        if not client.bucket_exists(BUCKET):
            client.make_bucket(BUCKET)
        client.put_object(BUCKET, name, BytesIO(data), len(data), content_type=mime)
    except Exception as exc:
        raise HTTPException(503, f'MinIO недоступен: {exc}') from exc
    return name


def remove_upload(name: str | None):
    if name:
        try:
            minio_client().remove_object(BUCKET, name)
        except Exception:
            pass
