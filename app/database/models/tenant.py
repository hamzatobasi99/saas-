import uuid
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    # UUID Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    
    # تفاصيل الشركة
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_tier: Mapped[str] = mapped_column(String(50), default="free", nullable=False)

    # Relationships (العلاقات مع الجداول الأخرى)
    # cascade="all, delete-orphan": تعني أنه إذا تم حذف الشركة، سيتم حذف كل مستخدميها تلقائياً
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")