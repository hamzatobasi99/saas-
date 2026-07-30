import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.security import verify_password, create_access_token
from app.crud.tenant_user import get_user_by_email  # تأكد من اسم ملف الـ CRUD لديك
from app.database.session import get_db

logger = logging.getLogger("auth")
router = APIRouter()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    tenant_id: str

@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)  # حقن جلسة قاعدة البيانات هنا
):
    """
    مسار تسجيل الدخول للشركات.
    يستقبل البريد الإلكتروني وكلمة المرور، ويرجع JWT Token.
    """
    # تمرير الـ db لدالة الـ CRUD
    user = await get_user_by_email(session=db, email=form_data.username)
    
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id)
    )
    
    logger.info(f"Successful login for user {user.id}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tenant_id": str(user.tenant_id)
    }