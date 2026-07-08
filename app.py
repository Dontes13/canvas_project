from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import DataRequired
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

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    grade_weight = db.Column(db.Float, nullable=False)
    assignment_type = db.Column(db.String(20))  # homework / quiz / exam / project
    status = db.Column(db.String(20), default="not_started")
    raw_text = db.Column(db.Text)
    course = db.relationship("Course", backref="assignments")

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    target_grade = db.Column(db.Float)
    current_estimated_grade = db.Column(db.Float)
    notes = db.Column(db.Text)
    course = db.relationship("Course", backref="goal")

class SyllabusForm(FlaskForm):
    syllabus_text = TextAreaField("Paste syllabus text", validators=[DataRequired()])


@app.route("/input", methods=["GET", "POST"])
def input_page():
    form = SyllabusForm()
    return render_template("input.html", form=form)

@app.route("/")
def index():
    return "Survival Guide is alive."

@app.route("/export-calendar")
def export_calendar():
    assignments = Assignment.query.all()
    if not assignments:
        return "No assignments in the database yet, nothing to export."
    service = get_calendar_service()
    count = 0
    for assignment in assignments:
        add_assignment_to_calendar(
            service,
            title=assignment.title,
            due_date=assignment.due_date,
            course_name=assignment.course.name if assignment.course else None,
            assignment_type=assignment.assignment_type,
        )
        count += 1
    return f"Added {count} assignments to your Google Calendar."

if __name__ == "__main__":
    app.run(debug=True)
