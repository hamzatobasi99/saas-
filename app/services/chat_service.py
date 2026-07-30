import logging
import json
from app.services.ai_client import get_chat_completion
from app.services.vector_store import search_similar_chunks

# Use a dedicated logger for billing and analytics tracking
logger = logging.getLogger("tenant_billing")

async def generate_agent_response(tenant_id: str, customer_phone: str, user_message: str) -> str:
    """
    Orchestrates the RAG pipeline for a specific tenant:
    1. Searches Qdrant for context isolated by tenant_id.
    2. Constructs the System Prompt.
    3. Calls the central AI Provider.
    4. Logs usage and cost for the billing engine.
    """
    
    # 1. Retrieve isolated context from Vector Store
    # Limit to 3 chunks to keep prompt context focused, fast, and cost-efficient
    relevant_chunks = await search_similar_chunks(query=user_message, tenant_id=tenant_id, limit=3)
    
    if relevant_chunks:
        context_text = "\n\n---\n\n".join(relevant_chunks)
    else:
        context_text = "No relevant context found in the knowledge base."

    # 2. Build the Multi-Tenant System Prompt
    # In the future, this system prompt can be merged with the tenant's custom agent instructions
    system_prompt = f"""You are a professional, helpful, and highly accurate AI Assistant representing this company.
Answer the user's question based strictly on the context provided below.
If the context does not contain the answer, politely inform the user that you don't have that information and do not hallucinate external facts.

COMPANY KNOWLEDGE CONTEXT:
{context_text}
"""

    # 3. Call the AI Provider (Returns our strongly-typed AIResponse Pydantic model)
    ai_response = await get_chat_completion(
        system_prompt=system_prompt,
        user_message=user_message
    )

    # 4. Log usage for Billing & Analytics (Ready for Stripe / Analytics dashboards)
    logger.info(json.dumps({
        "event": "tenant_chat_usage",
        "tenant_id": str(tenant_id),
        "customer_phone": customer_phone,
        "cost_usd": ai_response.estimated_cost_usd,
        "provider": ai_response.provider_name,
        "model": ai_response.model_name,
        "tokens": ai_response.usage.model_dump()
    }))

    # 5. Return the raw string content to be sent via the WhatsApp Webhook
    return ai_response.content