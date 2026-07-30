import uuid
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

class KnowledgeDocument(TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    # UUID Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    
    # ربط الملف بالشركة (حقل الـ SaaS الأساسي)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # تفاصيل الملف
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="processing", nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # من قام بالرفع؟ (SET NULL تعني إذا تم حذف الموظف، يبقى الملف ولكن يصبح حقله فارغاً)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    tenant = relationship("Tenant")
    uploader = relationship("User")