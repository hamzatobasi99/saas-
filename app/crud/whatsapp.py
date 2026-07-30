import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import WhatsappConfig
from app.schemas.whatsapp import WhatsappConfigCreate
from app.core.security import encrypt_token

async def create_whatsapp_config(session: AsyncSession, config_in: WhatsappConfigCreate) -> WhatsappConfig:
    """
    إضافة إعدادات واتساب جديدة للشركة
    ملاحظة: يتم تشفير الـ Access Token هنا قبل الحفظ في القاعدة
    """
    encrypted_token = encrypt_token(config_in.access_token)
    
    db_config = WhatsappConfig(
        tenant_id=config_in.tenant_id,
        waba_id=config_in.waba_id,
        phone_number_id=config_in.phone_number_id,
        encrypted_access_token=encrypted_token,
        webhook_verify_token=config_in.webhook_verify_token
    )
    session.add(db_config)
    await session.commit()
    await session.refresh(db_config)
    return db_config

async def get_whatsapp_config_by_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> WhatsappConfig | None:
    """جلب إعدادات الواتساب الخاصة بشركة محددة"""
    result = await session.execute(select(WhatsappConfig).where(WhatsappConfig.tenant_id == tenant_id))
    return result.scalar_one_or_none()

async def upsert_whatsapp_config(session: AsyncSession, config_in: WhatsappConfigCreate) -> WhatsappConfig:
    """
    إنشاء أو تحديث إعدادات الواتساب الخاصة بالشركة.
    تمت إضافتها لتتوافق مع متطلبات الاستيراد في whatsapp router.
    """
    db_config = await get_whatsapp_config_by_tenant(session, config_in.tenant_id)
    encrypted_token = encrypt_token(config_in.access_token)
    
    # إذا كانت الإعدادات موجودة، قم بتحديثها
    if db_config:
        db_config.waba_id = config_in.waba_id
        db_config.phone_number_id = config_in.phone_number_id
        db_config.encrypted_access_token = encrypted_token
        db_config.webhook_verify_token = config_in.webhook_verify_token
        
        await session.commit()
        await session.refresh(db_config)
        return db_config
        
    # إذا لم تكن موجودة، قم بإنشاء إعدادات جديدة
    return await create_whatsapp_config(session, config_in)

async def get_whatsapp_config_by_phone_id(session: AsyncSession, phone_number_id: str) -> WhatsappConfig | None:
    """
    الدالة الجديدة الخاصة بالـ SaaS: 
    البحث عن إعدادات الشركة فور وصول رسالة من الـ Webhook بناءً على رقم هاتف الواتساب
    """
    result = await session.execute(
        select(WhatsappConfig).where(WhatsappConfig.phone_number_id == phone_number_id)
    )
    return result.scalar_one_or_none()