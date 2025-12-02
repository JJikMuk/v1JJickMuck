from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # API Security
    api_key: str = "temporary-key"
    
    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "jjikmuk"
    postgres_user: str = "postgres"
    postgres_password: str = ""
    
    # pgvector Configuration
    embedding_dimension: int = 1536
    
    # Logging
    log_level: str = "INFO"
    
    # Gemini API (선택사항 - 기존 호환성을 위해)
    gemini_api_key: str = ""
    
    @property
    def database_url(self) -> str:
        """동기 DB URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def async_database_url(self) -> str:
        """비동기 DB URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
