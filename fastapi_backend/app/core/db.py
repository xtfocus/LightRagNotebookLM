from sqlmodel import Session, create_engine, select, SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
import json
from datetime import datetime
from minio import Minio
from loguru import logger

from app import crud
from app.core.config import settings
from app.models import User, UserCreate
from app.core.retry_utils import minio_retry

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

async_engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI).replace("+psycopg", "+asyncpg"), echo=True, future=True)
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


async def init_db(session: AsyncSession) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    result = await session.execute(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    )
    user = result.scalars().first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
            is_approved=True,  # Admin users are approved by default
        )
        user = await crud.create_user(session=session, user_create=user_in)

@minio_retry
def setup_minio_client():
    """
    Set up and return a MinIO client using configuration from settings.
    Ensures the target bucket exists (creates it if necessary).
    Returns the MinIO client and the bucket name.
    """
    logger.info(f"Setting up MinIO client for endpoint {settings.MINIO_ENDPOINT}...")
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=False
    )
    bucket_name = settings.MINIO_BUCKET
    if not minio_client.bucket_exists(bucket_name):
        logger.info(f"Bucket '{bucket_name}' does not exist. Creating...")
        minio_client.make_bucket(bucket_name)
        logger.info(f"Bucket '{bucket_name}' created.")
    else:
        logger.info(f"Bucket '{bucket_name}' already exists.")
    return minio_client, bucket_name
