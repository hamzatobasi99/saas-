import io
from pypdf import PdfReader

async def extract_text_from_file(file_content: bytes, filename: str) -> str:
    text = ""
    
    # معالجة الملفات النصية
    if filename.endswith(".txt"):
        try:
            # المحاولة الأولى: الترميز العالمي (وهو الأفضل للعربية)
            text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            # المحاولة الثانية: ترميز الويندوز العربي القديم (شائع جداً في الشركات)
            text = file_content.decode("windows-1256")
            
    # معالجة ملفات PDF
    elif filename.endswith(".pdf"):
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
                
    else:
        raise ValueError(f"Unsupported file format for {filename}. Only TXT and PDF are allowed.")
        
    return text.strip()