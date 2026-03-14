from __future__ import annotations

import streamlit as st


LANGUAGE_OPTIONS = ["English", "Tamil", "Hindi"]
LANGUAGE_CODE_MAP = {
    "English": "en",
    "Tamil": "ta",
    "Hindi": "hi",
}
LANGUAGE_NAME_MAP = {
    "en": "English",
    "ta": "Tamil",
    "hi": "Hindi",
}


def initialize_language_state() -> None:
    st.session_state.setdefault("assistant_language", "English")
    st.session_state.setdefault("translate_response", True)


def get_selected_language() -> str:
    initialize_language_state()
    return st.session_state["assistant_language"]


def get_selected_language_code() -> str:
    return LANGUAGE_CODE_MAP.get(get_selected_language(), "en")


def set_selected_language(language: str) -> None:
    if language in LANGUAGE_OPTIONS:
        st.session_state["assistant_language"] = language


def get_language_name(code: str) -> str:
    return LANGUAGE_NAME_MAP.get(code, "English")
