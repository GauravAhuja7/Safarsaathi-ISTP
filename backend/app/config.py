from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://safarsaathi:safarsaathi@localhost:5432/safarsaathi"
    redis_url: str = "redis://localhost:6379"

    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = "safarsaathi_verify"

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""

    msg91_api_key: str = ""
    sms_sender_id: str = "SAFARS"

    team_admin_phone: str = ""

    imd_api_key: str = ""
    imd_email: str = ""
    imd_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
