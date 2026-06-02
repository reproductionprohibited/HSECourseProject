from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(env_prefix="db_")


db_settings = DBSettings()
