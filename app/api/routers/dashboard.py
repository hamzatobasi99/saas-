import uuid
import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import get_db
from app.database.models import ChatSession, ChatMessage, WhatsappConfig
from app.services.vector_store import get_vector_store_stats
from app.api.deps import get_current_tenant, TokenPayload

logger = logging.getLogger("dashboard")
router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    current_tenant: TokenPayload = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    try:
        tenant_id_uuid = uuid.UUID(current_tenant.tenant_id)
        
        # تجهيز الاستعلامات
        total_sessions_query = select(func.count()).select_from(ChatSession).where(ChatSession.tenant_id == tenant_id_uuid)
        total_messages_query = select(func.count()).select_from(ChatMessage).where(ChatMessage.tenant_id == tenant_id_uuid)
        whatsapp_query = select(WhatsappConfig).where(WhatsappConfig.tenant_id == tenant_id_uuid)

        # تنفيذ جميع الاستعلامات (قاعدة البيانات والذكاء الاصطناعي) في نفس الوقت لرفع الأداء
        vector_stats_task = get_vector_store_stats(current_tenant.tenant_id)
        sessions_task = db.execute(total_sessions_query)
        messages_task = db.execute(total_messages_query)
        whatsapp_task = db.execute(whatsapp_query)

        vector_stats, sessions_res, messages_res, whatsapp_res = await asyncio.gather(
            vector_stats_task, sessions_task, messages_task, whatsapp_task
        )

        total_sessions = sessions_res.scalar() or 0
        total_messages = messages_res.scalar() or 0
        whatsapp_config = whatsapp_res.scalar_one_or_none()
        whatsapp_status = "connected" if whatsapp_config else "pending_setup"

        return {
            "knowledge_base": {
                "total_documents": vector_stats["total_documents"],
                "total_chunks": vector_stats["total_chunks"],
                "last_uploaded_document": vector_stats["last_uploaded_document"],
                "status": "ready"
            },
            "system_health": {
                "ai_engine": "online",
                "vector_db": "connected",
                "database": "connected"
            },
            "integrations": {
                "whatsapp": {
                    "status": whatsapp_status, 
                    "total_messages": total_messages,
                    "total_sessions": total_sessions
                },
                "instagram": {"status": "coming_soon", "total_messages": 0},
                "messenger": {"status": "coming_soon", "total_messages": 0},
            }
        }
    except Exception as e:
        # تسجيل الخطأ داخلياً وعدم تسريب التفاصيل للعميل
        logger.error(f"Failed to fetch dashboard stats for tenant {current_tenant.tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An internal server error occurred while fetching dashboard statistics.")