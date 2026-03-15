from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _resolve_service_account_path() -> Path:
    configured_path = os.getenv("GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE")
    if configured_path:
        return Path(configured_path)

    default_paths = [
        Path("calendar_key.json"),
        Path(r"C:\Users\U.S.Santhanu\Downloads\analog-pilot-488015-g4-281a5cc6e06d.json"),
    ]

    for path in default_paths:
        if path.exists():
            return path

    return default_paths[0]


def get_calendar_configuration() -> dict:
    service_account_path = _resolve_service_account_path()
    config = {
        "service_account_path": str(service_account_path),
        "service_account_email": "",
        "calendar_id": os.getenv("GOOGLE_CALENDAR_ID", "primary").strip() or "primary",
        "timezone": os.getenv("GOOGLE_CALENDAR_TIMEZONE", "Asia/Kolkata"),
        "is_ready": False,
        "message": "",
    }

    if not service_account_path.exists():
        config["message"] = (
            f"Service account key file not found at {service_account_path}. "
            "Add the JSON key file or set GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE."
        )
        return config

    try:
        with open(service_account_path, "r", encoding="utf-8") as key_file:
            key_data = json.load(key_file)
        config["service_account_email"] = key_data.get("client_email", "")
    except Exception:
        config["message"] = "Unable to read the Google service account key file."
        return config

    config["is_ready"] = True
    config["message"] = "Google Calendar is configured."
    return config


def create_calendar_event(
    title: str,
    description: str,
    start_datetime: datetime,
    end_datetime: datetime,
    audience: str = "",
):
    configuration = get_calendar_configuration()
    if not configuration["is_ready"]:
        raise RuntimeError(configuration["message"])

    service_account_path = Path(configuration["service_account_path"])

    credentials = service_account.Credentials.from_service_account_file(
        str(service_account_path),
        scopes=SCOPES,
    )

    service = build("calendar", "v3", credentials=credentials)
    calendar_id = configuration["calendar_id"]

    event_body = {
        "summary": title,
        "description": description if not audience else f"{description}\n\nAudience: {audience}",
        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": configuration["timezone"],
        },
        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": configuration["timezone"],
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 24 * 60},
                {"method": "popup", "minutes": 60},
            ],
        },
    }

    created_event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
    return {
        "id": created_event.get("id"),
        "htmlLink": created_event.get("htmlLink"),
        "status": created_event.get("status", "confirmed"),
        "calendar_id": calendar_id,
    }
