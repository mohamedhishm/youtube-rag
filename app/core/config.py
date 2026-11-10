
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "YouTube Video RAG Assistant"
    debug: bool = True
    mock_mode: bool = True
    groq_api_key: str | None = None
    use_llm: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
