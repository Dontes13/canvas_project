import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def parse_syllabus(text):
    prompt = f"""You are parsing a college course syllabus. Extract every graded item (assignments, quizzes, exams, midterms, finals, projects) into a JSON array.

Each item must have exactly these fields:
- "title": string, the name of the item (e.g. "Midterm Exam")
- "due_date": string in ISO format YYYY-MM-DD. If only a partial date is given, infer the most reasonable year (assume 2026 if no year is stated).
- "grade_weight": number (not a string), the percentage of the final grade this item is worth. Do not include a % sign.
- "assignment_type": one of exactly these four strings: "homework", "quiz", "exam", "project". Midterms and finals both count as "exam".

Return ONLY a raw JSON array. No markdown code fences, no explanation, no extra text before or after.

Syllabus text:
{text}
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


if __name__ == "__main__":
    sample = "Midterm Exam on October 14th, worth 25% of grade."
    result = parse_syllabus(sample)
    print(result)