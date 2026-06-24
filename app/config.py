from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Fraud Hunter"
    database_url: str = "sqlite:///./data/fraud_hunter.db"
    auth_disabled: bool = False
    # limiares de decisão (score 0-100)
    t_block: int = 80
    t_review: int = 60
    t_challenge: int = 35


settings = Settings()
