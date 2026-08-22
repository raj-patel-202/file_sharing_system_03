from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    upload_dir: str = "storage/uploads"
    max_upload_bytes: int = 2 * 1024 * 1024 * 1024 # 2 GB

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
