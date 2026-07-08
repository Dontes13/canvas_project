import os
from datetime import date, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]



def get_calendar_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

def add_assignment_to_calendar(service, title, due_date, course_name=None, assignment_type=None):
    due_str = due_date.isoformat() if isinstance(due_date, date) else due_date
    summary = f"[{course_name}] {title}" if course_name else title
    end_str = (date.fromisoformat(due_str) + timedelta(days=1)).isoformat()

    event = {
        "summary": summary,
        "description": f"Type: {assignment_type}" if assignment_type else "",
        "start": {"date": due_str},
        "end": {"date": end_str},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 7 * 24 * 60},  # 1 week before
                {"method": "popup", "minutes": 24 * 60},      # 1 day before
            ],
        },
    }
    created = service.events().insert(calendarId="primary", body=event).execute()
    return created

if __name__ == "__main__":
    service = get_calendar_service()
    print("Connected to Google Calendar!")
