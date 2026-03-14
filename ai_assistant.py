from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit as st

from db import get_student_db_context
from language_utils import LANGUAGE_OPTIONS, get_selected_language, get_selected_language_code, initialize_language_state, set_selected_language
from ui_translations import t
from utils.translator import Translator


@st.cache_resource
def get_edu_agent():
    from core.agent import EduAgent

    return EduAgent()


@st.cache_resource
def get_doc_processor():
    from processors.doc_processor import DocProcessor

    return DocProcessor()


@st.cache_resource
def get_image_processor():
    from processors.image_processor import ImageProcessor

    return ImageProcessor()


@st.cache_resource
def get_voice_processor():
    from processors.voice_processor import VoiceProcessor

    return VoiceProcessor()


@st.cache_resource
def get_file_handler():
    from utils.file_handler import FileHandler

    return FileHandler()


@st.cache_resource
def get_translator():
    return Translator()


def ask_combined_ai(
    query: str,
    role: str,
    linked_student_id: Optional[int] = None,
    uploaded_text: str = "",
    uploaded_file_name: str = "",
    target_language: str = "en",
) -> str:
    agent = get_edu_agent()
    translator = get_translator()
    detected_language = translator.detect_language(query)
    internal_query = translator.translate_text(query, detected_language, "en") if detected_language != "en" else query
    db_context = get_student_db_context(linked_student_id) if linked_student_id else ""

    retrieved_docs = agent.rag.retrieve(internal_query)
    context_parts = []

    if uploaded_text.strip():
        context_parts.append(
            f"Recently Uploaded File: {uploaded_file_name or 'Uploaded file'}\n"
            f"Use this content first when answering questions about the uploaded file.\n"
            f"Content:\n{uploaded_text[:8000]}"
        )

    if db_context:
        context_parts.append(f"Academic Database Context:\n{db_context}")

    for doc in retrieved_docs:
        context_parts.append(
            f"Source File: {doc['filename']}\nContent:\n{doc['text']}"
        )

    context = "\n\n".join(context_parts) if context_parts else t("no_relevant_info", "English")
    english_response = agent.llm.generate_response(context=context, query=internal_query, role=role)
    if target_language != "en":
        return translator.translate_text(english_response, "en", target_language)
    return english_response


def summarize_uploaded_content(text: str, file_name: str, role: str, target_language: str = "en") -> str:
    cleaned_text = text.strip()
    if not cleaned_text:
        return t("summary_empty", get_selected_language())

    try:
        agent = get_edu_agent()
        summary_prompt = (
            f"Summarize the uploaded file '{file_name}' in simple language. "
            "Explain what the content is about, list the main points, and keep it concise."
        )
        english_summary = agent.llm.generate_response(context=cleaned_text[:6000], query=summary_prompt, role=role)
        if target_language != "en":
            return get_translator().translate_text(english_summary, "en", target_language)
        return english_summary
    except Exception:
        preview = cleaned_text[:500]
        if len(cleaned_text) > 500:
            preview += "..."
        return f"Summary preview based on extracted content:\n\n{preview}"


def _extract_text_from_uploaded_file(uploaded_file, file_path: str, doc_processor, image_processor, voice_processor):
    file_suffix = Path(uploaded_file.name).suffix.lower()

    if uploaded_file.type == "application/pdf" or file_suffix == ".pdf":
        return doc_processor.read_pdf(file_path)

    if "image" in (uploaded_file.type or "") or file_suffix in {".png", ".jpg", ".jpeg"}:
        return image_processor.extract_text(file_path)

    if (
        "audio" in (uploaded_file.type or "")
        or "video" in (uploaded_file.type or "")
        or file_suffix in {".mp3", ".wav", ".m4a", ".mp4", ".mov", ".avi", ".mkv", ".webm"}
    ):
        return voice_processor.transcribe(file_path)

    raise ValueError(t("upload_unsupported", get_selected_language()))


def render_ai_assistant_section(role: str, linked_student_id: Optional[int] = None, allow_uploads: bool = False):
    initialize_language_state()
    is_parent_mode = role == "parent"
    selected_language = get_selected_language() if is_parent_mode else "English"
    selected_language_code = get_selected_language_code() if is_parent_mode else "en"

    st.subheader(t("assistant_title", selected_language))
    st.caption(t("assistant_caption", selected_language))

    if is_parent_mode:
        settings_col1, settings_col2 = st.columns([1, 1])
        selected_language = settings_col1.selectbox(
            t("language_selector", selected_language),
            LANGUAGE_OPTIONS,
            index=LANGUAGE_OPTIONS.index(get_selected_language()),
            key=f"assistant_language_selector_{role}_{linked_student_id or 'all'}",
        )
        set_selected_language(selected_language)
        selected_language_code = get_selected_language_code()
        settings_col2.toggle(
            t("translate_response", selected_language),
            key="translate_response",
            value=st.session_state.get("translate_response", True),
        )
        st.caption(f"{t('selected_language', selected_language)}: {selected_language}")
    else:
        st.session_state["translate_response"] = False

    try:
        agent = get_edu_agent()
        file_handler = get_file_handler()
        doc_processor = get_doc_processor()
        image_processor = get_image_processor()
        voice_processor = get_voice_processor()
    except Exception as exc:
        st.error(f"{t('ai_unavailable', selected_language)}: {exc}")
        return None, None

    session_key_prefix = f"{role}_{linked_student_id or 'all'}"
    uploaded_text_key = f"uploaded_text_{session_key_prefix}"
    uploaded_file_key = f"uploaded_file_{session_key_prefix}"
    st.session_state.setdefault(uploaded_text_key, "")
    st.session_state.setdefault(uploaded_file_key, "")

    if allow_uploads:
        uploaded_file = st.file_uploader(
            t("upload_label", selected_language),
            type=["pdf", "png", "jpg", "jpeg", "wav", "mp3", "m4a", "mp4", "mov", "avi", "mkv", "webm"],
            key=f"portal_upload_{role}",
        )

        if uploaded_file:
            safe_name = uploaded_file.name.replace(" ", "_")
            file_path = file_handler.save_file(uploaded_file, f"uploads/{safe_name}")

            text = _extract_text_from_uploaded_file(
                uploaded_file,
                file_path,
                doc_processor,
                image_processor,
                voice_processor,
            )
            agent.add_knowledge(text, uploaded_file.name)
            st.session_state["portal_voice_query"] = text
            st.session_state[uploaded_text_key] = text
            st.session_state[uploaded_file_key] = uploaded_file.name

            st.success(f"{t('upload_success', selected_language)}: {uploaded_file.name}")
            st.markdown(f"### {t('file_summary', selected_language)}")
            st.write(summarize_uploaded_content(text, uploaded_file.name, role, selected_language_code))
            st.markdown(f"### {t('content_preview', selected_language)}")
            st.text_area(
                t("detected_content", selected_language),
                value=text[:2000],
                height=220,
                key=f"content_preview_{role}_{uploaded_file.name}",
                disabled=True,
            )
            st.info(t("upload_question_hint", selected_language))
            return uploaded_file, file_path

    if st.session_state.get(uploaded_file_key):
        st.caption(f"{t('current_file', selected_language)}: {st.session_state[uploaded_file_key]}")

    question = st.text_input(
        t("ask_ai", selected_language),
        value="",
        key=f"portal_question_{role}_{linked_student_id or 'all'}",
        placeholder=t("ask_placeholder", selected_language),
    )

    if st.button(t("get_ai_answer", selected_language), key=f"ask_ai_{role}_{linked_student_id or 'all'}"):
        if not question.strip():
            st.warning(t("question_required", selected_language))
        else:
            response = ask_combined_ai(
                question,
                role=role,
                linked_student_id=linked_student_id,
                uploaded_text=st.session_state.get(uploaded_text_key, ""),
                uploaded_file_name=st.session_state.get(uploaded_file_key, ""),
                target_language=selected_language_code if is_parent_mode and st.session_state.get("translate_response", True) else "en",
            )
            st.write(f"### {t('ai_response', selected_language)}")
            st.write(response)

    return None, None
