from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # -> qc_server/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MQC_", env_file=".env", extra="ignore")

    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'mqc.db').as_posix()}"
    data_dir: str = str(BASE_DIR / "data")
    reviewer_email: str = "inspector@gspemail.com"
    cors_origins: str = "http://localhost:5757"
    camera_monitor_enabled: bool = True
    camera_poll_interval: int = 20
    models_dir: str = str(BASE_DIR / "models")
    stream_max_width: int = 960
    stream_max_fps: int = 15


settings = Settings()
