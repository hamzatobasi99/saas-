from pydantic import BaseModel, EmailStr, Field
import uuid
from typing import Optional

# ... (Tenant Schemas تبقى كما هي) ...

class UserCreate(BaseModel):
    email: EmailStr
    role: str = "employee"
    tenant_id: uuid.UUID
    # كلمة المرور بصيغة نصية واضحة (Plaintext) وتكون اختيارية لدعم OAuth مستقبلاً
    password: Optional[str] = Field(default=None, min_length=8)

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    tenant_id: uuid.UUID

    class Config:
        from_attributes = True