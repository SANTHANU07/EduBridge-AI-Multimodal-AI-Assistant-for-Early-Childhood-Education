from sentence_transformers import SentenceTransformer

class EmbeddingEngine:

    def __init__(self):
        # HuggingFace embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Embedding model loaded")

    def embed_text(self, text):
        embedding = self.model.encode(text)
        return embedding