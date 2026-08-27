from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Meet API"
    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/meetinglens"

    ollama_base_url: str = "http://localhost:11434/v1"
    chat_model: str = Field(
        default="llama3.1",
        validation_alias=AliasChoices("CHAT_MODEL", "LLM_MODEL"),
    )
    embedding_model: str = "nomic-embed-text"
    embedding_dimensions: int = 768
    prompt_version: str = "rag-v2"

    max_upload_size_mb: int = 5
    max_audio_upload_size_mb: int = 25
    max_transcript_chars: int = 400_000
    max_question_chars: int = 2000

    whisper_model: str = "base"
    whisper_language: str = ""

    chunk_target_tokens: int = 500
    chunk_max_tokens: int = 600
    chunk_overlap_tokens: int = 80
    short_transcript_tokens: int = 1800

    rag_candidate_k: int = 10
    rag_top_k: int = 6
    rag_min_score: float = 0.18
    rag_history_messages: int = 6
    rag_max_context_tokens: int = 3500

    upload_rate_limit: int = 10
    question_rate_limit: int = 30
    rate_limit_window_seconds: int = 60

    enable_ai_traces: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("ollama_base_url")
    @classmethod
    def normalize_ollama_base_url(cls, value: str) -> str:
        url = value.rstrip("/")
        if not url.endswith("/v1"):
            url = f"{url}/v1"
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
