from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.services.vector_store import init_vector_store

# تم تصحيح مسار الاستيراد ليقرأ من المجلد الفرعي الفعلي routers والتوافق مع بنية الملفات
from app.api.routers import webhook, dashboard, documents, whatsapp

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: 
    يتم تنفيذ هذا الكود مرة واحدة عند إقلاع الخادم (Startup)
    """
    # تهيئة الـ Vector Store للإنتاج (التأكد من وجود الـ Collection)
    await init_vector_store()
    
    yield  # الخادم يعمل الآن
    
    """
    يتم تنفيذ الكود هنا عند إغلاق الخادم (Shutdown)
    مثل إغلاق اتصالات قاعدة البيانات إذا لزم الأمر
    """
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# إعدادات CORS للسماح لتطبيق Next.js بالاتصال بالـ API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # سيتم تقييدها بدومين الإنتاج لاحقاً
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ربط واجهات الـ API (Routers)
app.include_router(webhook.router, prefix="/api/webhook", tags=["WhatsApp Webhook"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(documents.router, prefix="/api/documents", tags=["Knowledge Base"])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["WhatsApp Settings"])

@app.get("/health")
async def health_check():
    """مسار فحص صحة الخادم (يستخدم من قبل أدوات الـ Monitoring و CI/CD)"""
    return {"status": "healthy", "environment": "production"}