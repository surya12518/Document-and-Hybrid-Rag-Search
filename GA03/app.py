import streamlit as st
import pandas as pd
import plotly.express as px
from ingestion import extract_sections_from_pdf
from rag_engine import ResearchAssistant
import os

# Page Config
st.set_page_config(page_title="ScholarAI: Research Intelligence", layout="wide")

# Initialize Session State
if "assistant" not in st.session_state:
    st.session_state.assistant = ResearchAssistant()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "papers_loaded" not in st.session_state:
    st.session_state.papers_loaded = False

# --- Sidebar: Ingestion ---
st.sidebar.title("📚 Library Management")
uploaded_files = st.sidebar.file_uploader("Upload Research Papers (PDF)", accept_multiple_files=True, type="pdf")

if uploaded_files and st.sidebar.button("Process Papers"):
    with st.spinner("Parsing and Indexing Papers..."):
        papers = []
        # Save temp files for processing
        os.makedirs("temp", exist_ok=True)
        for uploaded_file in uploaded_files:
            path = os.path.join("temp", uploaded_file.name)
            with open(path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Ingest
            paper = extract_sections_from_pdf(path)
            papers.append(paper)
        
        # Index
        success = st.session_state.assistant.ingest_papers(papers)
        if success:
            st.session_state.papers_loaded = True
            st.sidebar.success(f"Successfully indexed {len(papers)} papers!")

# --- Main Interface ---
st.title("🧠 ScholarAI: Research Assistant")

tab1, tab2, tab3 = st.tabs(["🔍 Semantic Search & Chat", "📑 Paper Summarizer", "📈 Trend Analytics"])

# --- Tab 1: Chat (RAG) ---
with tab1:
    if st.session_state.papers_loaded:
        st.write("Ask questions across your entire library (e.g., 'Compare the methodology of paper A and B')")
        
        # Display Chat History
        for msg in st.session_state.chat_history:
            role = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(role):
                st.write(msg["content"])

        # Input
        if prompt := st.chat_input("Ask a research question..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                qa_chain = st.session_state.assistant.get_qa_chain()
                response = qa_chain({"question": prompt, "chat_history": []}) # simplified history handling
                answer = response["answer"]
                st.write(answer)
                
                # Show Sources
                with st.expander("View Source Documents"):
                    for doc in response["source_documents"]:
                        st.markdown(f"**{doc.metadata['title']}** (Section: {doc.metadata['section']})")
                        st.caption(doc.page_content[:200] + "...")
                
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
    else:
        st.info("Please upload and process research papers in the sidebar to begin.")

# --- Tab 2: Summarization ---
with tab2:
    if st.session_state.papers_loaded:
        paper_titles = [p.title for p in st.session_state.assistant.papers.values()]
        selected_paper_title = st.selectbox("Select a paper to analyze", paper_titles)
        
        # Find ID by title (simple reverse lookup for demo)
        selected_id = next(pid for pid, p in st.session_state.assistant.papers.items() if p.title == selected_paper_title)
        
        if st.button("Generate Structured Summary"):
            with st.spinner("Analyzing text structure..."):
                summary = st.session_state.assistant.summarize_paper(selected_id)
                st.markdown(summary)
    else:
        st.write("Upload papers to view summaries.")

# --- Tab 3: Trends ---
with tab3:
    if st.session_state.papers_loaded:
        from analytics import generate_trend_data
        
        st.subheader("Publication Trends")
        papers_list = list(st.session_state.assistant.papers.values())
        df = generate_trend_data(papers_list)
        
        if not df.empty:
            fig = px.bar(df, x="Year", y="Count", color="Topic", title="Papers by Year & Topic")
            st.plotly_chart(fig)
        else:
            st.write("Not enough data to generate trends.")