import uuid
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.crud.whatsapp import upsert_whatsapp_config, get_whatsapp_config_by_tenant
from app.core.security import encrypt_token

router = APIRouter()

async def get_current_tenant_id(x_tenant_id: str = Header(..., description="Tenant ID from Auth Token")) -> uuid.UUID:
    try:
        return uuid.UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Tenant ID format")

class WhatsAppSetupRequest(BaseModel):
    waba_id: str
    phone_number_id: str
    access_token: str

@router.post("/setup")
async def setup_whatsapp(
    payload: WhatsAppSetupRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        # تشفير الـ Token فوراً قبل التعامل مع قاعدة البيانات
        encrypted_token = encrypt_token(payload.access_token)
        
        await upsert_whatsapp_config(
            db=db,
            tenant_id=tenant_id,
            waba_id=payload.waba_id,
            phone_number_id=payload.phone_number_id,
            encrypted_token=encrypted_token
        )
        return {"message": "تم حفظ وإعدادات الواتساب بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_whatsapp_status(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    config = await get_whatsapp_config_by_tenant(db, tenant_id)
    if config:
        return {
            "status": "connected",
            "waba_id": config.waba_id,
            "phone_number_id": config.phone_number_id
        }
    return {"status": "pending_setup"}