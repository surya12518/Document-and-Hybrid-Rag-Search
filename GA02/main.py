import streamlit as st
import os
from config import Config
from ingest import load_documents, process_chunks
from vector_store import VectorDB
from rag_engine import RAGEngine

# Page Config
st.set_page_config(page_title="Hybrid RAG Search", layout="wide")

# Initialize Session State
if "rag_engine" not in st.session_state:
    try:
        Config.validate()
        st.session_state.rag_engine = RAGEngine()
    except Exception as e:
        st.error(f"Configuration Error: {e}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: Document Management ---
with st.sidebar:
    st.header("📂 Knowledge Base")
    uploaded_files = st.file_uploader(
        "Upload PDF/Text/MD", 
        type=["pdf", "txt", "md"], 
        accept_multiple_files=True
    )
    
    if st.button("Ingest Documents"):
        if uploaded_files:
            with st.spinner("Processing documents..."):
                raw_docs = load_documents(uploaded_files)
                chunks = process_chunks(raw_docs)
                st.session_state.rag_engine.vector_db.create_index(chunks)
                st.success(f"Indexed {len(chunks)} chunks!")
        else:
            st.warning("Please upload files first.")

    st.markdown("---")
    st.markdown("### Settings")
    force_web = st.checkbox("Force Web Search", value=False)

# --- MAIN CHAT INTERFACE ---
st.title("🧠 Enterprise Hybrid RAG")
st.caption("Auto-routes between internal documents and live web data.")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about your documents or the web..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        engine = st.session_state.rag_engine
        
        # 1. Route
        if force_web:
            mode = "web"
        else:
            with st.spinner("Classifying query..."):
                mode = engine.route_query(prompt)
        
        st.caption(f"🔍 Mode: **{mode.upper()}**")

        # 2. Retrieve
        with st.spinner("Retrieving context..."):
            context_result = engine.retrieve_context(prompt, mode)

        # 3. Generate Stream
        response_placeholder = st.empty()
        full_response = ""
        
        # Stream the answer
        stream = engine.generate_answer(prompt, context_result)
        if isinstance(stream, str): # Error or simple message
             response_placeholder.markdown(stream)
             full_response = stream
        else:
            for chunk in stream:
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)

        # 4. Show Evidence (Transparency)
        with st.expander("📚 View Source Evidence"):
            tabs = st.tabs([f"Source {i+1}" for i in range(len(context_result.chunks))])
            for i, chunk in enumerate(context_result.chunks):
                with tabs[i]:
                    st.markdown(f"**Source:** {chunk.citation_label}")
                    st.info(chunk.content)
                    if chunk.url:
                        st.markdown(f"[Open Link]({chunk.url})")

    # Save Assistant Message
    st.session_state.messages.append({"role": "assistant", "content": full_response})