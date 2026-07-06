import math

def priority_score(grade_weight, days_rem, course_pri_boost=1.0, target_grade=None, curr_grade=None):
    if target_grade is not None and curr_grade is not None:
        grade_gap = target_grade - curr_grade
        grade_impact = grade_weight * grade_gap
    else:
        grade_impact = grade_weight
    
    days_rem = max(days_rem, 1)
    urgency = 1 / days_rem

    return grade_impact * urgency * course_pri_boost


if __name__ == "__main__":
    # Exam worth 25%, due in 3 days, no goal set, no course boost
    score1 = priority_score(grade_weight=25, days_rem=3)
    print("No goal:", score1)

    # Same exam, but student wants 90%, currently estimated at 70%
    score2 = priority_score(grade_weight=25, days_rem=3, target_grade=90, curr_grade=70)
    print("With goal gap:", score2)

    # Due today
    score3 = priority_score(grade_weight=25, days_rem=0)
    print("Due today (clamped):", score3)