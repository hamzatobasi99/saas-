import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Tenant, User
from app.schemas.tenant_user import TenantCreate, UserCreate
# استيراد دالة التشفير التي أنشأناها في نواة الأمان
from app.core.security import get_password_hash 

async def create_tenant(session: AsyncSession, tenant_in: TenantCreate) -> Tenant:
    """إضافة شركة جديدة إلى قاعدة البيانات"""
    db_tenant = Tenant(
        name=tenant_in.name,
        subscription_tier=tenant_in.subscription_tier
    )
    session.add(db_tenant)
    await session.commit()
    await session.refresh(db_tenant)
    return db_tenant

async def get_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> Tenant | None:
    """جلب بيانات شركة عن طريق المعرف الخاص بها"""
    result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    return result.scalar_one_or_none()

# ----------------- الإضافات الجديدة والتحديثات ----------------- #

async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """
    جلب بيانات مستخدم عن طريق البريد الإلكتروني.
    هذه الدالة أساسية لعملية تسجيل الدخول (Login).
    """
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, user_in: UserCreate) -> User:
    """إضافة مستخدم جديد وتشفير كلمة المرور قبل حفظها"""

async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """جلب مستخدم عبر البريد الإلكتروني لتسجيل الدخول"""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
    
    # 1. تشفير كلمة المرور القادمة من الـ Schema
    hashed_pw = get_password_hash(user_in.password)
    
    # 2. إنشاء المستخدم مع كلمة المرور المشفرة
    db_user = User(
        email=user_in.email,
        role=user_in.role,
        tenant_id=user_in.tenant_id,
        hashed_password=hashed_pw  # تم إضافة الحقل هنا
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user