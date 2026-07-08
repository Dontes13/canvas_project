import os
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def build_course_context(courses):
    lines = []
    for course in courses:
        lines.append(f"Course: {course.name}")
        if course.professor:
            lines.append(f"Professor: {course.professor}")
        lines.append("Graded work:")
        for a in course.assignments:
            due = a.due_date.isoformat() if a.due_date else "no due date listed"
            lines.append(f"- {a.title} ({a.assignment_type}), due {due}, worth {a.grade_weight}% of the grade")
        if course.syllabus_text:
            lines.append("Full syllabus text:")
            lines.append(course.syllabus_text)
        lines.append("")
    return "\n".join(lines)


def ask_tutor(question, context):
    prompt = f"""You are a friendly, encouraging tutor helping a college student survive their classes.
Answer the student's question using ONLY the course information below.
If the answer is not in the course information, say you don't see it in the syllabus and suggest the student ask the professor or check the course page.
Keep answers short, specific, and practical.

Course information:
{context}

Student's question: {question}"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


if __name__ == "__main__":
    from app import app, Course

    question = " ".join(sys.argv[1:]) or "What should I focus on most in this class?"
    with app.app_context():
        courses = Course.query.all()
        if not courses:
            print("No courses in the database yet. Upload a syllabus at /upload first.")
        else:
            print("Q:", question)
            print()
            print("A:", ask_tutor(question, build_course_context(courses)))
