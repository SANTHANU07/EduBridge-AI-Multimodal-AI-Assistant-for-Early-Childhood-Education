from __future__ import annotations

import asyncio
import inspect
from typing import Optional


class Translator:
    def detect_language(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return "en"

        for char in text:
            code_point = ord(char)
            if 0x0B80 <= code_point <= 0x0BFF:
                return "ta"
            if 0x0900 <= code_point <= 0x097F:
                return "hi"
        return "en"

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        cleaned_text = (text or "").strip()
        if not cleaned_text or source_lang == target_lang:
            return text

        translated_text = self._translate_with_googletrans(cleaned_text, source_lang, target_lang)
        if translated_text:
            return translated_text

        translated_text = self._translate_with_ollama(cleaned_text, source_lang, target_lang)
        if translated_text:
            return translated_text

        return text

    def _translate_with_googletrans(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        try:
            from googletrans import Translator as GoogleTranslator  # type: ignore

            translator = GoogleTranslator()
            result = translator.translate(text, src=source_lang, dest=target_lang)
            if inspect.iscoroutine(result):
                try:
                    result = asyncio.run(result)
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    try:
                        result = loop.run_until_complete(result)
                    finally:
                        loop.close()
            return result.text
        except Exception:
            return None

    def _translate_with_ollama(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        try:
            import ollama

            prompt = (
                f"Translate the following text from {self._language_name(source_lang)} "
                f"to {self._language_name(target_lang)}. Return only the translated text.\n\n{text}"
            )
            response = ollama.chat(
                model="llama3.1",
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"].strip()
        except Exception:
            return None

    @staticmethod
    def _language_name(language_code: str) -> str:
        return {
            "en": "English",
            "ta": "Tamil",
            "hi": "Hindi",
        }.get(language_code, "English")
