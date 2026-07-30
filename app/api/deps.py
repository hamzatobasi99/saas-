import logging
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.database.session import get_db
from app.database.models import User

logger = logging.getLogger("security")

# إعداد OAuth2 ليتوافق مع Swagger UI واستقبال التوكن عبر Header: Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class TokenPayload(BaseModel):
    """نموذج Pydantic لضمان وجود البيانات الأساسية داخل الـ JWT Token"""
    user_id: str
    tenant_id: str

async def get_current_tenant(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """
    Dependency (تبعيات) يتم حقنها في مسارات الـ API.
    تقوم بفك تشفير التوكن، التحقق من صلاحيته، واستخراج معرف الشركة.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        
        if user_id is None or tenant_id is None:
            logger.warning("Token decoded successfully but missing sub (user_id) or tenant_id.")
            raise credentials_exception
            
        return TokenPayload(user_id=user_id, tenant_id=tenant_id)
        
    except JWTError as e:
        logger.warning(f"JWT Validation error: {str(e)}")
        raise credentials_exception

def require_role(allowed_roles: list[str]):
    """
    Dependency للتحقق من صلاحيات المستخدم (RBAC).
    يستخرج المستخدم من قاعدة البيانات للتحقق من دوره الحالي (owner, admin, employee).
    """
    async def role_checker(
        current_tenant: TokenPayload = Depends(get_current_tenant),
        db: AsyncSession = Depends(get_db)
    ) -> TokenPayload:
        result = await db.execute(select(User).where(User.id == uuid.UUID(current_tenant.user_id)))
        user = result.scalar_one_or_none()
        
        if not user or user.role not in allowed_roles:
            logger.warning(f"User {current_tenant.user_id} attempted an unauthorized action.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required permissions to perform this action."
            )
        return current_tenant
    return role_checker