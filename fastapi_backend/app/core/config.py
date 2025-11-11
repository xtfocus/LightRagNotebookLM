import os
import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (AnyUrl, BeforeValidator, EmailStr, HttpUrl, PostgresDsn,
                      computed_field, model_validator, Field, field_validator)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    BACKEND_API_PREFIX: str = os.getenv("BACKEND_API_PREFIX", "/api/v1")
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = os.getenv("FRONTEND_HOST", "http://localhost:5173")
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = (
        []
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        """Get CORS origins with proper handling of quoted and multi-line values."""
        cors_origins = self.BACKEND_CORS_ORIGINS
        if isinstance(cors_origins, str):
            # Handle quoted strings and multi-line values
            cors_origins = cors_origins.strip().strip('"').strip("'")
            if cors_origins:
                return [str(origin).rstrip("/") for origin in cors_origins.split(",") if origin.strip()]
        elif isinstance(cors_origins, list):
            return [str(origin).rstrip("/") for origin in cors_origins]
        
        # Fallback to just the frontend host
        return [self.FRONTEND_HOST]

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
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

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_file_size_human(self) -> str:
        """Human-readable maximum file size."""
        return self._bytes_to_human_readable(self.MAX_FILE_SIZE_BYTES)
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_total_upload_size_human(self) -> str:
        """Human-readable maximum total upload size."""
        return self._bytes_to_human_readable(self.MAX_TOTAL_UPLOAD_SIZE_BYTES)
    
    def _bytes_to_human_readable(self, bytes_value: int) -> str:
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}TB"

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

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

    # File Upload Configuration
    # Granular file size limits (matching indexing worker)
    MAX_PDF_SIZE_BYTES: int = int(os.getenv("MAX_PDF_SIZE_BYTES", "10485760"))   # 10MB default
    MAX_DOCX_SIZE_BYTES: int = int(os.getenv("MAX_DOCX_SIZE_BYTES", "10485760"))  # 10MB default
    MAX_TXT_SIZE_BYTES: int = int(os.getenv("MAX_TXT_SIZE_BYTES", "10485760"))    # 10MB default
    MIN_FILE_SIZE_BYTES: int = int(os.getenv("MIN_FILE_SIZE_BYTES", "100"))       # 100 bytes minimum
    
    # Legacy support - use the highest limit as fallback
    MAX_FILE_SIZE_BYTES: int = int(os.getenv("MAX_FILE_SIZE_BYTES", "104857600"))  # 100MB default (legacy)
    MAX_TOTAL_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_TOTAL_UPLOAD_SIZE_BYTES", "524288000"))  # 500MB default
    
    # File type configuration: read raw string env; parse via computed property to avoid JSON decoding
    ALLOWED_FILE_TYPES_RAW: str = os.getenv(
        "ALLOWED_FILE_TYPES",
        "pdf,doc,docx,txt,md,csv,xlsx,xls,ppt,pptx",
    )

    @property
    def ALLOWED_FILE_TYPES(self) -> list[str]:
        raw = (self.ALLOWED_FILE_TYPES_RAW or "").strip().strip('"').strip("'")
        if not raw:
            raw = "pdf,doc,docx,txt,md,csv,xlsx,xls,ppt,pptx"
        return [t.strip() for t in raw.split(",") if t.strip()]
    
    # URL Processing Configuration
    URL_PROCESSING_TIMEOUT_SECONDS: int = int(os.getenv("URL_PROCESSING_TIMEOUT_SECONDS", "25"))
    
    # Text Processing Configuration
    MAX_BINARY_NULL_RATIO: float = float(os.getenv("MAX_BINARY_NULL_RATIO", "0.1"))  # 10% null bytes threshold
    
    # Source Management Configuration
    MAX_CONCURRENT_PROCESSING_PER_USER: int = int(os.getenv("MAX_CONCURRENT_PROCESSING_PER_USER", "5"))  # Maximum files processing simultaneously per user

    # Retry Configuration
    # MinIO Retry Settings
    MINIO_RETRY_MAX_ATTEMPTS: int = int(os.getenv("MINIO_RETRY_MAX_ATTEMPTS", "3"))
    MINIO_RETRY_BASE_DELAY: float = float(os.getenv("MINIO_RETRY_BASE_DELAY", "1.0"))  # seconds
    MINIO_RETRY_MAX_DELAY: float = float(os.getenv("MINIO_RETRY_MAX_DELAY", "10.0"))  # seconds
    MINIO_RETRY_MULTIPLIER: float = float(os.getenv("MINIO_RETRY_MULTIPLIER", "2.0"))
    
    # Kafka Retry Settings
    KAFKA_RETRY_MAX_ATTEMPTS: int = int(os.getenv("KAFKA_RETRY_MAX_ATTEMPTS", "5"))
    KAFKA_RETRY_BASE_DELAY: float = float(os.getenv("KAFKA_RETRY_BASE_DELAY", "1.0"))  # seconds
    KAFKA_RETRY_MAX_DELAY: float = float(os.getenv("KAFKA_RETRY_MAX_DELAY", "60.0"))  # seconds
    KAFKA_RETRY_MULTIPLIER: float = float(os.getenv("KAFKA_RETRY_MULTIPLIER", "2.0"))
    
    # Database Retry Settings
    DB_RETRY_MAX_ATTEMPTS: int = int(os.getenv("DB_RETRY_MAX_ATTEMPTS", "5"))
    DB_RETRY_BASE_DELAY: float = float(os.getenv("DB_RETRY_BASE_DELAY", "1.0"))  # seconds
    DB_RETRY_MAX_DELAY: float = float(os.getenv("DB_RETRY_MAX_DELAY", "30.0"))  # seconds
    DB_RETRY_MULTIPLIER: float = float(os.getenv("DB_RETRY_MULTIPLIER", "2.0"))

    # Directory for fake project metadata JSON files (can be overridden by env)
    # Deprecated: business-specific seed directories removed for template
    FAKE_PROJECT_METADATA_DIR: str = "/dev/null"
    FAKE_PROJECT_DOCS_DIR: str = "/dev/null"

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

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


# Add logging to debug settings initialization
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    logger.debug("Initializing Settings...")
    settings = Settings()  # type: ignore
    logger.debug("Settings initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Settings: {e}")
    logger.error(f"Exception type: {type(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise
