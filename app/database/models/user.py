import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

class User(TimestampMixin, Base):
    __tablename__ = "users"

    # UUID Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    
    # Foreign Key يربط المستخدم بالشركة (أهم حقل في الـ Multi-Tenancy)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # تفاصيل المستخدم
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default="employee", nullable=False)
    
    # حقل كلمة المرور المشفرة (تمت إضافته لدعم الـ JWT Login)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")