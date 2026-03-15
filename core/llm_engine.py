import os
import re

import ollama


class LLMEngine:
    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1")
        self.prefer_cpu = False
        self.max_context_chars = 6000
        print("LLM Engine ready!")

    def generate_response(self, context, query, role):
        trimmed_context = self._trim_context(context)
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
{trimmed_context}

Question:
{query}

Response:
"""
        try:
            response = self._chat_with_fallback(prompt)
            return response["message"]["content"]
        except ollama.ResponseError:
            return self._build_context_fallback(trimmed_context, query, role)

    def _trim_context(self, context):
        if len(context) <= self.max_context_chars:
            return context
        return context[: self.max_context_chars] + "\n\n[Context truncated for stability.]"

    def _chat_with_fallback(self, prompt):
        attempts = []
        if self.prefer_cpu:
            attempts.extend(
                [
                    {"num_gpu": 0, "num_ctx": 1024},
                    {"num_gpu": 0, "num_ctx": 512},
                ]
            )
        else:
            attempts.append(None)
            attempts.extend(
                [
                    {"num_gpu": 0, "num_ctx": 1024},
                    {"num_gpu": 0, "num_ctx": 512},
                ]
            )

        last_error = None
        for options in attempts:
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    options=options,
                )
                if options and options.get("num_gpu") == 0:
                    self.prefer_cpu = True
                return response
            except ollama.ResponseError as exc:
                last_error = exc
                if self._is_memory_error(exc):
                    self.prefer_cpu = True
                    continue
                raise

        raise last_error

    def _is_memory_error(self, exc):
        error_message = str(exc).lower()
        memory_markers = [
            "cuda",
            "runner process has terminated",
            "out of memory",
            "unable to allocate",
            "cudamalloc failed",
        ]
        return any(marker in error_message for marker in memory_markers)

    def _build_context_fallback(self, context, query, role):
        source_files = re.findall(r"Source File:\s*(.+)", context)
        content_blocks = re.findall(r"Content:\n(.*?)(?=\n(?:Source File:|Recently Uploaded File:|Academic Database Context:)|\Z)", context, re.S)
        snippets = []
        for block in content_blocks[:3]:
            cleaned = " ".join(block.strip().split())
            if cleaned:
                snippets.append(cleaned[:220])

        role_intro = {
            "parent": "I could not run the full AI model right now, but here is a helpful answer from the available school data.",
            "teacher": "I could not run the full AI model right now, but here is a concise answer from the available school data.",
            "admin": "I could not run the full AI model right now. Here is a structured fallback answer from the available data.",
        }.get(role, "I could not run the full AI model right now, but here is a fallback answer from the available data.")

        lines = [role_intro]
        if source_files:
            lines.append(f"Relevant source files: {', '.join(dict.fromkeys(source_files[:3]))}.")
        if snippets:
            lines.append("Key extracted information:")
            for snippet in snippets:
                lines.append(f"- {snippet}")
        else:
            lines.append("No detailed extracted content was available for this question.")

        lines.append(f"Question asked: {query}")
        lines.append("If you restart Ollama or free GPU memory, the assistant can generate a fuller answer.")
        return "\n".join(lines)

    def test(self):
        response = self._chat_with_fallback("Say: EduBridge AI is ready!")
        return response["message"]["content"]


if __name__ == "__main__":
    engine = LLMEngine()
    print(engine.test())
