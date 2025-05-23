from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    WP_URL: str
    WP_JWT_SECRET_KEY: str
    WP_LOGIN: str
    WP_PASSWORD: str

settings = Settings()
