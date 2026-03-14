from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from ai_assistant import render_ai_assistant_section
from charts import (
    create_attendance_pie_chart,
    create_exam_comparison_chart,
    create_marks_progression_chart,
    create_overall_average_chart,
    create_subject_performance_chart,
)
from db import get_student_overview
from performance_utils import (
    build_summary_cards,
    calculate_subject_comparison,
    generate_rule_based_summary,
    get_latest_attendance_details,
)


def render_parent_portal(user: dict):
    st.title("Parent / Student Portal")
    st.caption("View homework, marks, attendance, notices, charts, and AI insights for your child.")
    _inject_portal_styles()

    linked_student_id = user.get("linked_student_id")
    overview = get_student_overview(linked_student_id)
    student = overview["student"]
    marks_df = _prepare_marks_chart_df(overview["marks"])
    attendance_df = overview["attendance"].copy()
    homework_df = overview["homework"].copy()
    notices_df = overview["notices"].copy()

    tabs = st.tabs(
        [
            "Student Dashboard",
            "Homework",
            "Marks",
            "Attendance",
            "Charts",
            "AI Summary",
            "AI Assistant",
        ]
    )

    with tabs[0]:
        _render_student_dashboard(student, marks_df, attendance_df, homework_df, notices_df)
    with tabs[1]:
        _render_homework_view(homework_df)
    with tabs[2]:
        _render_marks_view(student, marks_df)
    with tabs[3]:
        _render_attendance_view(attendance_df)
    with tabs[4]:
        _render_charts(marks_df, attendance_df)
    with tabs[5]:
        _render_ai_summary(marks_df, attendance_df)
    with tabs[6]:
        render_ai_assistant_section(role="parent", linked_student_id=linked_student_id, allow_uploads=True)


def _render_student_dashboard(student: dict, marks_df: pd.DataFrame, attendance_df: pd.DataFrame, homework_df: pd.DataFrame, notices_df: pd.DataFrame):
    st.subheader("Student Dashboard")
    info_col1, info_col2, info_col3 = st.columns(3)
    info_col1.metric("Student Name", student.get("student_name", "-"))
    info_col2.metric("Class", student.get("student_class", "-"))
    info_col3.metric("Roll Number", student.get("roll_number", "-"))

    summary_source = marks_df.copy()
    summary_source["attendance_percentage"] = _latest_attendance_value(attendance_df)
    summary_cards = build_summary_cards(summary_source)
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Average Score", summary_cards["average_score"])
    metric_col2.metric("Attendance", summary_cards["attendance"])
    metric_col3.metric("Subjects", summary_cards["subjects"])
    metric_col4.metric("Alert", summary_cards["alert"])

    st.markdown("### Latest Homework")
    st.dataframe(homework_df.head(5), use_container_width=True, hide_index=True)

    st.markdown("### Latest Marks")
    latest_marks = marks_df[["subject", "exam_name", "marks_scored", "total_marks", "percentage_scored"]].tail(5)
    st.dataframe(latest_marks, use_container_width=True, hide_index=True)

    st.markdown("### Notices")
    st.dataframe(notices_df.head(5), use_container_width=True, hide_index=True)


def _render_homework_view(homework_df: pd.DataFrame):
    st.subheader("Homework Viewer")
    if homework_df.empty:
        st.info("No homework posted yet.")
        return
    st.dataframe(homework_df[["subject", "title", "description", "due_date", "posted_by_teacher"]], use_container_width=True, hide_index=True)


def _render_marks_view(student: dict, marks_df: pd.DataFrame):
    st.subheader("Marks Viewer")
    if marks_df.empty:
        st.info("No marks available yet.")
        return

    st.dataframe(
        marks_df[["term_name", "exam_name", "exam_date", "subject", "marks_scored", "total_marks", "percentage_scored"]],
        use_container_width=True,
        hide_index=True,
    )

    report_df = marks_df[["exam_name", "exam_date", "subject", "marks_scored", "total_marks", "percentage_scored"]]
    csv_data = report_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export Student Report (CSV)",
        data=csv_data,
        file_name=f"{student.get('student_name', 'student')}_marks_report.csv",
        mime="text/csv",
    )

    report_text = _build_printable_report(student, marks_df)
    st.download_button(
        "Download Printable Report",
        data=report_text,
        file_name=f"{student.get('student_name', 'student')}_report.txt",
        mime="text/plain",
    )


def _render_attendance_view(attendance_df: pd.DataFrame):
    st.subheader("Attendance Viewer")
    if attendance_df.empty:
        st.info("No attendance records available.")
        return

    attendance_summary = _attendance_summary_df(attendance_df)
    latest_attendance, status, is_low = get_latest_attendance_details(attendance_summary)
    present_count = int((attendance_df["status"] == "Present").sum())
    absent_count = int((attendance_df["status"] == "Absent").sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("Attendance %", f"{latest_attendance:.1f}%")
    col2.metric("Present Days", present_count)
    col3.metric("Absent Days", absent_count)

    if is_low:
        st.warning("Attendance is below 75%. Please monitor it closely.")
    else:
        st.success(f"Attendance status: {status}")

    st.dataframe(attendance_df[["date", "status", "attendance_percentage"]], use_container_width=True, hide_index=True)


def _render_charts(marks_df: pd.DataFrame, attendance_df: pd.DataFrame):
    st.subheader("Charts and Analytics")
    if marks_df.empty:
        st.info("Charts will appear when marks are available.")
        return

    comparison_df = calculate_subject_comparison(marks_df)
    latest_attendance = _latest_attendance_value(attendance_df)

    left_col, right_col = st.columns(2)
    with left_col:
        st.plotly_chart(create_marks_progression_chart(marks_df), use_container_width=True)
    with right_col:
        st.plotly_chart(create_attendance_pie_chart(latest_attendance), use_container_width=True)

    middle_left, middle_right = st.columns(2)
    with middle_left:
        st.plotly_chart(create_exam_comparison_chart(comparison_df), use_container_width=True)
    with middle_right:
        st.plotly_chart(create_subject_performance_chart(marks_df), use_container_width=True)

    st.plotly_chart(create_overall_average_chart(marks_df), use_container_width=True)


def _render_ai_summary(marks_df: pd.DataFrame, attendance_df: pd.DataFrame):
    st.subheader("AI-style Summary")
    if marks_df.empty:
        st.info("Summary will appear when marks are available.")
        return

    comparison_df = calculate_subject_comparison(marks_df)
    summary_source = marks_df.copy()
    summary_source["attendance_percentage"] = _latest_attendance_value(attendance_df)
    summary = generate_rule_based_summary(summary_source, comparison_df)
    st.write(summary)

    low_subjects = marks_df.groupby("subject", as_index=False)["percentage_scored"].mean().sort_values("percentage_scored")
    if not low_subjects.empty and float(low_subjects.iloc[0]["percentage_scored"]) < 60:
        st.error(f"{low_subjects.iloc[0]['subject']} needs attention based on recent scores.")


def _prepare_marks_chart_df(marks_df: pd.DataFrame) -> pd.DataFrame:
    if marks_df.empty:
        return marks_df

    prepared_df = marks_df.copy()
    prepared_df["exam_date"] = pd.to_datetime(prepared_df["exam_date"])
    prepared_df["percentage_scored"] = ((prepared_df["marks_scored"] / prepared_df["total_marks"]) * 100).round(2)
    return prepared_df


def _attendance_summary_df(attendance_df: pd.DataFrame) -> pd.DataFrame:
    if attendance_df.empty:
        return pd.DataFrame(columns=["exam_date", "attendance_percentage"])

    summary_df = attendance_df.copy()
    summary_df["exam_date"] = pd.to_datetime(summary_df["date"])
    summary_df["attendance_percentage"] = pd.to_numeric(summary_df["attendance_percentage"], errors="coerce").fillna(0)
    return summary_df


def _latest_attendance_value(attendance_df: pd.DataFrame) -> float:
    if attendance_df.empty:
        return 0.0
    ordered = attendance_df.copy()
    ordered["date"] = pd.to_datetime(ordered["date"])
    ordered = ordered.sort_values("date")
    return float(pd.to_numeric(ordered["attendance_percentage"], errors="coerce").fillna(0).iloc[-1])


def _build_printable_report(student: dict, marks_df: pd.DataFrame) -> str:
    buffer = io.StringIO()
    buffer.write("EduBridge AI Student Report\n")
    buffer.write("===========================\n")
    buffer.write(f"Student Name: {student.get('student_name', '-')}\n")
    buffer.write(f"Class: {student.get('student_class', '-')}\n")
    buffer.write(f"Roll Number: {student.get('roll_number', '-')}\n\n")
    buffer.write("Marks Summary:\n")
    for row in marks_df.itertuples():
        buffer.write(
            f"- {row.exam_name} | {row.subject} | {row.marks_scored}/{row.total_marks} ({row.percentage_scored}%)\n"
        )
    return buffer.getvalue()


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
