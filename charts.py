from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


CHART_COLORS = {
    "primary": "#2D6A4F",
    "secondary": "#40916C",
    "accent": "#F4A261",
    "warning": "#E76F51",
    "neutral": "#577590",
}


def create_marks_progression_chart(student_df: pd.DataFrame):
    if student_df.empty:
        return _empty_figure("No marks data available yet.")

    progress_df = (
        student_df.sort_values("exam_date")
        .groupby(["exam_date", "exam_name"], as_index=False)["percentage_scored"]
        .mean()
    )

    fig = px.line(
        progress_df,
        x="exam_date",
        y="percentage_scored",
        markers=True,
        text="exam_name",
        title="Marks Progression Across Exams",
    )
    fig.update_traces(line_color=CHART_COLORS["primary"], textposition="top center")
    fig.update_layout(yaxis_title="Average Score (%)", xaxis_title="Exam Date")
    return fig


def create_exam_comparison_chart(comparison_df: pd.DataFrame):
    if comparison_df.empty:
        return _empty_figure("At least two exams are needed for comparison.")

    fig = go.Figure(
        data=[
            go.Bar(
                name="Previous Exam",
                x=comparison_df["subject"],
                y=comparison_df["previous_percentage"],
                marker_color=CHART_COLORS["neutral"],
            ),
            go.Bar(
                name="Current Exam",
                x=comparison_df["subject"],
                y=comparison_df["current_percentage"],
                marker_color=CHART_COLORS["accent"],
            ),
        ]
    )
    fig.update_layout(
        barmode="group",
        title="Current Exam vs Previous Exam",
        xaxis_title="Subject",
        yaxis_title="Score (%)",
    )
    return fig


def create_attendance_pie_chart(attendance_percentage: float):
    attendance_value = max(0, min(float(attendance_percentage), 100))
    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Present", "Remaining"],
                values=[attendance_value, 100 - attendance_value],
                hole=0.58,
                marker_colors=[CHART_COLORS["secondary"], "#D9E2EC"],
            )
        ]
    )
    fig.update_layout(title="Attendance Overview")
    return fig


def create_subject_performance_chart(student_df: pd.DataFrame):
    if student_df.empty:
        return _empty_figure("No subject performance data available.")

    subject_df = (
        student_df.groupby("subject", as_index=False)["percentage_scored"]
        .mean()
        .sort_values("percentage_scored", ascending=False)
    )

    fig = px.bar(
        subject_df,
        x="subject",
        y="percentage_scored",
        color="percentage_scored",
        color_continuous_scale=["#D8F3DC", CHART_COLORS["primary"]],
        title="Subject-wise Performance",
    )
    fig.update_layout(xaxis_title="Subject", yaxis_title="Average Score (%)", coloraxis_showscale=False)
    return fig


def create_overall_average_chart(filtered_df: pd.DataFrame):
    if filtered_df.empty:
        return _empty_figure("No overall average data available.")

    average_df = (
        filtered_df.groupby("exam_name", as_index=False)["percentage_scored"]
        .mean()
        .sort_values("percentage_scored", ascending=False)
    )

    fig = px.bar(
        average_df,
        x="exam_name",
        y="percentage_scored",
        color="percentage_scored",
        color_continuous_scale=["#FEE8C8", CHART_COLORS["accent"]],
        title="Overall Average Marks by Exam",
    )
    fig.update_layout(xaxis_title="Exam", yaxis_title="Average Score (%)", coloraxis_showscale=False)
    return fig


def _empty_figure(message: str):
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, showarrow=False, font={"size": 16})
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(title="Chart Unavailable", plot_bgcolor="white", paper_bgcolor="white")
    return fig
