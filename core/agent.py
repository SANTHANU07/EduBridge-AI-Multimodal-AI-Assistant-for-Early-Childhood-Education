from core.llm_engine import LLMEngine
from core.rag_pipeline import RAGPipeline


class EduAgent:
    def __init__(self):
        self.llm = LLMEngine()
        self.rag = RAGPipeline()

    def add_knowledge(self, text, filename):
        self.rag.add_document(text, filename)

    def clear_knowledge(self):
        self.rag.clear_knowledge_base()

    def ask(self, query, role):
        retrieved_docs = self.rag.retrieve(query)

        context_parts = []

        for doc in retrieved_docs:
            part = f"""
Source File: {doc['filename']}
Content:
{doc['text']}
"""
            context_parts.append(part.strip())

        context = "\n\n".join(context_parts)

        response = self.llm.generate_response(
            context=context,
            query=query,
            role=role
        )

        return response