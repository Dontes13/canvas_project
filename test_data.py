from datetime import date, timedelta
from app import app, db, Course, Assignment
from calendar_service import get_calendar_service, add_assignment_to_calendar
 # this creates the tables if they dont exist 
with app.app_context():
    db.create_all() 

    if Course.query.count() == 0:
        stats = Course(name="STATS 250", professor="Dr. Nguyen", priority_boost=1.0)
        db.session.add(stats)
        db.session.commit()

        db.session.add_all([
            Assignment(course_id=stats.id, title="Homework 3",
                       due_date=date.today() + timedelta(days=5),
                       grade_weight=5, assignment_type="homework"),
            Assignment(course_id=stats.id, title="Midterm Exam",
                       due_date=date.today() + timedelta(days=12),
                       grade_weight=25, assignment_type="exam"),
        ])
        db.session.commit()
        print("Fetched 1 course + 2 assignments.")
    else:
        print("Data already exists, skipping")

    for a in Assignment.query.all():
        print(a.id, a.title, a.due_date, a.course.name)





@app.route("/export-calendar")
def export_calendar():
    service = get_calendar_service()
    assignments = Assignment.query.all()
    count = 0
    for a in assignments:
        add_assignment_to_calendar(
            service,
            title=a.title,
            due_date=a.due_date,
            course_name=a.course.name,
            assignment_type=a.assignment_type,
        )
        count += 1
    return f"Exported {count} assignments to your Google Calendar!"