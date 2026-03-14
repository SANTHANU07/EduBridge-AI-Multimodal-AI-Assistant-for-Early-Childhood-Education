from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from charts import (
    create_attendance_pie_chart,
    create_exam_comparison_chart,
    create_marks_progression_chart,
    create_overall_average_chart,
    create_subject_performance_chart,
)
from data_handler import PerformanceDataHandler
from performance_utils import (
    apply_filters,
    build_summary_cards,
    calculate_subject_comparison,
    generate_rule_based_summary,
    get_latest_attendance_details,
)


def render_performance_dashboard():
    st.title("Student Performance Dashboard")
    st.caption("Track marks, attendance, and progress trends for early learners in a simple teacher-friendly view.")

    # Styling is lightweight so the page still feels like the existing project.
    _inject_dashboard_styles()

    data_handler = PerformanceDataHandler()

    with st.sidebar:
        st.subheader("Dashboard Actions")
        if st.button("Load Dummy Data", use_container_width=True):
            data_handler.replace_with_sample_data()
            st.success("Sample performance data loaded.")

        if st.button("Clear Performance Data", use_container_width=True):
            data_handler.clear_data()
            st.success("Performance records cleared.")

        sample_file_path = Path("sample_data/student_performance_sample.csv").resolve()
        st.caption(f"Sample dataset: {sample_file_path}")

    input_tab, dashboard_tab, records_tab = st.tabs(["Data Input", "Dashboard", "Records"])

    with input_tab:
        _render_input_section(data_handler)

    with dashboard_tab:
        _render_dashboard_section(data_handler)

    with records_tab:
        _render_records_section(data_handler)


def _render_input_section(data_handler: PerformanceDataHandler):
    st.subheader("Upload Performance Data")
    st.write("Upload a CSV or Excel sheet with student marks and attendance records.")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"],
        key="performance_upload",
    )

    if uploaded_file is not None:
        try:
            updated_df = data_handler.import_file(uploaded_file)
            st.success(f"Imported {len(updated_df)} total records successfully.")
        except Exception as exc:
            st.error(f"Unable to import the file: {exc}")

    st.divider()
    st.subheader("Manual Entry")
    st.write("Add a single student result quickly for live demos or classroom updates.")

    with st.form("manual_performance_entry"):
        col1, col2, col3 = st.columns(3)
        student_name = col1.text_input("Student Name", placeholder="Aarav")
        student_id = col2.text_input("Student ID", placeholder="STU-001")
        class_grade = col3.text_input("Class / Grade", placeholder="Grade 2")

        col4, col5, col6 = st.columns(3)
        exam_name = col4.text_input("Exam Name", placeholder="Term 1")
        exam_date = col5.date_input("Exam Date")
        subject = col6.text_input("Subject", placeholder="Math")

        col7, col8, col9 = st.columns(3)
        marks_scored = col7.number_input("Marks Scored", min_value=0.0, value=0.0, step=1.0)
        total_marks = col8.number_input("Total Marks", min_value=1.0, value=100.0, step=1.0)
        attendance_percentage = col9.number_input("Attendance Percentage", min_value=0.0, max_value=100.0, value=85.0, step=1.0)

        submitted = st.form_submit_button("Save Record", use_container_width=True)

        if submitted:
            if not all([student_name.strip(), student_id.strip(), class_grade.strip(), exam_name.strip(), subject.strip()]):
                st.error("Please fill in all text fields before saving.")
            else:
                record = {
                    "student_name": student_name,
                    "student_id": student_id,
                    "class_grade": class_grade,
                    "exam_name": exam_name,
                    "exam_date": exam_date,
                    "subject": subject,
                    "marks_scored": marks_scored,
                    "total_marks": total_marks,
                    "attendance_percentage": attendance_percentage,
                }
                data_handler.append_record(record)
                st.success("Student performance record saved.")


def _render_dashboard_section(data_handler: PerformanceDataHandler):
    df = data_handler.load_data()
    if df.empty:
        st.info("No performance data found. Load the dummy dataset or add records manually to see the dashboard.")
        return

    st.subheader("Performance Analytics")
    student_options = ["All Students"] + sorted(df["student_name"].dropna().unique().tolist())
    selected_student = st.selectbox("Student Selector", student_options)

    student_filtered_df = apply_filters(df, student_name=selected_student)

    subject_options = ["All Subjects"] + sorted(student_filtered_df["subject"].dropna().unique().tolist())
    selected_subject = st.selectbox("Subject Selector", subject_options)

    subject_filtered_df = apply_filters(student_filtered_df, subject=selected_subject)

    exam_options = ["All Exams"] + sorted(subject_filtered_df["exam_name"].dropna().unique().tolist())
    selected_exam = st.selectbox("Exam Selector", exam_options)

    filtered_df = apply_filters(subject_filtered_df, exam_name=selected_exam)

    if filtered_df.empty:
        st.warning("No records matched the current filters.")
        return

    summary_cards = build_summary_cards(filtered_df)
    card_col1, card_col2, card_col3, card_col4 = st.columns(4)
    card_col1.metric("Average Score", summary_cards["average_score"])
    card_col2.metric("Latest Attendance", summary_cards["attendance"])
    card_col3.metric("Subjects Covered", summary_cards["subjects"])
    card_col4.metric("Trend Alert", summary_cards["alert"])

    latest_attendance, attendance_status, show_warning = get_latest_attendance_details(filtered_df)
    attendance_subject = "This group" if selected_student == "All Students" else "This student"
    if show_warning:
        st.warning(f"Attendance is {latest_attendance:.1f}%. {attendance_subject} needs attention because it is below 75%.")
    else:
        st.success(f"Attendance is {latest_attendance:.1f}% with status: {attendance_status}.")

    # Detailed comparison only makes sense when one student is selected.
    detail_df = filtered_df if selected_student != "All Students" else pd.DataFrame()
    comparison_df = calculate_subject_comparison(detail_df)
    summary_text = generate_rule_based_summary(filtered_df, comparison_df)
    st.subheader("AI-style Summary")
    st.write(summary_text)

    top_left, top_right = st.columns(2)
    with top_left:
        st.plotly_chart(create_marks_progression_chart(filtered_df), use_container_width=True)
    with top_right:
        st.plotly_chart(create_attendance_pie_chart(latest_attendance), use_container_width=True)

    middle_left, middle_right = st.columns(2)
    with middle_left:
        st.plotly_chart(create_exam_comparison_chart(comparison_df), use_container_width=True)
    with middle_right:
        st.plotly_chart(create_subject_performance_chart(filtered_df), use_container_width=True)

    st.plotly_chart(create_overall_average_chart(filtered_df), use_container_width=True)

    st.subheader("Comparison Details")
    if selected_student == "All Students":
        st.info("Select one student to see subject-wise current vs previous exam comparisons.")
    elif comparison_df.empty:
        st.info("Comparison details will appear after at least two exam records are available for the same subject.")
    else:
        display_df = comparison_df.copy()
        display_df["difference"] = display_df["difference"].map(lambda value: f"{value:+.2f}")
        display_df["percentage_difference"] = display_df["percentage_difference"].map(lambda value: f"{value:+.2f}%")
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def _render_records_section(data_handler: PerformanceDataHandler):
    st.subheader("Saved Records")
    df = data_handler.load_data()

    if df.empty:
        st.info("No records saved yet.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Current Records as CSV",
        data=csv_data,
        file_name="student_performance_records.csv",
        mime="text/csv",
    )


def _inject_dashboard_styles():
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
        .stMetric [data-testid="stMetricValue"] {
            color: #FACC15 !important;
            font-weight: 700;
        }
        .stMetric [data-testid="stMetricLabel"] {
            color: #E2E8F0 !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background: #1E293B;
            color: #E2E8F0;
            border-radius: 10px;
            padding: 8px 14px;
            border: 1px solid #334155;
        }
        .stTabs [aria-selected="true"] {
            background: #0F766E !important;
            color: #F8FAFC !important;
            border: 1px solid #14B8A6 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
