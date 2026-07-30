import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

class ChatSession(TimestampMixin, Base):
    __tablename__ = "chat_sessions"

    # UUID Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    
    # ربط الجلسة بالشركة
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # رقم هاتف العميل (يُفضل عمل Index عليه لتسريع البحث عند وصول رسالة جديدة)
    customer_phone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # تحديث وقت آخر رسالة تلقائياً
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    tenant = relationship("Tenant")
    # سنضيف علاقة الرسائل (messages) بعد بناء جدول الرسائل في الخطوة القادمة