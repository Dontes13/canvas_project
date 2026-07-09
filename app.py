from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, session
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import TextAreaField, FloatField
from wtforms.validators import DataRequired, Optional
from flask_wtf.file import FileField, FileAllowed
from gemini_parser import parse_syllabus, clean_and_parse, parse_file
from datetime import datetime
from scoring import priority_score
import json
from calendar_service import get_calendar_service, add_assignment_to_calendar

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "change later"

db = SQLAlchemy(app)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    professor = db.Column(db.String(100))
    priority_boost = db.Column(db.Float, default=1.0)
    color = db.Column(db.String(20))
    syllabus_text = db.Column(db.Text)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date)
    grade_weight = db.Column(db.Float, nullable=False)
    assignment_type = db.Column(db.String(20))  # homework / quiz / exam / project
    status = db.Column(db.String(20), default="not_started")
    raw_text = db.Column(db.Text)
    gcal_event_id = db.Column(db.String(100))
    course = db.relationship("Course", backref="assignments")

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    target_grade = db.Column(db.Float)
    curr_est_grade = db.Column(db.Float)
    course = db.relationship("Course", backref="goal")

class SyllabusForm(FlaskForm):
    syllabus_text = TextAreaField("Paste syllabus text", validators=[Optional()])
    syllabus_file = FileField("Or upload your syllabus", validators=[FileAllowed(["pdf", "png", "jpg", "jpeg"], "PDF or image files only")])
    target_grade = FloatField("Target grade (optional)", validators=[Optional()])
    curr_est_grade = FloatField("Current estimated grade (optional)", validators=[Optional()])


# Helper functions for routing functions

def get_remaining_assginments(course):
    remaining = []

    for asgn in course.assignments:
        if asgn.status != "completed":
            remaining.append(asgn)
    
    return len(remaining)

def sort_helper(element):
    if element["priority_score"] is None:
        return -1
    else:
        return element["priority_score"]

def get_dashboard_data():
    courses = Course.query.all()
    results = []

    for c in courses:
        goal = c.goal[0] if c.goal else None
        target_grade = goal.target_grade if goal else None
        curr_est_grade = goal.curr_est_grade if goal else None

        for asgn in c.assignments:
            if asgn.status == "completed":
                continue

            if asgn.due_date is None:
                score = None
            else:
                days_rem = (asgn.due_date - datetime.now().date()).days
                score = priority_score(
                    grade_weight=asgn.grade_weight,
                    days_rem=days_rem,
                    course_pri_boost=c.priority_boost,
                    target_grade=target_grade,
                    curr_est_grade=curr_est_grade
                )
                score = round(score, 2)
            results.append({
                "id": asgn.id,
                "name": c.name,
                "assignment": asgn.title,
                "weight": asgn.grade_weight,
                "priority_score": score,
                "status": asgn.status
            })
    
    results.sort(key=sort_helper, reverse=True)
    return results


# Routing functions...

@app.route("/upload", methods=["GET", "POST"])
def input_page():
    # Set up the upload page for users to paste their syllabus
    form = SyllabusForm()
    res = None
    if form.validate_on_submit():
        syllabus_text = form.syllabus_text.data
        uploaded = form.syllabus_file.data
        if uploaded:
            ext = uploaded.filename.rsplit(".", 1)[-1].lower()
            mime = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}[ext]
            parsed = clean_and_parse(parse_file(uploaded.read(), mime))
            syllabus_text = parsed.pop("full_text", "")
        elif syllabus_text and syllabus_text.strip():
            parsed = clean_and_parse(parse_syllabus(syllabus_text))
        else:
            flash("Paste your syllabus text or upload a file first.")
            return render_template("upload.html", form=form, result=None)

        course_name = parsed.get("course_name", "Unkown Course")
        course = Course.query.filter_by(name=course_name).first()
        if course is None:
            course = Course(name=course_name)
            db.session.add(course)
        course.syllabus_text = syllabus_text
        
        for asgn in parsed["assignments"]:
            due_date_str = asgn.get("due_date")
            due_date = None
            if due_date_str:
                parsed_date = datetime.strptime(asgn["due_date"], "%Y-%m-%d")
                due_date = parsed_date.date()
            assignment = Assignment(
                course=course,
                title=asgn["title"],
                due_date=due_date,
                grade_weight=asgn["grade_weight"],
                assignment_type=asgn.get("assignment_type"),
                raw_text=asgn.get("raw_text")
            )
            db.session.add(assignment)
        
        target_grade = form.target_grade.data
        curr_est_grade = form.curr_est_grade.data
        if target_grade is not None or curr_est_grade is not None:
            goal = Goal(
                course=course,
                target_grade=target_grade,
                curr_est_grade=curr_est_grade
            )
            db.session.add(goal)
        
        db.session.commit()
        res = parsed

    return render_template("upload.html", form=form, result=res)

@app.route("/")
def index():
    # To-do: Connect this route with the "homepage.html"
    courses = Course.query.all()
    for c in courses:
        c.remaining_count = get_remaining_assginments(c)
    return render_template("homepage.html", courses=courses)

@app.route("/dashboard")
def dashboard():
    dashboard_data = get_dashboard_data()
    return render_template("dashboard.html", courses=dashboard_data)

chat_sessions = {}

@app.route("/api/chat", methods=["POST"])
def api_chat():
    from study_chat import start_chat
    from tutor import build_course_context
    if "chat_id" not in session:
        session["chat_id"] = str(uuid.uuid4())
    chat_id = session["chat_id"]
    if chat_id not in chat_sessions:
        courses = Course.query.all()
        context = build_course_context(courses) if courses else "No courses uploaded yet."
        chat_sessions[chat_id] = start_chat(context)
    message = (request.json.get("message") or "").strip()
    if not message:
        return jsonify({"reply": "Type a message first."})
    try:
        response = chat_sessions[chat_id].send_message(message)
        return jsonify({"reply": response.text})
    except Exception:
        chat_sessions.pop(chat_id, None)
        return jsonify({"reply": "Something went wrong on my end. Try asking again."})

@app.route("/complete/<int:assignment_id>", methods=["POST"])
def complete_assignment(assignment_id):
    assignment = Assignment.query.get(assignment_id)
    assignment.status = "completed"
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/export-calendar")
def export_calendar():
    assignments = Assignment.query.all()
    if not assignments:
        flash("No assignments in the database yet, nothing to export.")
        return redirect(url_for("dashboard"))
    service = get_calendar_service()
    count = 0
    skipped = 0
    already_there = 0
    for assignment in assignments:
        if assignment.due_date is None:
            skipped += 1
            continue
        if assignment.gcal_event_id:
            already_there += 1
            continue
        created = add_assignment_to_calendar(
            service,
            title=assignment.title,
            due_date=assignment.due_date,
            course_name=assignment.course.name if assignment.course else None,
            assignment_type=assignment.assignment_type,
        )
        assignment.gcal_event_id = created["id"]
        count += 1
    db.session.commit()
    message = f"Added {count} assignments to your Google Calendar."
    if already_there:
        message += f" {already_there} were already on the calendar."
    if skipped:
        message += f" Skipped {skipped} with no due date."
    flash(message)
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
