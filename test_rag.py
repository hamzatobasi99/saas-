import asyncio
import sys
from pathlib import Path

# إضافة المجلد الرئيسي للمسار
sys.path.append(str(Path(__file__).resolve().parent))

from app.services.text_chunker import chunk_text
from app.services.vector_store import store_chunks_in_db, search_similar_chunks

# المستندات التجريبية
ARABIC_DOC = """
سياسة الضمان والصيانة الخاصة بشركة هيرفي للتكنولوجيا:
تغطي سياسة الضمان جميع الأجهزة الذكية لمدة 24 شهراً من تاريخ الشراء.
يشمل الضمان الأعطال المصنعية والشاشات والبطاريات.
لا يشمل الضمان الأضرار الناتجة عن الغرق أو الكسر العمدي.
لطلب الصيانة يجب التواصل مع الدعم الفني عبر الرقم المجاني 800123.
"""

ENGLISH_DOC = """
Enterprise SaaS Cancellation Policy:
Customers may cancel their subscription at any time with a 30-day prior notice.
Refunds are eligible only within the first 14 days of purchase.
Data retention after cancellation is maintained for 90 days before permanent deletion.
For API rate limits, enterprise tiers support up to 10,000 requests per minute.
"""

MIXED_DOC = """
مشروع WhatsApp Smart AI Agent:
Our system integrates Next.js frontend with Python FastAPI backend.
يدعم النظام البحث الدلالي باستخدام Vector Search و Qdrant.
For deployment, we use Docker containers with automated CI/CD pipelines on GitHub Actions.
"""

async def run_rag_tests():
    print("=" * 60)
    print("🚀 Starting RAG Engine Automated Test Suite")
    print("=" * 60)

    # 1. اختبار المستند العربي
    print("\n[1/3] Testing Arabic Document Retrieval...")
    ar_chunks = chunk_text(ARABIC_DOC, chunk_size=200, chunk_overlap=20)
    await store_chunks_in_db(ar_chunks, "arabic_doc.txt")
    
    ar_results = await search_similar_chunks("كم مدة فترة الضمان وماذا يغطي؟")
    ar_context = " ".join(ar_results)
    
    assert "24 شهراً" in ar_context, "❌ فشل الاختبار العربي: لم يتم استرجاع مدة الضمان!"
    print("✅ Arabic Retrieval Test Passed! Found '24 شهراً' in returned chunks.")

    # 2. اختبار المستند الإنجليزي
    print("\n[2/3] Testing English Document Retrieval...")
    en_chunks = chunk_text(ENGLISH_DOC, chunk_size=200, chunk_overlap=20)
    await store_chunks_in_db(en_chunks, "english_doc.txt")
    
    en_results = await search_similar_chunks("What is the API rate limit for enterprise tiers?")
    en_context = " ".join(en_results)
    
    assert "10,000" in en_context or "rate limits" in en_context, "❌ فشل الاختبار الإنجليزي: لم يتم استرجاع معلومات الـ API limit!"
    print("✅ English Retrieval Test Passed! Found '10,000 requests' in returned chunks.")

    # 3. اختبار المستند المختلط (Mixed Bilingual)
    print("\n[3/3] Testing Mixed Bilingual Document Retrieval...")
    mixed_chunks = chunk_text(MIXED_DOC, chunk_size=200, chunk_overlap=20)
    await store_chunks_in_db(mixed_chunks, "mixed_doc.txt")
    
    mixed_results = await search_similar_chunks("What technology is used for deployment?")
    mixed_context = " ".join(mixed_results)
    
    assert "Docker" in mixed_context, "❌ فشل الاختبار المختلط: لم يتم استرجاع تقنية الـ Deployment!"
    print("✅ Mixed Bilingual Test Passed! Found 'Docker' in returned chunks.")

    print("\n" + "=" * 60)
    print("🎉 ALL RAG ENGINE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_rag_tests())