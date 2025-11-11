from sqlmodel import Session, create_engine, SQLModel
from minio import Minio
from loguru import logger
from contextlib import contextmanager

from app.core.config import settings

# Create database engine
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

@contextmanager
def get_session():
    """Get a database session."""
    with Session(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

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
