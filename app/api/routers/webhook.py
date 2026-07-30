import logging
import httpx
from fastapi import APIRouter, Request, Response, BackgroundTasks, status

from app.core.config import settings
from app.core.security import decrypt_token
from app.services.chat_service import generate_agent_response
from app.crud.whatsapp import get_whatsapp_config_by_phone_id
from app.crud.chat import save_message

logger = logging.getLogger("whatsapp_webhook")
router = APIRouter()

@router.get("/")
async def verify_webhook(request: Request):
    """
    مسار التحقق الخاص بـ Meta (Hub Challenge).
    يتم استدعاؤه مرة واحدة عند ربط رقم الواتساب بالمنصة.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.info("WhatsApp Webhook verified successfully by Meta.")
        return Response(content=challenge, status_code=status.HTTP_200_OK)
    
    return Response(content="Forbidden", status_code=status.HTTP_403_FORBIDDEN)


async def process_whatsapp_message(payload: dict):
    """
    معالجة الرسالة في الخلفية (Background Task) لضمان عدم تأخير الرد على Meta.
    تمت إضافة حمايات صلبة لمنع انهيار الخادم بسبب Payload غير متوقع.
    """
    try:
        entries = payload.get("entry", [])
        if not entries:
            return
            
        changes = entries[0].get("changes", [])
        if not changes:
            return
            
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        
        # تجاهل الإشعارات التي لا تحتوي على رسائل (مثل تحديثات الحالة: تم القراءة/الاستلام)
        if not messages:
            return 
            
        message = messages[0]
        customer_phone = message.get("from")
        text_body = message.get("text", {}).get("body")
        phone_number_id = value.get("metadata", {}).get("phone_number_id")

        if not text_body:
            logger.warning("Received a non-text message. Media handling is for v2.")
            return

        tenant_config = await get_whatsapp_config_by_phone_id(phone_number_id)
        if not tenant_config:
            logger.error(f"No tenant configuration found for phone_number_id: {phone_number_id}")
            return

        tenant_id = tenant_config.tenant_id
        # Decrypt the token dynamically instead of relying on a missing model attribute
        access_token = decrypt_token(tenant_config.encrypted_access_token)

        await save_message(tenant_id, customer_phone, text_body, sender="customer")

        ai_response_text = await generate_agent_response(
            tenant_id=tenant_id, 
            customer_phone=customer_phone, 
            user_message=text_body
        )

        await save_message(tenant_id, customer_phone, ai_response_text, sender="ai")

        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "messaging_product": "whatsapp",
                "to": customer_phone,
                "type": "text",
                "text": {"body": ai_response_text}
            }
            
            resp = await client.post(url, headers=headers, json=data)
            resp.raise_for_status()
            
            logger.info(f"AI response successfully sent to {customer_phone} for tenant {tenant_id}")

    except Exception as e:
        logger.error(f"Critical error in process_whatsapp_message: {str(e)}")


@router.post("/")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    نقطة استقبال الرسائل من Meta.
    ترجع استجابة فورية 200 OK وتحيل العمل الثقيل إلى BackgroundTasks.
    """
    payload = await request.json()
    background_tasks.add_task(process_whatsapp_message, payload)
    return Response(content="EVENT_RECEIVED", status_code=status.HTTP_200_OK)