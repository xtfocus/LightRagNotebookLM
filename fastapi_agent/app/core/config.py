import secrets
from typing import Any, Literal, Annotated
from pydantic import AnyUrl, BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    """
    Parse the BACKEND_CORS_ORIGINS environment variable.
    Accepts either a comma-separated string or a list of URLs.
    Returns a list of origins for FastAPI CORS middleware.
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Config(BaseSettings):
    """
    Application configuration using Pydantic BaseSettings.
    Loads environment variables and provides type validation for all config fields.

    Attributes:
        AGENT_API_PREFIX: The API version prefix for all routes (from env AGENT_API_PREFIX).
        SECRET_KEY: Secret key for cryptographic operations (e.g., JWT, session).
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time in minutes.
        ENVIRONMENT: Deployment environment (local, staging, production).
        BACKEND_CORS_ORIGINS: Allowed CORS origins (list of URLs or comma-separated string).
        LANGGRAPHDB_URI: Database URI for LangGraph checkpointing or other DB needs.
    """
    model_config = SettingsConfigDict(
        env_file="../.env",  # Path to the .env file (relative to this file)
        env_ignore_empty=True,  # Ignore empty environment variables
        extra="ignore",  # Ignore extra fields not defined in the model
    )
    AGENT_API_PREFIX: str = "/api/v1"  # API version prefix, from env AGENT_API_PREFIX
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Secure secret key for the app
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"  # Deployment environment
    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []  # CORS origins

    # Postgres connection fields
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "langgraph"

    @property
    def LANGGRAPHDB_URI(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}?sslmode=disable"
        )
    # Keep the old LANGGRAPHDB_URI for backward compatibility if needed
    # LANGGRAPHDB_URI: str = "postgresql://user:pass@localhost/db"  # Database URI
    # Add more config fields as needed, following the same pattern


config = Config() 