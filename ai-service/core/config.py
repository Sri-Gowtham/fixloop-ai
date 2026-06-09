"""
core/config.py
--------------
Centralised settings loaded from environment variables / .env file.
Uses Pydantic BaseSettings so every value is validated at startup.
"""

from typing import List, Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field("development", pattern="^(development|staging|production)$")

    # ---- Supabase ----
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str         # backend uses service role (bypasses RLS)
    DATABASE_URL: str                      # direct asyncpg / psycopg2 connection

    # ---- OpenAI ----
    OPENAI_API_KEY: str
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"   # 1536-dim, matches schema
    OPENAI_CHAT_MODEL: str = "gpt-4o"

    # ---- Google Gemini (optional — used for cluster label generation) ----
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # LLM backend selection: "openai" | "gemini"
    CLUSTER_LLM_BACKEND: str = Field("openai", pattern="^(openai|gemini)$")

    # ---- CORS ----
    CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",
    ]

    # ---- Ingestion pipeline ----
    MAX_UPLOAD_SIZE_MB: int = 200
    INGEST_BATCH_SIZE: int = 64            # tickets per embed batch

    # ---- Clustering ----
    CLUSTER_MIN_CLUSTER_SIZE: int = 3      # HDBSCAN min_cluster_size
    CLUSTER_MIN_SAMPLES: int = 2           # HDBSCAN min_samples (controls noise sensitivity)
    CLUSTER_EPSILON: float = 0.15          # HDBSCAN cluster_selection_epsilon (cosine distance)
    CLUSTER_MAX_TICKETS: int = 10_000      # safety cap — load at most this many tickets per run
    CLUSTER_LLM_BATCH_SIZE: int = 10       # clusters to label per LLM call
    CLUSTER_TITLE_MAX_WORDS: int = 8       # max words in generated cluster title

    # ---- Investigations ----
    INVESTIGATION_CONFIDENCE_THRESHOLD: float = 0.70
    DEPLOY_CORRELATION_WINDOW_DAYS: int = 7
    INVESTIGATION_TICKET_SAMPLE_SIZE: int = 30   # ticket samples sent to LLM
    INVESTIGATION_LLM_BACKEND: str = Field("openai", pattern="^(openai|gemini)$")
    # Revenue: average support cost per ticket per month (used for estimate)
    REVENUE_COST_PER_TICKET_USD: float = 70.0

    # ---- Recommendations ----
    RECOMMENDATION_LLM_BACKEND: str = Field("openai", pattern="^(openai|gemini)$")
    RECOMMENDATION_CACHE_DAYS: int = 7   # reuse recent recs for the same investigation



settings = Settings()  # type: ignore[call-arg]
