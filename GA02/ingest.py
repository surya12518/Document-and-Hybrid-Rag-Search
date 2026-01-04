import re
import uuid
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader, WikipediaLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LC_Document
from models import DocumentChunk, SourceType

def clean_text(text: str) -> str:
    """Removes noise, excessive whitespace, and non-printable characters."""
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII
    return text.strip()

def load_documents(files) -> List[LC_Document]:
    """Loads documents from uploaded Streamlit files or paths."""
    raw_docs = []
    
    for file in files:
        # Handle Streamlit UploadedFile specifically in main app, 
        # here we assume file paths or temp file handling
        file_name = file.name
        temp_path = f"temp_{file_name}"
        
        with open(temp_path, "wb") as f:
            f.write(file.getvalue())

        try:
            if file_name.endswith(".pdf"):
                loader = PyPDFLoader(temp_path)
                docs = loader.load()
                # Tag metadata
                for d in docs:
                    d.metadata["source_id"] = file_name
                    d.metadata["source_type"] = SourceType.PDF.value
                    d.metadata["title"] = file_name
                raw_docs.extend(docs)
            elif file_name.endswith(".txt") or file_name.endswith(".md"):
                loader = TextLoader(temp_path)
                docs = loader.load()
                for d in docs:
                    d.metadata["source_id"] = file_name
                    d.metadata["source_type"] = SourceType.TEXT.value
                    d.metadata["title"] = file_name
                raw_docs.extend(docs)
        finally:
            # Cleanup would happen here in a real OS-level script
            pass
            
    return raw_docs

def process_chunks(raw_docs: List[LC_Document]) -> List[DocumentChunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    
    lc_chunks = splitter.split_documents(raw_docs)
    
    processed_chunks = []
    for chunk in lc_chunks:
        processed_chunks.append(DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            source_id=chunk.metadata.get("source_id", "unknown"),
            source_type=chunk.metadata.get("source_type", SourceType.TEXT),
            title=chunk.metadata.get("title", "Untitled"),
            content=clean_text(chunk.page_content),
            page_number=chunk.metadata.get("page", None)
        ))
    return processed_chunks