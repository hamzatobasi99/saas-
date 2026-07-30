import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# تم تصحيح مسار الاستيراد ليتوافق مع بنية مجلدات قاعدة البيانات
from app.database.models import ChatSession, ChatMessage

async def get_or_create_chat_session(db: AsyncSession, tenant_id: uuid.UUID, customer_phone: str) -> ChatSession:
    """
    البحث عن جلسة سابقة لنفس العميل داخل هذه الشركة، أو إنشاء جلسة جديدة إذا لم تكن موجودة.
    """
    query = select(ChatSession).where(
        ChatSession.tenant_id == tenant_id,
        ChatSession.customer_phone == customer_phone
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        session = ChatSession(
            tenant_id=tenant_id,
            customer_phone=customer_phone
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
    
    return session

async def create_chat_message(
    db: AsyncSession, 
    tenant_id: uuid.UUID, 
    session_id: uuid.UUID, 
    sender_type: str, 
    content: str, 
    tokens_used: int = 0
) -> ChatMessage:
    """
    تسجيل رسالة جديدة (من العميل أو الذكاء الاصطناعي) وربطها بالجلسة والشركة.
    """
    message = ChatMessage(
        tenant_id=tenant_id,
        session_id=session_id,
        sender_type=sender_type,
        content=content,
        tokens_used=tokens_used
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return message

async def save_message(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_phone: str,
    content: str,
    sender: str
) -> ChatMessage:
    """
    دالة مساعدة (Helper) تجمع بين البحث عن الجلسة أو إنشائها، ثم حفظ الرسالة بداخلها.
    تُستخدم بشكل أساسي من قبل الـ Webhook.
    """
    session = await get_or_create_chat_session(db, tenant_id, customer_phone)
    return await create_chat_message(
        db=db, 
        tenant_id=tenant_id, 
        session_id=session.id, 
        sender_type=sender, 
        content=content
    )