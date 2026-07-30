from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from pydantic import BaseModel
import logging

from app.api.deps import get_current_tenant, TokenPayload, require_role
from app.services.vector_store import (
    store_chunks_in_db, 
    delete_file_from_db, 
    get_vector_store_stats
)

logger = logging.getLogger("tenant_actions")
router = APIRouter()

class DeleteDocumentRequest(BaseModel):
    filename: str

def simple_text_chunker(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """مقسم نصوص بسيط للإنتاج، يمكن استبداله لاحقاً بمكتبات متقدمة مثل LangChain TextSplitter."""
    if not text:
        return []
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    # حصر رفع المستندات بمدراء الشركة فقط
    current_tenant: TokenPayload = Depends(require_role(["owner", "admin"]))
):
    """رفع ملف نصي، تقسيمه، وتخزينه كمتجهات في مساحة الشركة المعزولة."""
    if not file.filename.endswith(('.txt', '.md')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currently, only .txt and .md files are supported for production MVP."
        )
    
    try:
        content_bytes = await file.read()
        text_content = content_bytes.decode('utf-8')
        
        chunks = simple_text_chunker(text_content)
        
        chunks_count = await store_chunks_in_db(
            chunks=chunks, 
            filename=file.filename, 
            tenant_id=current_tenant.tenant_id
        )
        
        logger.info(f"Tenant {current_tenant.tenant_id} uploaded {file.filename} ({chunks_count} chunks)")
        
        return {
            "status": "success",
            "filename": file.filename,
            "chunks_processed": chunks_count,
            "message": "Document successfully vectorized and stored."
        }
    except Exception as e:
        logger.error(f"Error processing file upload for tenant {current_tenant.tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process and store the document."
        )

@router.delete("/delete")
async def delete_document(
    request: DeleteDocumentRequest,
    # حصر صلاحية الحذف بالمدراء والمالكين فقط لمنع التخريب من قبل الموظفين
    current_tenant: TokenPayload = Depends(require_role(["owner", "admin"]))
):
    """حذف مستند معين من قاعدة المعرفة الخاصة بالشركة."""
    try:
        success = await delete_file_from_db(
            filename=request.filename, 
            tenant_id=current_tenant.tenant_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or you do not have permission to delete it."
            )
            
        logger.info(f"Tenant {current_tenant.tenant_id} deleted document {request.filename}")
        
        return {"status": "success", "message": f"Document '{request.filename}' deleted successfully."}
    except Exception as e:
        logger.error(f"Error deleting file for tenant {current_tenant.tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the document."
        )

@router.get("/stats")
async def get_stats(current_tenant: TokenPayload = Depends(get_current_tenant)):
    """جلب إحصائيات قاعدة المتجهات للشركة لعرضها في الـ Dashboard."""
    try:
        stats = await get_vector_store_stats(tenant_id=current_tenant.tenant_id)
        return {"status": "success", "data": stats}
    except Exception as e:
        logger.error(f"Error fetching stats for tenant {current_tenant.tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge base statistics."
        )