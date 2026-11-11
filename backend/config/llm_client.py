import os
import logging
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock
from config.settings import settings

logger = logging.getLogger("agent.config.llm_client")


class LLMClient:
    _instance: Optional['LLMClient'] = None

    def __new__(cls) -> 'LLMClient':
        """Ensure singleton lifecycle management across application runtimes."""
        if cls._instance is None:
            cls._instance = super(LLMClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Parse core setup metadata precisely during initial class allocation."""
        self.provider = settings.LLM_PROVIDER.upper()
        self.model_name = settings.LLM_MODEL_NAME
        logger.info(f"LLMClient initialized successfully using provider: {self.provider} | Model: {self.model_name}")

    def get_model(self, temperature: float = 0.0, max_tokens: Optional[int] = None) -> Any:
        model_kwargs: Dict[str, Any] = {}
        if max_tokens is not None:
            model_kwargs["max_tokens"] = max_tokens

        # Route 1: Local Endpoint or standard OpenAI Schema
        if self.provider in ["OPENAI", "OPENAI_COMPATIBLE"]:
            return ChatOpenAI(
                base_url=settings.LLM_BASE_URL,
                api_key=settings.LLM_API_KEY,
                model=self.model_name,
                temperature=temperature,
                **model_kwargs
            )

        # Route 2: AWS Bedrock Core Runtime Pipeline
        elif self.provider == "AWS":
            bedrock_kwargs = {"temperature": temperature}
            if max_tokens is not None:
                bedrock_kwargs["max_tokens_to_sample"] = max_tokens

            return ChatBedrock(
                model_id=self.model_name,
                region_name=settings.AWS_REGION,
                model_kwargs=bedrock_kwargs
            )

        else:
            raise ValueError(f"System failure: Configuration profile '{self.provider}' is unsupported.")


# Global access reference for easy importing across components
llm_client = LLMClient()
