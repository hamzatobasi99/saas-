import httpx
import os

async def send_whatsapp_message(phone_number_id: str, access_token: str, recipient_phone: str, message_body: str):
    """
    إرسال رسالة واتساب باستخدام بيانات الشركة الخاصة (Phone Number ID و Access Token المفكوك)
    """
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": message_body},
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"WhatsApp API Error: {e.response.text}")
            raise e
        except Exception as e:
            print(f"Connection Error: {str(e)}")
            raise e