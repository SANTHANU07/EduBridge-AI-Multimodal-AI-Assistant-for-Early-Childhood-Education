from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


REQUIRED_COLUMNS = [
    "student_name",
    "student_id",
    "class_grade",
    "exam_name",
    "exam_date",
    "subject",
    "marks_scored",
    "total_marks",
    "attendance_percentage",
]


class PerformanceDataHandler:
    """CSV-backed storage layer for student performance records."""

    def __init__(self, storage_path: str = "data/student_performance_records.csv"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.storage_path.exists():
            pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(self.storage_path, index=False)

    def load_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.storage_path)
        return self._normalize_dataframe(df)

    def save_data(self, df: pd.DataFrame) -> None:
        normalized_df = self._normalize_dataframe(df)
        normalized_df.to_csv(self.storage_path, index=False)

    def append_record(self, record: Dict) -> pd.DataFrame:
        current_df = self.load_data()
        new_record_df = pd.DataFrame([record])
        combined_df = pd.concat([current_df, new_record_df], ignore_index=True)
        self.save_data(combined_df)
        return self.load_data()

    def import_file(self, file_obj) -> pd.DataFrame:
        file_name = getattr(file_obj, "name", "").lower()

        if file_name.endswith(".csv"):
            uploaded_df = pd.read_csv(file_obj)
        elif file_name.endswith((".xlsx", ".xls")):
            uploaded_df = pd.read_excel(file_obj)
        else:
            raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")

        current_df = self.load_data()
        combined_df = pd.concat([current_df, uploaded_df], ignore_index=True)
        self.save_data(combined_df)
        return self.load_data()

    def replace_with_sample_data(self, sample_path: str = "sample_data/student_performance_sample.csv") -> pd.DataFrame:
        sample_df = pd.read_csv(sample_path)
        self.save_data(sample_df)
        return self.load_data()

    def clear_data(self) -> None:
        pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(self.storage_path, index=False)

    def list_students(self) -> List[str]:
        df = self.load_data()
        if df.empty:
            return []

        students = df["student_name"].dropna().sort_values().unique().tolist()
        return students

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized_df = df.copy()
        normalized_df.columns = [self._normalize_column_name(column) for column in normalized_df.columns]

        # Make sure every required field exists even if the uploaded sheet is incomplete.
        for column in REQUIRED_COLUMNS:
            if column not in normalized_df.columns:
                normalized_df[column] = pd.NA

        normalized_df = normalized_df[REQUIRED_COLUMNS]

        string_columns = [
            "student_name",
            "student_id",
            "class_grade",
            "exam_name",
            "subject",
        ]
        for column in string_columns:
            normalized_df[column] = normalized_df[column].fillna("").astype(str).str.strip()

        normalized_df["exam_date"] = pd.to_datetime(
            normalized_df["exam_date"],
            errors="coerce",
        )

        numeric_columns = ["marks_scored", "total_marks", "attendance_percentage"]
        for column in numeric_columns:
            normalized_df[column] = pd.to_numeric(normalized_df[column], errors="coerce")

        normalized_df["marks_scored"] = normalized_df["marks_scored"].fillna(0).clip(lower=0)
        normalized_df["total_marks"] = normalized_df["total_marks"].fillna(100).replace(0, 100)
        normalized_df["attendance_percentage"] = normalized_df["attendance_percentage"].fillna(0).clip(0, 100)
        # This derived column powers the charts and comparison summaries.
        normalized_df["percentage_scored"] = (
            normalized_df["marks_scored"] / normalized_df["total_marks"] * 100
        ).round(2)

        normalized_df = normalized_df.sort_values(
            by=["student_name", "subject", "exam_date", "exam_name"],
            na_position="last",
        ).reset_index(drop=True)

        return normalized_df

    @staticmethod
    def _normalize_column_name(column_name: str) -> str:
        return (
            str(column_name)
            .strip()
            .lower()
            .replace("%", "percentage")
            .replace("/", "_")
            .replace(" ", "_")
        )
