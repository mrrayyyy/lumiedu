from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LumiEdu API"
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://lumiedu:change_me@postgres:5432/lumiedu"
    redis_url: str = "redis://redis:6379/0"
    stt_url: str = "http://stt-service:8101"
    llm_url: str = "http://llm-service:8102"
    tts_url: str = "http://tts-service:8103"
    request_timeout_seconds: float = 15.0
    max_concurrent_sessions: int = 3
    jwt_secret_key: str = "change_me_secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    auth_disabled: bool = False
    bootstrap_admin_email: str = "admin@lumiedu.local"
    bootstrap_admin_password: str = "Admin123!"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
