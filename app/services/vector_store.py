import uuid
import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from app.core.config import settings
from app.services.ai_client import get_embedding

logger = logging.getLogger(__name__)

# AsyncQdrantClient لا يدعم وضع ":memory:" لأنه مخصص للاتصالات عبر الشبكة.
# نقوم بتحويله إلى الرابط الافتراضي لمنع تعطل الخادم عند قراءة الإعدادات.
_qdrant_url = settings.QDRANT_URL
if _qdrant_url == ":memory:":
    _qdrant_url = "http://localhost:6333"

# استخدام AsyncQdrantClient إلزامي لبيئات الإنتاج المبنية على FastAPI
# لمنع توقف الخادم (Blocking I/O) عند معالجة طلبات متزامنة من عدة شركات
qdrant = AsyncQdrantClient(
    url=_qdrant_url,
    api_key=settings.QDRANT_API_KEY,
    timeout=10.0
)

COLLECTION_NAME = "saas_documents"
VECTOR_SIZE = 1536  # Dimension size for text-embedding-3-small

async def init_vector_store():
    """
    التأكد من وجود الـ Collection عند تشغيل الخادم.
    يجب استدعاء هذه الدالة داخل الـ lifespan في main.py.
    تمت إضافة حماية لمنع تعطل إقلاع الخادم في حال لم يتم تشغيل Qdrant بعد.
    """
    try:
        exists = await qdrant.collection_exists(COLLECTION_NAME)
        if not exists:
            await qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info(f"Initialized new Qdrant collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.warning(f"Could not connect to Qdrant Vector Store. AI features will not work until Qdrant is running. Error: {str(e)}")

async def store_chunks_in_db(chunks: list[str], filename: str, tenant_id: str) -> int:
    """تخزين القطع النصية مع ربطها بمعرف الشركة لضمان عزل البيانات."""
    if not chunks:
        return 0
        
    points = []
    for i, chunk in enumerate(chunks):
        point_id = str(uuid.uuid4())
        
        # الاعتماد على طبقة التجريد المركزية للذكاء الاصطناعي
        vector = await get_embedding(chunk)
        
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "tenant_id": str(tenant_id),
                    "filename": filename, 
                    "text": chunk, 
                    "chunk_index": i
                }
            )
        )
        
    await qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    return len(points)

async def delete_file_from_db(filename: str, tenant_id: str) -> bool:
    """حذف متجهات ملف محدد يتبع لشركة محددة فقط."""
    await qdrant.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="tenant_id",
                        match=models.MatchValue(value=str(tenant_id)),
                    ),
                    models.FieldCondition(
                        key="filename",
                        match=models.MatchValue(value=filename),
                    )
                ]
            )
        )
    )
    return True

async def search_similar_chunks(query: str, tenant_id: str, limit: int = 3) -> list[str]:
    """بحث دلالي داخل المستندات الخاصة بالشركة فقط (Tenant Isolation)."""
    query_vector = await get_embedding(query)
    
    search_result = await qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="tenant_id",
                    match=models.MatchValue(value=str(tenant_id)),
                )
            ]
        ),
        limit=limit
    )
    return [hit.payload["text"] for hit in search_result.points if hit.payload and "text" in hit.payload]

async def get_vector_store_stats(tenant_id: str) -> dict:
    """جلب إحصائيات المستندات لشركة محددة باستخدام Async Scroll API."""
    results, _ = await qdrant.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="tenant_id",
                    match=models.MatchValue(value=str(tenant_id)),
                )
            ]
        ),
        limit=10000,
        with_payload=True,
        with_vectors=False
    )
    
    total_chunks = len(results)
    unique_files = list(set(hit.payload.get("filename") for hit in results if hit.payload and "filename" in hit.payload))
    last_uploaded = unique_files[-1] if unique_files else None
    
    return {
        "total_documents": len(unique_files),
        "total_chunks": total_chunks,
        "last_uploaded_document": last_uploaded,
    }