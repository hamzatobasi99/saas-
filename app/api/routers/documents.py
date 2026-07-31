from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from pydantic import BaseModel
import logging

from app.api.deps import get_current_tenant, TokenPayload, require_role
from app.services.vector_store import (
    store_chunks_in_db, 
    delete_file_from_db, 
    get_vector_store_stats,
    qdrant,
    COLLECTION_NAME
)
from qdrant_client.http import models

# استيراد مستخرج النصوص المتقدم الذي يدعم PDF والترميزات المختلفة
from app.services.document_parser import extract_text_from_file

logger = logging.getLogger("tenant_actions")
router = APIRouter()

def simple_text_chunker(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """مقسم نصوص بسيط للإنتاج، يمكن استبداله لاحقاً بمكتبات متقدمة مثل LangChain TextSplitter."""
    if not text:
        return []
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

@router.get("/")
async def get_documents(current_tenant: TokenPayload = Depends(get_current_tenant)):
    """
    جلب قائمة المستندات للشركة.
    تم إضافته ليتوافق مع طلب GET /api/documents في الـ Frontend.
    """
    try:
        # استخدام Scroll API لجلب الملفات الفريدة من Qdrant مباشرة
        results, _ = await qdrant.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="tenant_id",
                        match=models.MatchValue(value=str(current_tenant.tenant_id)),
                    )
                ]
            ),
            limit=10000,
            with_payload=True,
            with_vectors=False
        )
        
        # استخراج أسماء الملفات الفريدة
        unique_files = list(set(hit.payload.get("filename") for hit in results if hit.payload and "filename" in hit.payload))
        
        # بناء هيكل الاستجابة المتوافق مع TypeScript Interface في الـ Frontend
        documents = []
        for filename in unique_files:
            if filename:
                documents.append({
                    "id": filename,  # استخدام اسم الملف كمعرف
                    "filename": filename,
                    "size": 0,
                    "created_at": datetime.now().strftime("%Y-%m-%d")
                })
                
        return documents
    except Exception as e:
        logger.error(f"Error fetching documents list for tenant {current_tenant.tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents list."
        )

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_tenant: TokenPayload = Depends(get_current_tenant)
):
    """رفع ملف، استخراج النص باستخدام المحلل المتقدم، وتقسيمه لتخزينه كمتجهات."""
    if not file.filename.endswith(('.txt', '.md', '.pdf')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only TXT, MD, and PDF are allowed."
        )
    
    try:
        content_bytes = await file.read()
        
        # استخدام المحلل المتقدم لمعالجة الـ PDF والترميزات لضمان عدم انهيار الـ Backend
        text_content = await extract_text_from_file(content_bytes, file.filename)
        
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

@router.delete("/{file_id}")
async def delete_document(
    file_id: str,
    current_tenant: TokenPayload = Depends(require_role(["owner", "admin"]))
):
    """
    حذف مستند معين بناءً على الـ ID.
    يتوافق الآن مع apiClient.delete(`/api/documents/${id}`)
    """
    try:
        success = await delete_file_from_db(
            filename=file_id, 
            tenant_id=current_tenant.tenant_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or you do not have permission to delete it."
            )
            
        logger.info(f"Tenant {current_tenant.tenant_id} deleted document {file_id}")
        
        return {"status": "success", "message": f"Document '{file_id}' deleted successfully."}
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