from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database.session import get_db
from app.schemas.tenant_user import TenantCreate, TenantResponse
from app.crud.tenant_user import create_tenant
from app.api.deps import require_role, TokenPayload

logger = logging.getLogger("tenants")
router = APIRouter()

@router.post("/", response_model=TenantResponse)
async def create_new_tenant(
    tenant_in: TenantCreate, 
    db: AsyncSession = Depends(get_db),
    current_admin: TokenPayload = Depends(require_role(["super_admin"]))
):
    """
    إنشاء شركة جديدة في النظام.
    هذا المسار محمي بصلاحيات الأدمن الرئيسي لمنع الإغراق وتسجيل الشركات الوهمية.
    """
    try:
        new_tenant = await create_tenant(session=db, tenant_in=tenant_in)
        return new_tenant
    except Exception as e:
        logger.error(f"Error creating tenant {tenant_in.name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Failed to create tenant. Please verify the provided data."
        )