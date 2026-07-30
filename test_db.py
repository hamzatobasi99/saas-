import asyncio
from sqlalchemy import text
from app.database.session import AsyncSessionLocal

async def test_connection():
    print("⏳ جاري محاولة الاتصال بقاعدة بيانات Supabase...")
    try:
        # نفتح جلسة اتصال مع قاعدة البيانات
        async with AsyncSessionLocal() as session:
            # نرسل استعلام بسيط جداً
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            
            if value == 1:
                print("✅ تم الاتصال بقاعدة البيانات بنجاح! Supabase يعمل بكفاءة.")
            else:
                print("⚠️ الاتصال تم، لكن النتيجة غير متوقعة.")
    except Exception as e:
        print(f"❌ فشل الاتصال بقاعدة البيانات. تأكد من الرابط وكلمة المرور في ملف .env")
        print(f"تفاصيل الخطأ:\n{e}")

if __name__ == "__main__":
    asyncio.run(test_connection())