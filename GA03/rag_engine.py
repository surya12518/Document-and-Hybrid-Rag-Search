from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import RetrievalQA, ConversationalRetrievalChain
from langchain_core.prompts import PromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from ingestion import ResearchPaper
from dotenv import load_dotenv
from typing import List

load_dotenv()

# Initialize global LLM components
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
llm = ChatGroq(
    model_name="openai/gpt-oss-120b", 
    temperature=0)

class ResearchAssistant:
    def __init__(self):
        self.vector_store = None
        self.papers = {} # In-memory storage for raw paper objects

    def ingest_papers(self, papers: List[ResearchPaper]):
        """Splits papers into chunks and builds FAISS index."""
        documents = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        for paper in papers:
            self.papers[paper.paper_id] = paper
            
            # Chunking strategy: Attach metadata to every chunk
            for section in paper.sections:
                chunks = text_splitter.create_documents(
                    [section.content], 
                    metadatas=[{
                        "paper_id": paper.paper_id,
                        "title": paper.title,
                        "section": section.title,
                        "year": paper.year
                    }] * len(section.content) # This logic simplifies; ideally split first then assign
                )
                documents.extend(chunks)
        
        if documents:
            self.vector_store = FAISS.from_documents(documents, embeddings)
            return True
        return False

    def get_qa_chain(self):
        """Creates a conversational chain for RAG."""
        if not self.vector_store:
            return None

        memory = InMemorySaver(
            memory_key="chat_history", 
            return_messages=True,
            output_key='answer'
        )
        
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        
        return ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            verbose=True
        )

    def summarize_paper(self, paper_id: str) -> str:
        """Generates a structured summary for a specific paper."""
        paper = self.papers.get(paper_id)
        if not paper: 
            return "Paper not found."

        # Direct LLM call for summarization (Map-Reduce style simplified)
        prompt = f"""
        Analyze the following research paper text and provide a structured summary.
        
        Paper Title: {paper.title}
        Text: {paper.full_text[:15000]}... (truncated)

        Output Format:
        1. **Problem Statement**: What is the paper trying to solve?
        2. **Key Methodology**: How did they solve it?
        3. **Main Results**: What did they find?
        4. **Limitations**: What are the gaps?
        """
        
        response = llm.invoke(prompt)
        return response.content