import os
from dotenv import load_dotenv

load_dotenv()

class VectorStore:
    def __init__(self):
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX")

        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in .env")

        if not index_name:
            raise ValueError("PINECONE_INDEX not found in .env")

        try:
            from pinecone import Pinecone
        except Exception as exc:
            try:
                from pinecone.pinecone import Pinecone
            except Exception as nested_exc:
                raise RuntimeError(
                    "Pinecone SDK could not be loaded. Remove `pinecone-client`, install `pinecone`, "
                    "and verify your virtual environment dependencies."
                ) from nested_exc

        pc = Pinecone(api_key=api_key)
        self.index = pc.Index(index_name)

    def add_vector(self, vector, text, filename):
        self.index.upsert(
            vectors=[
                {
                    "id": str(abs(hash(text + filename))),
                    "values": vector.tolist(),
                    "metadata": {
                        "text": text,
                        "filename": filename
                    }
                }
            ]
        )

    def search(self, vector, top_k=5, min_score=0.0):
        results = self.index.query(
            vector=vector.tolist(),
            top_k=top_k,
            include_metadata=True
        )

        docs = []
        for match in results.matches:
            metadata = match.metadata or {}
            score = getattr(match, "score", 0)

            if score >= min_score:
                docs.append(
                    {
                        "text": metadata.get("text", ""),
                        "filename": metadata.get("filename", "Unknown file"),
                        "score": score
                    }
                )

        return docs

    def clear_all(self):
        self.index.delete(delete_all=True)
