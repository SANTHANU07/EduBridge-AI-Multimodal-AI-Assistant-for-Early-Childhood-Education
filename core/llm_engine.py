import ollama


class LLMEngine:
    def __init__(self):
        self.model = "llama3.1"
        print("LLM Engine ready!")

    def generate_response(self, context, query, role):
        prompt = f"""
You are EduBridge AI, an assistant for early childhood education.

You are responding to a user with the role: {role}.

Your job is to answer in one of these two ways:

1. If the provided context contains relevant information for the user's question:
   - Answer using the provided context.
   - Mention the source file name if it is available and relevant.
   - Do not invent information not supported by the context.

2. If the provided context clearly says that no relevant uploaded document information was found:
   - Answer using general knowledge.
   - Clearly say that the answer is not based on uploaded files.
   - Do not pretend the answer came from the uploaded documents.

Important rules:
- If role is 'parent': use simple, friendly language.
- If role is 'teacher': use professional language.
- If role is 'admin': give a detailed and structured summary.
- If multiple files are relevant, combine the information clearly.
- Do not make up file names.
- If source file names are present, mention them when useful.
- Keep the answer directly focused on the user's question.

Context:
{context}

Question:
{query}

Response:
"""

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        return response["message"]["content"]

    def test(self):
        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": "Say: EduBridge AI is ready!"
                }
            ]
        )
        return response["message"]["content"]


if __name__ == "__main__":
    engine = LLMEngine()
    print(engine.test())