import os
from dotenv import load_dotenv
from google import genai
import json

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def parse_syllabus(text):
    prompt = f"""You are parsing a college course syllabus. Extract the course name and every graded item (assignments, quizzes, exams, midterms, finals, projects).

Return a single JSON object with exactly these two fields:
- "course_name": string, the name of the course as stated in the syllabus (e.g. "Introduction to Computer Science"). If no course name is stated, use "Unknown Course".
- "assignments": a JSON array where each item has exactly these fields:
  - "title": string, the name of the item (e.g. "Midterm Exam")
  - "due_date": string in ISO format YYYY-MM-DD. If only a partial date is given, infer the most reasonable year (assume 2026 if no year is stated).
  - "grade_weight": number (not a string), the percentage of the final grade this item is worth. Do not include a % sign.
  - "assignment_type": one of exactly these four strings: "homework", "quiz", "exam", "project". Midterms and finals both count as "exam".

Before returning your answer, verify that the JSON is syntactically valid — check that every array and object is properly closed and every item is separated by a comma.
Return ONLY the raw JSON object. No markdown code fences, no explanation, no extra text before or after.

Syllabus text:
{text}
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


def clean_and_parse(raw_text):
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()
    print("CLEANED JSON:", cleaned)
    return json.loads(cleaned)

if __name__ == "__main__":
    sample = "Midterm Exam on October 14th, worth 25% of grade."
    result = parse_syllabus(sample)
    print(result)