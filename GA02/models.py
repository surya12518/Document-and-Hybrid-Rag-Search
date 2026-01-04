from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional

class SourceType(str, Enum):
    PDF = "pdf"
    TEXT = "text"
    WIKIPEDIA = "wikipedia"
    WEB = "web"

class DocumentChunk(BaseModel):
    chunk_id: str
    source_id: str
    source_type: SourceType
    title: str
    content: str
    page_number: Optional[int] = None
    url: Optional[str] = None
    
    @property
    def citation_label(self):
        """Returns a citation string, e.g., 'Transformer Notes.pdf (Page 3)'"""
        if self.source_type == SourceType.WEB:
            return f"[Web] {self.title}"
        return f"[Doc] {self.title}" + (f" (Pg {self.page_number})" if self.page_number else "")

class SearchResult(BaseModel):
    query: str
    chunks: List[DocumentChunk]
    is_web_search: bool = False