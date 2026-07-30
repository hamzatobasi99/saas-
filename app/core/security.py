from datetime import datetime, timedelta
from typing import Optional
import base64
from jose import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from app.core.config import settings

# إعداد Passlib باستخدام خوارزمية bcrypt القياسية للإنتاج
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# عمر التوكن الافتراضي (مثلاً: 7 أيام)
ACCESS_TOKEN_EXPIRE_DAYS = 7

def _get_fernet() -> Fernet:
    """توليد مفتاح تشفير متماثل صالح بناءً على SECRET_KEY"""
    key = settings.SECRET_KEY.encode('utf-8')
    # Fernet requires a 32-byte url-safe base64-encoded key
    key = base64.urlsafe_b64encode(key.ljust(32)[:32])
    return Fernet(key)

def encrypt_token(token: str) -> str:
    """تشفير النصوص الحساسة مثل Access Tokens"""
    return _get_fernet().encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """فك تشفير النصوص الحساسة"""
    return _get_fernet().decrypt(encrypted_token.encode()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    مقارنة كلمة المرور المدخلة مع الكلمة المشفرة في قاعدة البيانات
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    تشفير كلمة المرور قبل حفظها في قاعدة البيانات
    """
    return pwd_context.hash(password)

def create_access_token(user_id: str, tenant_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    توليد JWT يحمل بيانات المستخدم والشركة (Tenant).
    هذا التوكن سيتم إرساله للـ Frontend ليضعه في Header كل طلب (Authorization: Bearer <token>).
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    # الـ Payload يحتوي على البيانات التي اعتمدنا عليها في deps.py
    to_encode = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "exp": expire
    }
    
    # التشفير باستخدام المفتاح السري الخاص بالخادم
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    
    return encoded_jwt