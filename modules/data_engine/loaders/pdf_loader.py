from typing import AsyncIterator
import aiofiles
from pypdf import PdfReader
from io import BytesIO
from .base import BaseLoader, RawDocument

class PDFLoader(BaseLoader):
    def __init__(self):
        super().__init__("literature")
    
    async def load(self, path: str, **kwargs) -> AsyncIterator[RawDocument]:
        async with aiofiles.open(path, 'rb') as f:
            content = await f.read()
        
        reader = PdfReader(BytesIO(content))
        total_pages = len(reader.pages)
        
        # 按页或按段落拆分
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text or len(text.strip()) < 50:
                continue
                
            yield RawDocument(
                doc_id=f"pdf_{kwargs.get('paper_id', 'unknown')}_p{i}",
                source_type="literature",
                raw_content=text,
                metadata={
                    "total_pages": total_pages,
                    "page_num": i,
                    "title": kwargs.get("title", "unknown"),
                    "doi": kwargs.get("doi", None)
                },
                file_path=path
            )