from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration management via environment variables."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    host: str = "localhost"
    port: int = 8765
    db_path: str = "data/evm.db"
    admin_secret_key: str = "admin-secret"

settings = Settings()
