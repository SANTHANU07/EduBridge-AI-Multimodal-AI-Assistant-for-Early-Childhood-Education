from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from calendar_integration import create_calendar_event, get_calendar_configuration
from db import add_school_event, delete_school_event, get_school_events, list_students


def render_teacher_events_section(user: dict):
    st.subheader("School Events")
    st.caption("Create school announcements and sync them with Google Calendar.")

    calendar_config = get_calendar_configuration()
    with st.expander("Google Calendar Setup", expanded=not calendar_config["is_ready"]):
        st.write(f"Service account file: `{calendar_config['service_account_path']}`")
        st.write(f"Service account email: `{calendar_config['service_account_email'] or 'Not found'}`")
        st.write(f"Calendar ID: `{calendar_config['calendar_id']}`")
        st.write(f"Timezone: `{calendar_config['timezone']}`")
        if calendar_config["is_ready"]:
            st.success("Google Calendar configuration is ready.")
        else:
            st.warning(calendar_config["message"])

    class_options = ["All Parents"] + sorted(list_students()["student_class"].unique().tolist()) + ["Grade 1-2"]

    with st.form("school_event_form"):
        title = st.text_input("Event title", placeholder="Parent Teacher Meeting")
        description = st.text_area("Event description", placeholder="Discussion about student progress")
        event_date = st.date_input("Date")
        col1, col2, col3 = st.columns(3)
        start_time = col1.time_input("Start time")
        end_time = col2.time_input("End time")
        audience = col3.selectbox("Class or audience", class_options)
        submitted = st.form_submit_button("Create Event", use_container_width=True)

        if submitted:
            start_dt = datetime.combine(event_date, start_time)
            end_dt = datetime.combine(event_date, end_time)
            if end_dt <= start_dt:
                st.error("End time must be after start time.")
            else:
                google_event_id = None
                calendar_link = None
                try:
                    event_result = create_calendar_event(title, description, start_dt, end_dt, audience)
                    google_event_id = event_result["id"]
                    calendar_link = event_result["htmlLink"]
                    st.success(
                        f"Google Calendar event created successfully in calendar: {event_result['calendar_id']}"
                    )
                    if calendar_link:
                        st.markdown(f"[Open Calendar Event]({calendar_link})")
                except Exception as exc:
                    st.warning(f"Calendar sync failed, but the event will still be saved locally: {exc}")

                add_school_event(
                    title=title,
                    description=description,
                    event_date=str(event_date),
                    start_time=start_time.strftime("%H:%M"),
                    end_time=end_time.strftime("%H:%M"),
                    audience="" if audience == "All Parents" else audience,
                    teacher_name=user["full_name"],
                    google_event_id=google_event_id,
                    calendar_link=calendar_link,
                )
                st.success("School event saved to the local database.")
                st.rerun()

    st.markdown("### View Events")
    events_df = get_school_events()
    if events_df.empty:
        st.info("No school events created yet.")
        return

    display_df = events_df.copy()
    if "calendar_link" in display_df.columns:
        display_df["calendar_link"] = display_df["calendar_link"].fillna("")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    selected_event_id = st.selectbox("Delete Event", events_df["id"].tolist(), key="delete_school_event_id")
    if st.button("Delete Selected Event", use_container_width=True):
        delete_school_event(selected_event_id)
        st.success("School event deleted.")
        st.rerun()


def render_parent_events_section(events_df: pd.DataFrame):
    st.subheader("Upcoming School Events")
    if events_df.empty:
        st.info("No upcoming school events right now.")
        return

    display_df = events_df[["title", "event_date", "start_time", "end_time", "description", "audience"]].copy()
    display_df.columns = ["Title", "Date", "Start", "End", "Description", "Audience"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
