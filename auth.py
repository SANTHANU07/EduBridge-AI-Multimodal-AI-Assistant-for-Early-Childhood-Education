from __future__ import annotations

import streamlit as st

from db import fetch_user


def initialize_session_state() -> None:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("current_user", None)


def login_user(username: str, password: str) -> bool:
    username = username.strip()
    password = password.strip()
    user = fetch_user(username, password)
    if not user:
        return False

    st.session_state["authenticated"] = True
    st.session_state["current_user"] = user
    return True


def logout_user() -> None:
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = None


def require_login() -> bool:
    initialize_session_state()
    return st.session_state["authenticated"]


def get_current_user():
    return st.session_state.get("current_user")


def render_login_screen() -> None:
    initialize_session_state()

    st.title("EduBridge AI")
    st.subheader("Role-Based School Portal")
    st.write("Log in as a teacher or parent/student to access the correct portal.")

    with st.container(border=True):
        st.markdown("### Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            if login_user(username, password):
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    st.markdown("### Quick Demo Access")
    demo_col1, demo_col2, demo_col3 = st.columns(3)

    if demo_col1.button("Teacher Demo Login", use_container_width=True):
        login_user("teacher_demo", "teacher123")
        st.rerun()

    if demo_col2.button("Aarav Parent Login", use_container_width=True):
        login_user("aarav_parent", "parent123")
        st.rerun()

    if demo_col3.button("Diya Parent Login", use_container_width=True):
        login_user("diya_parent", "parent123")
        st.rerun()

    st.info(
        "Demo logins: `teacher_demo / teacher123`, `aarav_parent / parent123`, `diya_parent / parent123`."
    )
