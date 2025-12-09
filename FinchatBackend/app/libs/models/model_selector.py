from agno.models.ollama import Ollama
from app.config.settings import settings


def get_ollama() -> Ollama:
    return Ollama(
        id=settings.ollama_model,
        host=settings.ollama_host,
        options={
            "temperature": 0,
            "seed": 123,
        },
    )
