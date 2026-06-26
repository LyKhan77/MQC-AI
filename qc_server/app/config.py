from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MQC_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/mqc.db"
    data_dir: str = "./data"
    reviewer_email: str = "inspector@gspemail.com"
    cors_origins: str = "http://localhost:5757"


settings = Settings()
