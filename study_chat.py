import os
from datetime import date
from dotenv import load_dotenv
from google import genai
from google.genai import types
from calendar_service import get_calendar_service

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
service = get_calendar_service()


def list_events(day: str):
    """List all events on the student's Google Calendar for one day.

    Args:
        day: The date to check, in YYYY-MM-DD format.
    """
    resp = service.events().list(
        calendarId="primary",
        timeMin=f"{day}T00:00:00-07:00",
        timeMax=f"{day}T23:59:59-07:00",
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    events = []
    for e in resp.get("items", []):
        events.append({
            "title": e.get("summary", "(no title)"),
            "start": e["start"].get("dateTime", e["start"].get("date")),
            "end": e["end"].get("dateTime", e["end"].get("date")),
        })
    return events


def create_study_session(title: str, start: str, end: str):
    """Create a study session event on the student's Google Calendar.

    Args:
        title: Name of the session, e.g. "Study: Calc Midterm 1".
        start: Start time in ISO format, e.g. 2026-07-10T20:00:00.
        end: End time in ISO format, e.g. 2026-07-10T22:00:00.
    """
    event = {
        "summary": title,
        "start": {"dateTime": start, "timeZone": "America/Los_Angeles"},
        "end": {"dateTime": end, "timeZone": "America/Los_Angeles"},
    }
    created = service.events().insert(calendarId="primary", body=event).execute()
    return {"created": created.get("summary"), "link": created.get("htmlLink")}


def start_chat(course_context):
    system = f"""You are a friendly study-planning tutor helping a college student survive their classes.
Today's date is {date.today().isoformat()}.

Course information:
{course_context}

You can answer questions about the courses using ONLY the course information above.
If something is not in it, say you don't see it in the syllabus.

You can also plan study sessions on the student's Google Calendar. Rules:
- Ask about their preferences if you don't know them yet (morning or night person, how long they like to study).
- Before proposing times, use list_events to check their calendar for conflicts on those days.
- Propose a specific plan and wait for the student to confirm BEFORE creating any events.
- Only after they agree, use create_study_session to book each session.
- Plan sessions before due dates, heavier weighting for exams and projects.
- After booking, use list_events on the affected days to verify the sessions were created correctly, then summarize the updated schedule.
"""
    return client.chats.create(
        model="gemini-3-flash-preview",
        config=types.GenerateContentConfig(
            system_instruction=system,
            tools=[list_events, create_study_session],
        ),
    )


if __name__ == "__main__":
    from app import app, Course
    from tutor import build_course_context

    with app.app_context():
        courses = Course.query.all()
        context = build_course_context(courses) if courses else "No courses uploaded yet."

    chat = start_chat(context)
    print("Study tutor ready. Ask about your classes or say 'plan my study week'. Type 'quit' to exit.")
    while True:
        try:
            msg = input("\nYou: ").strip()
        except EOFError:
            break
        if msg.lower() in ("quit", "exit", "q"):
            break
        if not msg:
            continue
        response = chat.send_message(msg)
        print("\nTutor:", response.text)
