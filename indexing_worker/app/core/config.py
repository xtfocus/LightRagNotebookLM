import os
import warnings
from typing import Any

from pydantic import PostgresDsn
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./indexing_worker/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    
    # Project Configuration
    PROJECT_NAME: str = "Indexing Worker"
    ENVIRONMENT: str = "local"
    
    # Database Configuration (for document status updates)
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # MinIO Configuration (for file retrieval)
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ROOT_USER: str = os.getenv("MINIO_ROOT_USER", "admin")
    MINIO_ROOT_PASSWORD: str = os.getenv("MINIO_ROOT_PASSWORD", "changeme")
    MINIO_BUCKET: str = "app-docs"

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_EXTERNAL_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_EXTERNAL_BOOTSTRAP_SERVERS", "localhost:9094")
    KAFKA_TOPIC_SOURCE_CHANGES: str = "source_changes"

    # Qdrant Configuration
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION_NAME: str = "documents"

    # OpenAI Configuration
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
    OPENAI_EMBEDDING_DIMENSION: int = int(os.getenv("OPENAI_EMBEDDING_DIMENSION", "1536"))

    # Indexing Worker Configuration
    INDEXING_WORKER_BATCH_SIZE: int = int(os.getenv("INDEXING_WORKER_BATCH_SIZE", "10"))
    INDEXING_WORKER_POLL_INTERVAL: int = int(os.getenv("INDEXING_WORKER_POLL_INTERVAL", "5"))
    INDEXING_WORKER_CHUNK_SIZE: int = int(os.getenv("INDEXING_WORKER_CHUNK_SIZE", "1000"))
    INDEXING_WORKER_CHUNK_OVERLAP: int = int(os.getenv("INDEXING_WORKER_CHUNK_OVERLAP", "200"))

    # File Processing Limits
    MAX_PDF_SIZE_BYTES: int = int(os.getenv("MAX_PDF_SIZE_BYTES", "10485760"))   # 10MB default
    MAX_DOCX_SIZE_BYTES: int = int(os.getenv("MAX_DOCX_SIZE_BYTES", "10485760"))  # 10MB default
    MAX_TXT_SIZE_BYTES: int = int(os.getenv("MAX_TXT_SIZE_BYTES", "10485760"))    # 10MB default
    MIN_FILE_SIZE_BYTES: int = int(os.getenv("MIN_FILE_SIZE_BYTES", "100"))       # 100 bytes minimum
    
    # URL Processing Configuration
    URL_PROCESSING_TIMEOUT_SECONDS: int = int(os.getenv("URL_PROCESSING_TIMEOUT_SECONDS", "25"))
    
    # Text Processing Configuration
    MAX_BINARY_NULL_RATIO: float = float(os.getenv("MAX_BINARY_NULL_RATIO", "0.1"))  # 10% null bytes threshold

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    def _enforce_non_default_secrets(self) -> None:
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)


settings = Settings()  # type: ignore
settings._enforce_non_default_secrets()
