"""
src/config.py — Centralized configuration via pydantic-settings
Membaca dari environment variables / .env file
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM (SumoPod API — OpenAI-compatible) ---
    llm_base_url: str = "https://api.sumopod.com/v1"
    llm_api_key: str = "your-sumopod-api-key"
    llm_model_name: str = "claude-3-haiku-20240307"

    # --- Embedding ---
    embedding_model_name: str = "text-embedding-3-small"
    embedding_base_url: str = "https://api.sumopod.com/v1"
    embedding_api_key: str = "your-sumopod-api-key"

    # --- PostgreSQL ---
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "omni_resolve"
    postgres_user: str = "omni_user"
    postgres_password: str = "changeme"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync DSN — digunakan oleh pgvector LangChain integration."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # --- Telegram Bot ---
    telegram_bot_token: str = ""
    telegram_mode: str = "polling"          # "polling" | "webhook"
    telegram_webhook_url: str = ""          # URL publik (untuk mode webhook di SumoPod)
    telegram_admin_chat_id: str = ""        # Chat ID supervisor untuk HITL

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "change-me-in-production"

    # --- Business Logic ---
    hitl_threshold_idr: float = 1_000_000.0  # Rp 1.000.000
    supervisor_webhook_url: str = "https://hooks.example.com/supervisor"

    # --- SMTP Email Notifications ---
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = "OmniResolve AI <noreply@example.com>"

    # --- App ---
    environment: str = "development"
    log_level: str = "INFO"
    base_url: str = "http://localhost:8001"


@lru_cache
def get_settings() -> Settings:
    """Singleton settings — di-cache setelah pertama kali dipanggil."""
    return Settings()
