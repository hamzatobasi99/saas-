import logging
import json
import httpx
import openai
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.schemas.ai import AIResponse, TokenUsage

# Structured Logger for Telemetry (Grafana/Loki ready)
logger = logging.getLogger("ai_telemetry")

class BaseAIProvider(ABC):
    """Abstract Base Class for all AI Providers."""
    
    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        pass

    @abstractmethod
    async def get_chat_completion(self, system_prompt: str, user_message: str) -> AIResponse:
        pass

# Define ONLY transient errors for retries (Skip Auth/Invalid Request errors)
TRANSIENT_ERRORS = (
    openai.RateLimitError,
    openai.APIConnectionError,
    openai.InternalServerError,
    httpx.TimeoutException,
    httpx.ConnectError,
)

def log_retry(retry_state):
    """Structured logging for retry attempts."""
    logger.warning(json.dumps({
        "event": "ai_request_retry",
        "attempt": retry_state.attempt_number,
        "error": str(retry_state.outcome.exception())
    }))

class OpenAIProvider(BaseAIProvider):
    """OpenAI Implementation of the AI Provider."""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.chat_model = settings.OPENAI_CHAT_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.timeout = settings.AI_REQUEST_TIMEOUT
        
        # Enforce timeout at the HTTP client level
        http_client = httpx.AsyncClient(timeout=self.timeout)
        self.client = openai.AsyncOpenAI(api_key=self.api_key, http_client=http_client)

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on current OpenAI pricing for gpt-4o-mini."""
        if self.chat_model == "gpt-4o-mini":
            # $0.150 / 1M input tokens, $0.600 / 1M output tokens
            return (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.60 / 1_000_000)
        return 0.0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(TRANSIENT_ERRORS),
        after=log_retry
    )
    async def get_embedding(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            input=[text],
            model=self.embedding_model
        )
        return response.data[0].embedding

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(TRANSIENT_ERRORS),
        after=log_retry
    )
    async def get_chat_completion(self, system_prompt: str, user_message: str) -> AIResponse:
        response = await self.client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1
        )
        
        usage = response.usage
        cost = self._calculate_cost(usage.prompt_tokens, usage.completion_tokens)
        
        # Structured log for successful generation (Billing & Telemetry)
        logger.info(json.dumps({
            "event": "ai_completion_success",
            "provider": "openai",
            "model": self.chat_model,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "cost_usd": cost
        }))

        return AIResponse(
            content=response.choices[0].message.content,
            usage=TokenUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens
            ),
            estimated_cost_usd=cost,
            provider_name="openai",
            model_name=self.chat_model
        )

# Factory pattern to resolve the configured AI Provider dynamically
def get_ai_provider() -> BaseAIProvider:
    if settings.AI_PROVIDER.lower() == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")

# Global singleton instance
ai_provider = get_ai_provider()

# Facade functions to keep compatibility with other services (e.g., vector_store.py)
async def get_embedding(text: str) -> list[float]:
    return await ai_provider.get_embedding(text)

async def get_chat_completion(system_prompt: str, user_message: str) -> AIResponse:
    return await ai_provider.get_chat_completion(system_prompt, user_message)