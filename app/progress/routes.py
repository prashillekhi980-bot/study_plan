"""Progress blueprint — dedicated study analytics page (proposal Step 13):
overall completion, progress by module, task completion, study hours by
day/week, completed vs remaining work. Informational only — it doesn't
grade or assess the student.
"""
from datetime import date, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Module, Task, StudySession

progress_bp = Blueprint("progress", __name__, url_prefix="/progress")

WEEK_DAYS = 7


@progress_bp.route("/")
@login_required
def view_progress():
    modules = Module.query.filter_by(user_id=current_user.id).order_by(Module.created_at).all()
    module_ids = [m.id for m in modules]
    all_tasks = Task.query.filter(Task.module_id.in_(module_ids)).all() if module_ids else []

    total_estimated = sum(t.estimated_hours for t in all_tasks)
    total_completed_hours = sum(t.hours_completed for t in all_tasks)
    overall_progress = round((total_completed_hours / total_estimated) * 100) if total_estimated else 0

    completed_count = sum(1 for t in all_tasks if t.status == "completed")

    # Study hours actually logged (StudySession rows created when the
    # student logs hours or completes a task — see tasks/routes.py),
    # for the last 7 days, oldest first.
    today = date.today()
    window_start = today - timedelta(days=WEEK_DAYS - 1)
    logged_sessions = (
        StudySession.query.filter(
            StudySession.user_id == current_user.id,
            StudySession.is_completed.is_(True),
            StudySession.scheduled_date >= window_start,
            StudySession.scheduled_date <= today,
        ).all()
    )
    hours_by_date = {}
    for s in logged_sessions:
        hours_by_date[s.scheduled_date] = hours_by_date.get(s.scheduled_date, 0) + s.allocated_hours

    daily_hours = []
    current = window_start
    while current <= today:
        daily_hours.append({"date": current, "hours": round(hours_by_date.get(current, 0), 2)})
        current += timedelta(days=1)

    week_total_hours = round(sum(d["hours"] for d in daily_hours), 2)

    return render_template(
        "progress/view.html",
        modules=modules,
        overall_progress=overall_progress,
        total_estimated=total_estimated,
        total_completed_hours=round(total_completed_hours, 2),
        total_remaining_hours=round(max(total_estimated - total_completed_hours, 0), 2),
        task_count=len(all_tasks),
        completed_count=completed_count,
        daily_hours=daily_hours,
        week_total_hours=week_total_hours,
    )
