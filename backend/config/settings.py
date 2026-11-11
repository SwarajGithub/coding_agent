import os
from pydantic_settings import BaseSettings
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock


class Settings(BaseSettings):
    LLM_PROVIDER: str = "OPENAI_COMPATIBLE"
    LLM_BASE_URL: str = "http://192.168.0.13:11434/v1"
    LLM_API_KEY: str = "ollama"
    LLM_MODEL_NAME: str = "qwen3-8k:latest"
    AWS_REGION: str = "us-east-1"

    # Automatically hooks into docker environment variables seamlessly
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()


def get_configured_llm(temperature: float = 0.0):
    """Unified entry point delivering externalized model instances to agent loops."""
    provider = settings.LLM_PROVIDER.upper()

    if provider in ["OPENAI", "OPENAI_COMPATIBLE"]:
        return ChatOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL_NAME,
            temperature=temperature
        )
    elif provider == "AWS":
        return ChatBedrock(
            model_id=settings.LLM_MODEL_NAME,
            region_name=settings.AWS_REGION,
            model_kwargs={"temperature": temperature}
        )
    else:
        raise ValueError(f"Unsupported LLM provider profile configuration specified: {settings.LLM_PROVIDER}")
