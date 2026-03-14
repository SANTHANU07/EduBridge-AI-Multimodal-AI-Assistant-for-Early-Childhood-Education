from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd


DB_PATH = Path("data/edubridge.db")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                student_class TEXT NOT NULL,
                roll_number TEXT NOT NULL UNIQUE,
                parent_name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                linked_student_id INTEGER,
                full_name TEXT NOT NULL,
                FOREIGN KEY (linked_student_id) REFERENCES students (id)
            );

            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                teacher_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                subject_specialty TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                due_date TEXT NOT NULL,
                posted_by_teacher TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                exam_name TEXT NOT NULL,
                exam_date TEXT NOT NULL,
                marks_scored REAL NOT NULL,
                total_marks REAL NOT NULL,
                term_name TEXT NOT NULL,
                entered_by_teacher TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id)
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                attendance_percentage REAL,
                updated_by_teacher TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id)
            );

            CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                class_name TEXT NOT NULL,
                created_by_teacher TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS uploaded_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                class_name TEXT,
                uploaded_by_teacher TEXT NOT NULL,
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

    seed_sample_data()


def seed_sample_data() -> None:
    with get_connection() as conn:
        user_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        if user_count:
            return

        students = [
            ("Aarav", "Grade 2", "G2-01", "Priya"),
            ("Diya", "Grade 2", "G2-02", "Karthik"),
            ("Ishaan", "Grade 1", "G1-01", "Meera"),
        ]
        conn.executemany(
            """
            INSERT INTO students (student_name, student_class, roll_number, parent_name)
            VALUES (?, ?, ?, ?)
            """,
            students,
        )

        student_rows = conn.execute("SELECT id, student_name FROM students ORDER BY id").fetchall()
        student_map = {row["student_name"]: row["id"] for row in student_rows}

        users = [
            ("teacher_demo", hash_password("teacher123"), "teacher", None, "Anitha Teacher"),
            ("aarav_parent", hash_password("parent123"), "parent_student", student_map["Aarav"], "Priya"),
            ("diya_parent", hash_password("parent123"), "parent_student", student_map["Diya"], "Karthik"),
        ]
        conn.executemany(
            """
            INSERT INTO users (username, password, role, linked_student_id, full_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            users,
        )

        teacher_user_id = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            ("teacher_demo",),
        ).fetchone()["id"]

        conn.execute(
            """
            INSERT INTO teachers (user_id, teacher_name, class_name, subject_specialty)
            VALUES (?, ?, ?, ?)
            """,
            (teacher_user_id, "Anitha Teacher", "Grade 1-2", "Math and English"),
        )

        today = date.today()
        created_at = datetime.now().isoformat(timespec="seconds")

        homework_rows = [
            ("Grade 2", "Math", "Number Bonds Worksheet", "Complete page 3 and revise number bonds up to 20.", str(today + timedelta(days=1)), "Anitha Teacher", created_at),
            ("Grade 2", "English", "Reading Practice", "Read the short story aloud with a parent and note two new words.", str(today + timedelta(days=2)), "Anitha Teacher", created_at),
            ("Grade 1", "Science", "Plants Around Us", "Draw two plants you see near home and label them.", str(today + timedelta(days=3)), "Anitha Teacher", created_at),
        ]
        conn.executemany(
            """
            INSERT INTO homework (class_name, subject, title, description, due_date, posted_by_teacher, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            homework_rows,
        )

        marks_rows = [
            (student_map["Aarav"], "Math", "Term 1", "2025-06-10", 72, 100, "Term 1", "Anitha Teacher", created_at),
            (student_map["Aarav"], "English", "Term 1", "2025-06-10", 68, 100, "Term 1", "Anitha Teacher", created_at),
            (student_map["Aarav"], "Math", "Term 2", "2025-09-15", 84, 100, "Term 2", "Anitha Teacher", created_at),
            (student_map["Aarav"], "English", "Term 2", "2025-09-15", 75, 100, "Term 2", "Anitha Teacher", created_at),
            (student_map["Diya"], "Math", "Term 1", "2025-06-10", 80, 100, "Term 1", "Anitha Teacher", created_at),
            (student_map["Diya"], "Science", "Term 1", "2025-06-10", 78, 100, "Term 1", "Anitha Teacher", created_at),
            (student_map["Diya"], "Math", "Term 2", "2025-09-15", 88, 100, "Term 2", "Anitha Teacher", created_at),
            (student_map["Diya"], "Science", "Term 2", "2025-09-15", 85, 100, "Term 2", "Anitha Teacher", created_at),
            (student_map["Ishaan"], "Math", "Term 1", "2025-06-10", 61, 100, "Term 1", "Anitha Teacher", created_at),
            (student_map["Ishaan"], "English", "Term 1", "2025-06-10", 65, 100, "Term 1", "Anitha Teacher", created_at),
            (student_map["Ishaan"], "Math", "Term 2", "2025-09-15", 69, 100, "Term 2", "Anitha Teacher", created_at),
            (student_map["Ishaan"], "English", "Term 2", "2025-09-15", 70, 100, "Term 2", "Anitha Teacher", created_at),
        ]
        conn.executemany(
            """
            INSERT INTO marks (student_id, subject, exam_name, exam_date, marks_scored, total_marks, term_name, entered_by_teacher, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            marks_rows,
        )

        attendance_rows = []
        for offset in range(10):
            attendance_date = today - timedelta(days=offset)
            attendance_rows.extend(
                [
                    (student_map["Aarav"], str(attendance_date), "Present" if offset != 3 else "Absent", 90, "Anitha Teacher"),
                    (student_map["Diya"], str(attendance_date), "Present" if offset != 5 else "Absent", 92, "Anitha Teacher"),
                    (student_map["Ishaan"], str(attendance_date), "Present" if offset not in {1, 7} else "Absent", 74, "Anitha Teacher"),
                ]
            )
        conn.executemany(
            """
            INSERT INTO attendance (student_id, date, status, attendance_percentage, updated_by_teacher)
            VALUES (?, ?, ?, ?, ?)
            """,
            attendance_rows,
        )

        notice_rows = [
            ("Parent-Teacher Meeting", "Meeting scheduled on Friday at 4 PM in the kindergarten hall.", "Grade 2", "Anitha Teacher", created_at),
            ("Worksheet Reminder", "Please bring the phonics worksheet in the blue folder tomorrow.", "Grade 1", "Anitha Teacher", created_at),
        ]
        conn.executemany(
            """
            INSERT INTO notices (title, description, class_name, created_by_teacher, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            notice_rows,
        )


def query_df(query: str, params: Iterable | None = None) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params or [])


def fetch_user(username: str, password: str) -> Optional[Dict]:
    hashed_password = hash_password(password)
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT users.*, students.student_name, students.student_class
            FROM users
            LEFT JOIN students ON students.id = users.linked_student_id
            WHERE username = ? AND password = ?
            """,
            (username, hashed_password),
        ).fetchone()
    return dict(row) if row else None


def list_students() -> pd.DataFrame:
    return query_df("SELECT * FROM students ORDER BY student_class, student_name")


def get_student(student_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return dict(row) if row else None


def get_teacher_dashboard_stats() -> Dict[str, int]:
    with get_connection() as conn:
        return {
            "total_students": conn.execute("SELECT COUNT(*) FROM students").fetchone()[0],
            "total_homework": conn.execute("SELECT COUNT(*) FROM homework").fetchone()[0],
            "total_marks": conn.execute("SELECT COUNT(*) FROM marks").fetchone()[0],
            "attendance_updates": conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0],
        }


def get_recent_activity(limit: int = 8) -> pd.DataFrame:
    query = """
        SELECT 'Homework' AS activity_type, title AS activity_title, created_at AS activity_time, class_name AS context
        FROM homework
        UNION ALL
        SELECT 'Notice' AS activity_type, title AS activity_title, created_at AS activity_time, class_name AS context
        FROM notices
        UNION ALL
        SELECT 'Marks' AS activity_type, exam_name || ' - ' || subject AS activity_title, created_at AS activity_time, CAST(student_id AS TEXT) AS context
        FROM marks
        ORDER BY activity_time DESC
        LIMIT ?
    """
    return query_df(query, [limit])


def get_homework(class_name: str | None = None) -> pd.DataFrame:
    if class_name:
        return query_df("SELECT * FROM homework WHERE class_name = ? ORDER BY due_date ASC, created_at DESC", [class_name])
    return query_df("SELECT * FROM homework ORDER BY due_date ASC, created_at DESC")


def add_homework(class_name: str, subject: str, title: str, description: str, due_date: str, teacher_name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO homework (class_name, subject, title, description, due_date, posted_by_teacher, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (class_name, subject, title, description, due_date, teacher_name, datetime.now().isoformat(timespec="seconds")),
        )


def update_homework(record_id: int, class_name: str, subject: str, title: str, description: str, due_date: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE homework
            SET class_name = ?, subject = ?, title = ?, description = ?, due_date = ?
            WHERE id = ?
            """,
            (class_name, subject, title, description, due_date, record_id),
        )


def delete_homework(record_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM homework WHERE id = ?", (record_id,))


def get_marks(student_id: int | None = None) -> pd.DataFrame:
    query = """
        SELECT marks.*, students.student_name, students.student_class, students.roll_number
        FROM marks
        JOIN students ON students.id = marks.student_id
    """
    params: List = []
    if student_id:
        query += " WHERE marks.student_id = ?"
        params.append(student_id)
    query += " ORDER BY exam_date ASC, subject ASC"
    return query_df(query, params)


def add_marks(student_id: int, subject: str, exam_name: str, exam_date: str, marks_scored: float, total_marks: float, term_name: str, teacher_name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO marks (student_id, subject, exam_name, exam_date, marks_scored, total_marks, term_name, entered_by_teacher, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (student_id, subject, exam_name, exam_date, marks_scored, total_marks, term_name, teacher_name, datetime.now().isoformat(timespec="seconds")),
        )


def update_marks(record_id: int, student_id: int, subject: str, exam_name: str, exam_date: str, marks_scored: float, total_marks: float, term_name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE marks
            SET student_id = ?, subject = ?, exam_name = ?, exam_date = ?, marks_scored = ?, total_marks = ?, term_name = ?
            WHERE id = ?
            """,
            (student_id, subject, exam_name, exam_date, marks_scored, total_marks, term_name, record_id),
        )


def delete_marks(record_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM marks WHERE id = ?", (record_id,))


def get_attendance(student_id: int | None = None) -> pd.DataFrame:
    query = """
        SELECT attendance.*, students.student_name, students.student_class, students.roll_number
        FROM attendance
        JOIN students ON students.id = attendance.student_id
    """
    params: List = []
    if student_id:
        query += " WHERE attendance.student_id = ?"
        params.append(student_id)
    query += " ORDER BY date DESC, student_name ASC"
    return query_df(query, params)


def add_attendance(student_id: int, attendance_date: str, status: str, attendance_percentage: float, teacher_name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO attendance (student_id, date, status, attendance_percentage, updated_by_teacher)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_id, attendance_date, status, attendance_percentage, teacher_name),
        )


def update_attendance(record_id: int, student_id: int, attendance_date: str, status: str, attendance_percentage: float) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE attendance
            SET student_id = ?, date = ?, status = ?, attendance_percentage = ?
            WHERE id = ?
            """,
            (student_id, attendance_date, status, attendance_percentage, record_id),
        )


def delete_attendance(record_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM attendance WHERE id = ?", (record_id,))


def bulk_upsert_attendance(rows: List[Dict], teacher_name: str) -> None:
    with get_connection() as conn:
        for row in rows:
            conn.execute(
                """
                INSERT INTO attendance (student_id, date, status, attendance_percentage, updated_by_teacher)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    row["student_id"],
                    row["date"],
                    row["status"],
                    row["attendance_percentage"],
                    teacher_name,
                ),
            )


def get_notices(class_name: str | None = None) -> pd.DataFrame:
    if class_name:
        return query_df("SELECT * FROM notices WHERE class_name = ? ORDER BY created_at DESC", [class_name])
    return query_df("SELECT * FROM notices ORDER BY created_at DESC")


def add_notice(title: str, description: str, class_name: str, teacher_name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO notices (title, description, class_name, created_by_teacher, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, description, class_name, teacher_name, datetime.now().isoformat(timespec="seconds")),
        )


def update_notice(record_id: int, title: str, description: str, class_name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE notices
            SET title = ?, description = ?, class_name = ?
            WHERE id = ?
            """,
            (title, description, class_name, record_id),
        )


def delete_notice(record_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM notices WHERE id = ?", (record_id,))


def add_uploaded_file(file_name: str, file_type: str, class_name: str, teacher_name: str, file_path: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO uploaded_files (file_name, file_type, class_name, uploaded_by_teacher, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (file_name, file_type, class_name, teacher_name, file_path, datetime.now().isoformat(timespec="seconds")),
        )


def get_uploaded_files(class_name: str | None = None) -> pd.DataFrame:
    if class_name:
        return query_df("SELECT * FROM uploaded_files WHERE class_name = ? ORDER BY created_at DESC", [class_name])
    return query_df("SELECT * FROM uploaded_files ORDER BY created_at DESC")


def get_student_overview(student_id: int) -> Dict[str, pd.DataFrame | Dict]:
    student = get_student(student_id)
    marks_df = get_marks(student_id)
    attendance_df = get_attendance(student_id)
    class_name = student["student_class"] if student else None
    homework_df = get_homework(class_name)
    notices_df = get_notices(class_name)
    return {
        "student": student or {},
        "marks": marks_df,
        "attendance": attendance_df,
        "homework": homework_df,
        "notices": notices_df,
    }


def get_student_db_context(student_id: int) -> str:
    overview = get_student_overview(student_id)
    student = overview["student"]
    if not student:
        return "No student record found in the academic database."

    homework_df = overview["homework"].head(5)
    marks_df = overview["marks"].sort_values("exam_date", ascending=False).head(6)
    attendance_df = overview["attendance"].sort_values("date", ascending=False).head(10)
    notices_df = overview["notices"].head(5)

    sections = [
        f"Student Name: {student['student_name']}",
        f"Class: {student['student_class']}",
        f"Roll Number: {student['roll_number']}",
    ]

    if not homework_df.empty:
        homework_lines = [
            f"- {row.subject}: {row.title} (Due: {row.due_date})"
            for row in homework_df.itertuples()
        ]
        sections.append("Recent Homework:\n" + "\n".join(homework_lines))

    if not marks_df.empty:
        marks_lines = [
            f"- {row.subject} {row.exam_name}: {row.marks_scored}/{row.total_marks} on {row.exam_date}"
            for row in marks_df.itertuples()
        ]
        sections.append("Recent Marks:\n" + "\n".join(marks_lines))

    if not attendance_df.empty:
        attendance_lines = [
            f"- {row.date}: {row.status} ({row.attendance_percentage}%)"
            for row in attendance_df.itertuples()
        ]
        sections.append("Recent Attendance:\n" + "\n".join(attendance_lines))

    if not notices_df.empty:
        notice_lines = [
            f"- {row.title}: {row.description}"
            for row in notices_df.itertuples()
        ]
        sections.append("Recent Notices:\n" + "\n".join(notice_lines))

    return "\n\n".join(sections)
