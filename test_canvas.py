import os
import json
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()

sample_syllabus = """
STATS 250 - Introduction to Statistics
Grading: Exams 50%, Homework 30%, Final Project 20%

Assignments:
- Homework 3, due July 8, worth 20 points
- Midterm 2, due July 14, worth 100 points
- Project proposal, due July 20, worth 25 points
"""

prompt = f"""Extract the grading structure and assignments from this syllabus.
Respond with ONLY valid JSON, no markdown fences, no commentary, in this shape:

{{
  "course_name": "string",
  "grading_weights": {{"Category": percent_number}},
  "assignments": [
    {{"name": "string", "due_date": "YYYY-MM-DD", "points": number, "category": "string"}}
  ]
}}

SYLLABUS:
{sample_syllabus}
"""

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    messages=[{"role": "user", "content": prompt}]
)

raw = message.content[0].text
print("Raw response:\n", raw)

parsed = json.loads(raw)
print("\nParsed successfully:")
print(json.dumps(parsed, indent=2))