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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class TokenPayload(BaseModel):
    user_id: str
    tenant_id: str

async def get_current_tenant(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> TokenPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # فك تشفير توكن Supabase باستخدام المفتاح الخاص به أو مفتاح السيرفر المعتمد
        secret = settings.SUPABASE_JWT_SECRET or settings.SECRET_KEY
        payload = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
        
        # استخراج البريد الإلكتروني أو الـ sub (Supabase user id)
        supabase_user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if not supabase_user_id:
            logger.warning("Token decoded successfully but missing sub.")
            raise credentials_exception
            
        # البحث عن المستخدم في قاعدة البيانات الخاصة بنا مطابقةً لـ Supabase ID أو البريد الإلكتروني
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Authenticated Supabase user {email} not found in local database.")
            raise credentials_exception
            
        return TokenPayload(user_id=str(user.id), tenant_id=str(user.tenant_id))
        
    except JWTError as e:
        logger.warning(f"JWT Validation error: {str(e)}")
        raise credentials_exception

def require_role(allowed_roles: list[str]):
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