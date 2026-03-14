from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd


def apply_filters(
    df: pd.DataFrame,
    student_name: str | None = None,
    subject: str | None = None,
    exam_name: str | None = None,
) -> pd.DataFrame:
    filtered_df = df.copy()

    if student_name and student_name != "All Students":
        filtered_df = filtered_df[filtered_df["student_name"] == student_name]

    if subject and subject != "All Subjects":
        filtered_df = filtered_df[filtered_df["subject"] == subject]

    if exam_name and exam_name != "All Exams":
        filtered_df = filtered_df[filtered_df["exam_name"] == exam_name]

    return filtered_df.reset_index(drop=True)


def get_attendance_status(attendance_percentage: float) -> str:
    if attendance_percentage >= 90:
        return "Excellent"
    if attendance_percentage >= 75:
        return "Good"
    return "Needs Attention"


def build_summary_cards(student_df: pd.DataFrame, attendance_threshold: int = 75) -> Dict[str, str]:
    if student_df.empty:
        return {
            "average_score": "0.0%",
            "attendance": "0.0%",
            "subjects": "0",
            "alert": f"Attendance below {attendance_threshold}%",
        }

    latest_attendance = float(student_df.sort_values("exam_date")["attendance_percentage"].iloc[-1])
    average_score = float(student_df["percentage_scored"].mean())

    return {
        "average_score": f"{average_score:.1f}%",
        "attendance": f"{latest_attendance:.1f}%",
        "subjects": str(student_df["subject"].nunique()),
        "alert": "On Track" if latest_attendance >= attendance_threshold else f"Below {attendance_threshold}%",
    }


def calculate_subject_comparison(student_df: pd.DataFrame) -> pd.DataFrame:
    if student_df.empty:
        return pd.DataFrame()

    comparison_rows = []
    for subject, subject_df in student_df.groupby("subject"):
        subject_df = subject_df.sort_values("exam_date")
        if len(subject_df) < 2:
            continue

        current = subject_df.iloc[-1]
        previous = subject_df.iloc[-2]
        previous_percentage = float(previous["percentage_scored"])
        current_percentage = float(current["percentage_scored"])
        difference = current_percentage - previous_percentage
        percentage_difference = 0.0 if previous_percentage == 0 else (difference / previous_percentage) * 100

        if difference > 0:
            status = "Increased"
        elif difference < 0:
            status = "Decreased"
        else:
            status = "Remained the same"

        comparison_rows.append(
            {
                "subject": subject,
                "previous_exam": previous["exam_name"],
                "current_exam": current["exam_name"],
                "previous_percentage": round(previous_percentage, 2),
                "current_percentage": round(current_percentage, 2),
                "difference": round(difference, 2),
                "percentage_difference": round(percentage_difference, 2),
                "status": status,
            }
        )

    return pd.DataFrame(comparison_rows)


def generate_rule_based_summary(student_df: pd.DataFrame, comparison_df: pd.DataFrame) -> str:
    if student_df.empty:
        return "No student performance data is available yet. Upload a file or add a manual entry to start the dashboard."

    summary_lines = []

    if not comparison_df.empty:
        top_change = comparison_df.iloc[comparison_df["difference"].abs().idxmax()]
        summary_lines.append(
            f"{top_change['subject']} marks {top_change['status'].lower()} by {abs(top_change['difference']):.1f} points compared to the previous exam."
        )

    attendance_series = student_df.sort_values("exam_date")["attendance_percentage"]
    latest_attendance = float(attendance_series.iloc[-1])
    attendance_status = get_attendance_status(latest_attendance)
    summary_lines.append(f"Attendance is {latest_attendance:.1f}% and the current status is {attendance_status}.")

    if len(attendance_series) >= 2:
        attendance_change = latest_attendance - float(attendance_series.iloc[-2])
        if attendance_change > 0:
            summary_lines.append(f"Attendance improved by {attendance_change:.1f}% from the previous record.")
        elif attendance_change < 0:
            summary_lines.append(f"Attendance decreased by {abs(attendance_change):.1f}% from the previous record.")

    average_trend = _get_overall_trend(student_df)
    summary_lines.append(f"Overall performance trend is {average_trend}.")

    return " ".join(summary_lines)


def get_latest_attendance_details(student_df: pd.DataFrame, threshold: int = 75) -> Tuple[float, str, bool]:
    if student_df.empty:
        return 0.0, "Needs Attention", True

    latest_attendance = float(student_df.sort_values("exam_date")["attendance_percentage"].iloc[-1])
    status = get_attendance_status(latest_attendance)
    return latest_attendance, status, latest_attendance < threshold


def _get_overall_trend(student_df: pd.DataFrame) -> str:
    progression_df = (
        student_df.sort_values("exam_date")
        .groupby(["exam_date", "exam_name"], as_index=False)["percentage_scored"]
        .mean()
    )

    if len(progression_df) < 2:
        return "steady"

    latest_score = float(progression_df["percentage_scored"].iloc[-1])
    previous_score = float(progression_df["percentage_scored"].iloc[-2])

    if latest_score > previous_score:
        return "upward"
    if latest_score < previous_score:
        return "downward"
    return "steady"
