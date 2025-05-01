from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Classe para configurar as variáveis de ambiente.

    Args:
        BaseSettings (pydantic_settings.BaseSettings):
            classe base para configurar as variáveis de ambiente.
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )
    WP_URL: str
    WP_JWT_SECRET_KEY: str
    WP_LOGIN: str
    WP_PASSWORD: str
