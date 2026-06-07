from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE)

DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175,https://cartium-ten-ashen.vercel.app,"
TRUTHY_VALUES = {"1", "true", "yes", "on", "debug", "development"}
FALSY_VALUES = {"0", "false", "no", "off", "release", "prod", "production", ""}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=str(ENV_FILE), env_file_encoding="utf-8")

    app_name: str = "cartium-backend"
    environment: str = Field(default="development", validation_alias="APP_ENV")
    debug: bool = False
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: [origin.strip() for origin in DEFAULT_CORS_ORIGINS.split(",") if origin.strip()]
    )
    google_client_id: str = ""
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    ai_model_name: str = Field(default="microsoft/Phi-3-mini-4k-instruct", validation_alias="AI_MODEL_NAME")
    huggingface_api_key: str = Field(default="", validation_alias="HUGGINGFACE_API_KEY")
    huggingface_chat_url: str = Field(default="https://router.huggingface.co/v1/chat/completions", validation_alias="HUGGINGFACE_CHAT_URL")
    huggingface_timeout_seconds: int = Field(default=90, validation_alias="HUGGINGFACE_TIMEOUT_SECONDS")
    embedding_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", validation_alias="EMBEDDING_MODEL_NAME")
    chroma_db_path: str = Field(default=str(Path(__file__).resolve().parents[2] / "chroma_db"), validation_alias="CHROMA_DB_PATH")
    chroma_collection_name: str = Field(default="cartium_knowledge", validation_alias="CHROMA_COLLECTION_NAME")
    max_context_docs: int = Field(default=5, validation_alias="MAX_CONTEXT_DOCS")
    max_new_tokens: int = Field(default=300, validation_alias="MAX_NEW_TOKENS")
    temperature: float = Field(default=0.4, validation_alias="TEMPERATURE")
    top_p: float = Field(default=0.9, validation_alias="TOP_P")
    repetition_penalty: float = Field(default=1.1, validation_alias="REPETITION_PENALTY")

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False

        text = str(value).strip().lower()
        if text in TRUTHY_VALUES:
            return True
        if text in FALSY_VALUES:
            return False
        return False

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if value is None:
            value = DEFAULT_CORS_ORIGINS

        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]

        if isinstance(value, (list, tuple, set)):
            return [str(origin).strip() for origin in value if str(origin).strip()]

        return [origin.strip() for origin in DEFAULT_CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
