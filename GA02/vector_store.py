import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document as LC_Document
from config import Config
from models import DocumentChunk

class VectorDB:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model=Config.EMBEDDING_MODEL)
        self.db = None
        self.load_index()

    def create_index(self, chunks: list[DocumentChunk]):
        lc_docs = [
            LC_Document(
                page_content=c.content,
                metadata=c.model_dump(exclude={"content"}) # Store all metadata except content duplication
            ) for c in chunks
        ]
        
        if not lc_docs:
            return

        self.db = FAISS.from_documents(lc_docs, self.embeddings)
        self.db.save_local(Config.VECTOR_DB_PATH)
        print(f"Indexed {len(chunks)} chunks.")

    def load_index(self):
        if os.path.exists(Config.VECTOR_DB_PATH):
            self.db = FAISS.load_local(
                Config.VECTOR_DB_PATH, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )

    def search(self, query: str, k: int = 4) -> list[DocumentChunk]:
        if not self.db:
            return []
        
        results = self.db.similarity_search(query, k=k)
        chunks = []
        for doc in results:
            chunks.append(DocumentChunk(
                chunk_id=doc.metadata.get("chunk_id"),
                source_id=doc.metadata.get("source_id"),
                source_type=doc.metadata.get("source_type"),
                title=doc.metadata.get("title"),
                content=doc.page_content,
                page_number=doc.metadata.get("page_number"),
                url=doc.metadata.get("url")
            ))
        return chunks