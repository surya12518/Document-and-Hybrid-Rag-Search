import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    VECTOR_DB_PATH = "faiss_index"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_MODEL = "openai/gpt-oss-120b" # Recommended for complex reasoning
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    @staticmethod
    def validate():
        if not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing.")
        if not Config.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is missing.")