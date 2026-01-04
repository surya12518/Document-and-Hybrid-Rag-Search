from typing import Literal
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import Config
from vector_store import VectorDB
from web_search import WebSearcher
from models import SearchResult, SourceType

class RAGEngine:
    def __init__(self):
        self.llm = ChatGroq(model=Config.LLM_MODEL, temperature=0)
        self.vector_db = VectorDB()
        self.web_searcher = WebSearcher()
        self.router_chain = self._build_router()

    def _build_router(self):
        """Classifies query into 'document', 'web', or 'hybrid'."""
        system_prompt = """You are an expert router. 
        - If the query requires specific internal knowledge likely found in uploaded PDFs (technical manuals, internal reports), choose 'document'.
        - If the query requires real-time facts, news, or general knowledge not in static files, choose 'web'.
        - If it might need both (e.g., comparing internal data to market trends), choose 'hybrid'.
        Output only one word: document, web, or hybrid."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{query}")
        ])
        return prompt | self.llm | StrOutputParser()

    def route_query(self, query: str) -> str:
        decision = self.router_chain.invoke({"query": query}).strip().lower()
        print(f"Routing Decision: {decision}")
        return decision

    def retrieve_context(self, query: str, mode: str) -> SearchResult:
        chunks = []
        is_web = False

        if mode in ["document", "hybrid"]:
            chunks.extend(self.vector_db.search(query, k=4))
        
        if mode in ["web", "hybrid"]:
            # If document search yielded nothing or explicitly asked for web
            if not chunks or mode == "web" or mode == "hybrid":
                web_results = self.web_searcher.search(query)
                chunks.extend(web_results)
                is_web = True

        return SearchResult(query=query, chunks=chunks, is_web_search=is_web)

    def generate_answer(self, query: str, context: SearchResult):
        if not context.chunks:
            return "I couldn't find any information in the documents or on the web to answer your question."

        # Format context with IDs for citation
        context_text = "\n\n".join(
            [f"Source [{i+1}] ({c.citation_label}): {c.content}" 
             for i, c in enumerate(context.chunks)]
        )

        system_prompt = """You are a helpful knowledge assistant. 
        Answer the user's question using ONLY the provided context. 
        
        CRITICAL CITATION RULES:
        1. Every statement must be cited using the format [Source ID].
        2. Example: "The transformer architecture uses self-attention [Source 1]."
        3. If the context has conflicting info, mention both.
        4. If the answer is not in the context, state that you don't know.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Context:\n{context}\n\nQuestion: {query}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        return chain.stream({"context": context_text, "query": query})