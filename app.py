import streamlit as st

from ai_assistant import render_ai_assistant_section
from auth import get_current_user, logout_user, render_login_screen, require_login
from db import DB_PATH, initialize_database
from language_utils import initialize_language_state
from parent_portal import render_parent_portal
from performance_dashboard import render_performance_dashboard
from teacher_portal import render_teacher_portal


st.set_page_config(page_title="EduBridge AI", layout="wide")


def main():
    initialize_database()
    initialize_language_state()

    if not require_login():
        render_login_screen()
        return

    user = get_current_user()
    with st.sidebar:
        st.title("EduBridge AI")
        st.caption(f"Logged in as: {user['full_name']}")
        st.caption(f"Role: {user['role']}")
        st.caption(f"Database: {DB_PATH.resolve()}")

        if user["role"] == "teacher":
            page = st.radio(
                "Choose a section",
                [
                    "Multimodal AI Assistant",
                    "Teacher Portal",
                    "Student Performance Dashboard",
                ],
            )
        else:
            page = st.radio(
                "Choose a section",
                [
                    "Multimodal AI Assistant",
                    "Parent / Student Portal",
                ],
            )

        if st.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()

    if user["role"] == "teacher":
        if page == "Teacher Portal":
            render_teacher_portal(user)
        elif page == "Student Performance Dashboard":
            render_performance_dashboard()
        else:
            st.title("Multimodal AI Assistant")
            st.caption("Upload school files and ask questions using EduBridge AI.")
            render_ai_assistant_section(role="teacher", allow_uploads=True)
    else:
        if page == "Parent / Student Portal":
            render_parent_portal(user)
        else:
            st.title("Multimodal AI Assistant")
            st.caption("Upload files, get summaries, and ask AI questions using school files and your linked academic data.")
            render_ai_assistant_section(role="parent", linked_student_id=user.get("linked_student_id"), allow_uploads=True)


if __name__ == "__main__":
    main()
