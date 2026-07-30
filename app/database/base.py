from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """
    النموذج الأساسي لجميع الجداول في قاعدة البيانات.
    ترث منه جميع الـ Models ليتعرف عليها SQLAlchemy 2.0 و Alembic.
    """
    pass

class TimestampMixin:
    """
    مكون إضافي (Mixin) يضيف حقل تاريخ الإنشاء تلقائياً لكل جدول يرث منه.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )