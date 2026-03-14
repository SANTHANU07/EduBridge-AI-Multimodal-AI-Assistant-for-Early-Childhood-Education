from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from ai_assistant import render_ai_assistant_section
from db import (
    add_attendance,
    add_homework,
    add_marks,
    add_notice,
    add_uploaded_file,
    bulk_upsert_attendance,
    delete_attendance,
    delete_homework,
    delete_marks,
    delete_notice,
    get_attendance,
    get_homework,
    get_marks,
    get_notices,
    get_recent_activity,
    get_teacher_dashboard_stats,
    get_uploaded_files,
    list_students,
    update_attendance,
    update_homework,
    update_marks,
    update_notice,
)


def render_teacher_portal(user: dict):
    st.title("Teacher Portal")
    st.caption("Manage homework, marks, attendance, notices, and classroom files from one place.")
    _inject_portal_styles()

    tabs = st.tabs(
        [
            "Dashboard",
            "Homework",
            "Marks",
            "Attendance",
            "Notices",
            "Uploads",
            "AI Assistant",
        ]
    )

    with tabs[0]:
        _render_teacher_dashboard()
    with tabs[1]:
        _render_homework_management(user)
    with tabs[2]:
        _render_marks_management(user)
    with tabs[3]:
        _render_attendance_management(user)
    with tabs[4]:
        _render_notice_management(user)
    with tabs[5]:
        _render_uploads(user)
    with tabs[6]:
        render_ai_assistant_section(role="teacher", allow_uploads=True)


def _render_teacher_dashboard():
    stats = get_teacher_dashboard_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", stats["total_students"])
    col2.metric("Homework Posted", stats["total_homework"])
    col3.metric("Marks Entries", stats["total_marks"])
    col4.metric("Attendance Updates", stats["attendance_updates"])

    st.subheader("Recent Activity Feed")
    activity_df = get_recent_activity()
    if activity_df.empty:
        st.info("No recent activity yet.")
    else:
        st.dataframe(activity_df, use_container_width=True, hide_index=True)

    st.subheader("Class Snapshot")
    students_df = list_students()
    marks_df = get_marks()
    attendance_df = get_attendance()
    overview_rows = []

    for student in students_df.itertuples():
        student_marks = marks_df[marks_df["student_id"] == student.id]
        student_attendance = attendance_df[attendance_df["student_id"] == student.id]
        average_score = (
            ((student_marks["marks_scored"] / student_marks["total_marks"]) * 100).mean()
            if not student_marks.empty
            else 0.0
        )
        latest_attendance = (
            float(student_attendance.sort_values("date")["attendance_percentage"].iloc[-1])
            if not student_attendance.empty
            else 0.0
        )
        overview_rows.append(
            {
                "Student": student.student_name,
                "Class": student.student_class,
                "Roll Number": student.roll_number,
                "Average Marks (%)": round(average_score, 2),
                "Latest Attendance (%)": latest_attendance,
            }
        )

    st.dataframe(pd.DataFrame(overview_rows), use_container_width=True, hide_index=True)


def _render_homework_management(user: dict):
    st.subheader("Homework Management")
    students_df = list_students()
    class_options = sorted(students_df["student_class"].unique().tolist())

    with st.form("homework_form"):
        col1, col2 = st.columns(2)
        class_name = col1.selectbox("Class", class_options)
        subject = col2.text_input("Subject", placeholder="Math")
        title = st.text_input("Title")
        description = st.text_area("Description")
        due_date = st.date_input("Due Date", min_value=date.today())
        if st.form_submit_button("Post Homework", use_container_width=True):
            add_homework(class_name, subject, title, description, str(due_date), user["full_name"])
            st.success("Homework posted.")
            st.rerun()

    homework_df = get_homework()
    st.dataframe(homework_df, use_container_width=True, hide_index=True)

    if homework_df.empty:
        return

    selected_id = st.selectbox("Homework Record ID", homework_df["id"].tolist(), key="teacher_homework_id")
    selected_row = homework_df[homework_df["id"] == selected_id].iloc[0]

    with st.form("homework_edit_form"):
        edit_class = st.selectbox("Edit Class", class_options, index=class_options.index(selected_row["class_name"]), key="edit_homework_class_name")
        edit_subject = st.text_input("Edit Subject", value=selected_row["subject"])
        edit_title = st.text_input("Edit Title", value=selected_row["title"])
        edit_description = st.text_area("Edit Description", value=selected_row["description"])
        edit_due = st.date_input("Edit Due Date", value=pd.to_datetime(selected_row["due_date"]).date(), key="edit_due_date")
        if st.form_submit_button("Update Homework", use_container_width=True):
            update_homework(selected_id, edit_class, edit_subject, edit_title, edit_description, str(edit_due))
            st.success("Homework updated.")
            st.rerun()

    if st.button("Delete Homework", key="teacher_delete_homework", use_container_width=True):
        delete_homework(selected_id)
        st.success("Homework deleted.")
        st.rerun()


def _render_marks_management(user: dict):
    st.subheader("Marks Entry")
    students_df = list_students()
    student_labels = {f"{row.student_name} ({row.student_class})": row.id for row in students_df.itertuples()}

    with st.form("marks_form"):
        selected_student = st.selectbox("Student", list(student_labels.keys()))
        col1, col2, col3 = st.columns(3)
        subject = col1.text_input("Subject", placeholder="English")
        exam_name = col2.text_input("Exam Name", placeholder="Term 1")
        exam_date = col3.date_input("Exam Date")
        col4, col5, col6 = st.columns(3)
        term_name = col4.text_input("Term Name", placeholder="Term 1")
        marks_scored = col5.number_input("Marks Scored", min_value=0.0, value=0.0, step=1.0)
        total_marks = col6.number_input("Total Marks", min_value=1.0, value=100.0, step=1.0)
        if st.form_submit_button("Save Marks", use_container_width=True):
            add_marks(student_labels[selected_student], subject, exam_name, str(exam_date), marks_scored, total_marks, term_name, user["full_name"])
            st.success("Marks saved.")
            st.rerun()

    marks_df = get_marks()
    if not marks_df.empty:
        marks_df["percentage"] = ((marks_df["marks_scored"] / marks_df["total_marks"]) * 100).round(2)
    st.dataframe(marks_df, use_container_width=True, hide_index=True)

    if marks_df.empty:
        return

    selected_id = st.selectbox("Marks Record ID", marks_df["id"].tolist(), key="teacher_marks_id")
    selected_row = marks_df[marks_df["id"] == selected_id].iloc[0]
    current_label = next(label for label, value in student_labels.items() if value == selected_row["student_id"])
    label_list = list(student_labels.keys())

    with st.form("marks_edit_form"):
        edit_student = st.selectbox("Edit Student", label_list, index=label_list.index(current_label), key="edit_marks_student")
        col1, col2, col3 = st.columns(3)
        edit_subject = col1.text_input("Edit Subject", value=selected_row["subject"])
        edit_exam_name = col2.text_input("Edit Exam Name", value=selected_row["exam_name"])
        edit_exam_date = col3.date_input("Edit Exam Date", value=pd.to_datetime(selected_row["exam_date"]).date(), key="edit_marks_exam_date")
        col4, col5, col6 = st.columns(3)
        edit_term = col4.text_input("Edit Term Name", value=selected_row["term_name"])
        edit_scored = col5.number_input("Edit Marks Scored", min_value=0.0, value=float(selected_row["marks_scored"]), step=1.0)
        edit_total = col6.number_input("Edit Total Marks", min_value=1.0, value=float(selected_row["total_marks"]), step=1.0)
        if st.form_submit_button("Update Marks", use_container_width=True):
            update_marks(selected_id, student_labels[edit_student], edit_subject, edit_exam_name, str(edit_exam_date), edit_scored, edit_total, edit_term)
            st.success("Marks updated.")
            st.rerun()

    if st.button("Delete Marks", key="teacher_delete_marks", use_container_width=True):
        delete_marks(selected_id)
        st.success("Marks deleted.")
        st.rerun()


def _render_attendance_management(user: dict):
    st.subheader("Attendance Entry")
    students_df = list_students()
    student_labels = {f"{row.student_name} ({row.student_class})": row.id for row in students_df.itertuples()}

    single_tab, bulk_tab = st.tabs(["Single Entry", "Bulk Attendance"])

    with single_tab:
        with st.form("attendance_form"):
            student_label = st.selectbox("Student", list(student_labels.keys()))
            col1, col2, col3 = st.columns(3)
            attendance_date = col1.date_input("Date", value=date.today())
            status = col2.selectbox("Status", ["Present", "Absent"])
            attendance_percentage = col3.number_input("Attendance Percentage", min_value=0.0, max_value=100.0, value=85.0, step=1.0)
            if st.form_submit_button("Save Attendance", use_container_width=True):
                add_attendance(student_labels[student_label], str(attendance_date), status, attendance_percentage, user["full_name"])
                st.success("Attendance saved.")
                st.rerun()

    with bulk_tab:
        bulk_date = st.date_input("Bulk Attendance Date", value=date.today(), key="bulk_attendance_date")
        statuses = {}
        for row in students_df.itertuples():
            col1, col2 = st.columns([3, 2])
            col1.write(f"{row.student_name} - {row.student_class}")
            statuses[row.id] = col2.selectbox(
                f"Status for {row.student_name}",
                ["Present", "Absent"],
                key=f"bulk_status_{row.id}",
            )
        if st.button("Save Bulk Attendance", use_container_width=True):
            rows = [
                {
                    "student_id": student_id,
                    "date": str(bulk_date),
                    "status": status,
                    "attendance_percentage": 100.0 if status == "Present" else 0.0,
                }
                for student_id, status in statuses.items()
            ]
            bulk_upsert_attendance(rows, user["full_name"])
            st.success("Bulk attendance saved.")
            st.rerun()

    attendance_df = get_attendance()
    st.dataframe(attendance_df, use_container_width=True, hide_index=True)

    if attendance_df.empty:
        return

    selected_id = st.selectbox("Attendance Record ID", attendance_df["id"].tolist(), key="teacher_attendance_id")
    selected_row = attendance_df[attendance_df["id"] == selected_id].iloc[0]
    current_label = next(label for label, value in student_labels.items() if value == selected_row["student_id"])
    label_list = list(student_labels.keys())

    with st.form("attendance_edit_form"):
        edit_student = st.selectbox("Edit Student", label_list, index=label_list.index(current_label), key="edit_attendance_student")
        col1, col2, col3 = st.columns(3)
        edit_date = col1.date_input("Edit Date", value=pd.to_datetime(selected_row["date"]).date(), key="edit_attendance_record_date")
        edit_status = col2.selectbox("Edit Status", ["Present", "Absent"], index=0 if selected_row["status"] == "Present" else 1)
        edit_percentage = col3.number_input("Edit Attendance Percentage", min_value=0.0, max_value=100.0, value=float(selected_row["attendance_percentage"]), step=1.0)
        if st.form_submit_button("Update Attendance", use_container_width=True):
            update_attendance(selected_id, student_labels[edit_student], str(edit_date), edit_status, edit_percentage)
            st.success("Attendance updated.")
            st.rerun()

    if st.button("Delete Attendance", key="teacher_delete_attendance", use_container_width=True):
        delete_attendance(selected_id)
        st.success("Attendance deleted.")
        st.rerun()


def _render_notice_management(user: dict):
    st.subheader("Notice and Announcement Posting")
    class_options = sorted(list_students()["student_class"].unique().tolist())

    with st.form("notice_form"):
        title = st.text_input("Notice Title")
        class_name = st.selectbox("Class", class_options)
        description = st.text_area("Description")
        if st.form_submit_button("Post Notice", use_container_width=True):
            add_notice(title, description, class_name, user["full_name"])
            st.success("Notice posted.")
            st.rerun()

    notice_df = get_notices()
    st.dataframe(notice_df, use_container_width=True, hide_index=True)

    if notice_df.empty:
        return

    selected_id = st.selectbox("Notice Record ID", notice_df["id"].tolist(), key="teacher_notice_id")
    selected_row = notice_df[notice_df["id"] == selected_id].iloc[0]

    with st.form("notice_edit_form"):
        edit_title = st.text_input("Edit Title", value=selected_row["title"])
        edit_class = st.selectbox("Edit Class", class_options, index=class_options.index(selected_row["class_name"]), key="edit_notice_class")
        edit_description = st.text_area("Edit Description", value=selected_row["description"])
        if st.form_submit_button("Update Notice", use_container_width=True):
            update_notice(selected_id, edit_title, edit_description, edit_class)
            st.success("Notice updated.")
            st.rerun()

    if st.button("Delete Notice", key="teacher_delete_notice", use_container_width=True):
        delete_notice(selected_id)
        st.success("Notice deleted.")
        st.rerun()


def _render_uploads(user: dict):
    st.subheader("Class File Uploads")
    class_options = sorted(list_students()["student_class"].unique().tolist())
    class_name = st.selectbox("Class for File", class_options, key="teacher_upload_class")

    uploaded_file, file_path = render_ai_assistant_section(role="teacher_upload", allow_uploads=True)
    if uploaded_file and file_path:
        add_uploaded_file(uploaded_file.name, uploaded_file.type or "unknown", class_name, user["full_name"], file_path)
        st.success("File metadata stored and indexed for AI use.")

    files_df = get_uploaded_files()
    if not files_df.empty:
        st.dataframe(files_df, use_container_width=True, hide_index=True)


def _inject_portal_styles():
    st.markdown(
        """
        <style>
        .stMetric {
            background: #1F2937;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 0.8rem;
        }
        .stMetric label,
        .stMetric div {
            color: #F8FAFC !important;
        }
        .stTabs [data-baseweb="tab"] {
            background: #111827;
            color: #E2E8F0;
            border: 1px solid #334155;
            border-radius: 10px;
        }
        .stTabs [aria-selected="true"] {
            background: #0F766E !important;
            color: #F8FAFC !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
