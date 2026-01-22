from utils.rag_pipeline import build_or_load_vector_store

vector_store = build_or_load_vector_store(["docs/clinic_info.pdf"])

docs = vector_store.similarity_search("What are the working hours?")

print(docs[0].page_content)
