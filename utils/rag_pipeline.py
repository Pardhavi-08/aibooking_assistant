import os
import streamlit as st

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

from models.embeddings import get_embedding_model

FAISS_DIR = "data/faiss_index"
INDEX_FILE = os.path.join(FAISS_DIR, "index.faiss")

os.makedirs(FAISS_DIR, exist_ok=True)


def build_vector_store(pdf_paths: list):
    embedding_model = get_embedding_model()

    # ✅ Load existing FAISS index ONLY if index file exists
    if os.path.exists(INDEX_FILE):
        return FAISS.load_local(
            FAISS_DIR,
            embedding_model,
            allow_dangerous_deserialization=True
        )

    # ❌ No PDFs → do NOT build
    if not pdf_paths:
        return None

    documents = []
    for path in pdf_paths:
        loader = PyPDFLoader(path)
        documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)

    vector_store = FAISS.from_documents(chunks, embedding_model)
    vector_store.save_local(FAISS_DIR)

    return vector_store


def retrieve_context(query: str, k: int = 4) -> str:
    """
    Retrieve relevant chunks ONLY from user-uploaded PDFs
    """

    # 🛑 Guard 1: No vector store
    if "vector_store" not in st.session_state or st.session_state.vector_store is None:
        return ""

    # 🛑 Guard 2: Ignore greetings / very short queries
    if len(query.strip()) < 5:
        return ""

    vector_store = st.session_state.vector_store

    try:
        docs = vector_store.similarity_search(query, k=k)
    except Exception:
        return ""

    if not docs:
        return ""

    return "\n\n".join(doc.page_content for doc in docs)
