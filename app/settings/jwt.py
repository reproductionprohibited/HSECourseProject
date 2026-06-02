from pydantic_settings import BaseSettings, SettingsConfigDict


class JWTSettings(BaseSettings):
    secret_key: str
    algorithm: str

    model_config = SettingsConfigDict(env_prefix="jwt_")


jwt_settings = JWTSettings()  # type: ignore[call-arg]
