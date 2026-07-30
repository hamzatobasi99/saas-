from pydantic import BaseModel

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class AIResponse(BaseModel):
    content: str
    usage: TokenUsage
    estimated_cost_usd: float = 0.0
    provider_name: str
    model_name: str