import uuid
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

class ChatMessage(TimestampMixin, Base):
    __tablename__ = "chat_messages"

    # UUID Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    
    # ربط الرسالة بالشركة
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # ربط الرسالة بجلسة المحادثة
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # نوع المرسل (customer, ai_agent, human)
    sender_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # محتوى الرسالة
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # عدد الـ Tokens المستخدمة (لتتبع استهلاك OpenAI API)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    session = relationship("ChatSession")