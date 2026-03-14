from core.embeddings import EmbeddingEngine
from core.vector_store import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter


class RAGPipeline:
    def __init__(self):
        self.embedder = EmbeddingEngine()
        self.vector_store = VectorStore()

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def add_document(self, text, filename):
        chunks = self.text_splitter.split_text(text)

        for chunk in chunks:
            if chunk.strip():
                enriched_chunk = f"Filename: {filename}\nContent: {chunk}"
                vector = self.embedder.embed_text(enriched_chunk)
                self.vector_store.add_vector(vector, enriched_chunk, filename)

    def retrieve(self, query):
        query_vector = self.embedder.embed_text(query)
        docs = self.vector_store.search(query_vector, top_k=5, min_score=0.0)
        return docs

    def clear_knowledge_base(self):
        self.vector_store.clear_all()