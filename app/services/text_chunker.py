def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """
    يقسم النص الطويل إلى أجزاء صغيرة (Chunks) لتسهيل بحث الذكاء الاصطناعي فيه.
    - chunk_size: عدد الحروف في كل جزء تقريباً.
    - chunk_overlap: عدد الحروف المتداخلة بين الجزء والجزء لتجنب ضياع المعنى بين الفواصل.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # التحرك للأمام مع ترك مسافة تداخل (overlap)
        start += chunk_size - chunk_overlap
        
    return chunks