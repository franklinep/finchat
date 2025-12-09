from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    database_url: str

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "gpt-oss:20b"

    device: str = "gpu"

    environment: str = "local"
    jwt_secret: str = "dev-secret"
    jwt_expire_minutes: int = 60

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
