from pydantic import BaseModel
import uuid

class WhatsappConfigCreate(BaseModel):
    tenant_id: uuid.UUID
    waba_id: str
    phone_number_id: str
    access_token: str  # النص الصريح الذي سيدخله المستخدم (سيتم تشفيره تلقائياً قبل الحفظ)
    webhook_verify_token: str | None = None

class WhatsappConfigResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    waba_id: str
    phone_number_id: str
    webhook_verify_token: str | None = None

    class Config:
        from_attributes = True