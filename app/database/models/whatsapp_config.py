import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

class WhatsappConfig(TimestampMixin, Base):
    __tablename__ = "whatsapp_configs"

    # UUID Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    
    # ربط الإعدادات بالشركة (unique=True يضمن علاقة 1-to-1)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    
    # معرفات Meta
    waba_id: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number_id: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # التوكن المشفر (طبقة الأمان)
    encrypted_access_token: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # رمز التحقق من الـ Webhook
    webhook_verify_token: Mapped[str] = mapped_column(String(100), nullable=True)

    # Relationships
    tenant = relationship("Tenant")