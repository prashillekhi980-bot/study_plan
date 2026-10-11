"""Recommendations blueprint — dashboard + "what to study next" engine.

The dashboard shows real progress data plus the top-ranked recommendation
from the rule-based scoring engine (Phase 4 of the proposal: urgency,
difficulty, unfinished progress, priority, struggling flag).
"""
from datetime import date
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Task, Module, StudySession
from app.recommendations.engine import rank_tasks

recommendations_bp = Blueprint("recommendations", __name__)


@recommendations_bp.route("/dashboard")
@login_required
def dashboard():
    module_ids = [m.id for m in Module.query.filter_by(user_id=current_user.id).all()]

    all_tasks = Task.query.filter(Task.module_id.in_(module_ids)).all() if module_ids else []
    completed_tasks = [t for t in all_tasks if t.status == "completed"]

    total_estimated = sum(t.estimated_hours for t in all_tasks)
    total_completed_hours = sum(t.hours_completed for t in all_tasks)
    overall_progress = round((total_completed_hours / total_estimated) * 100) if total_estimated else 0

    upcoming = sorted(
        [t for t in all_tasks if t.status != "completed"],
        key=lambda t: t.due_date,
    )[:5]

    struggling_tasks = [t for t in all_tasks if t.is_struggling and t.status != "completed"]

    overdue_count = sum(
        1 for t in all_tasks if t.status != "completed" and t.due_date < date.today()
    )

    stats = {
        "module_count": len(module_ids),
        "task_count": len(all_tasks),
        "completed_count": len(completed_tasks),
        "overall_progress": overall_progress,
        "overdue_count": overdue_count,
    }

    incomplete = [t for t in all_tasks if t.status != "completed"]
    ranked = rank_tasks(incomplete)
    top_recommendations = ranked[:3]

    today = date.today()
    todays_sessions = (
        StudySession.query.filter_by(user_id=current_user.id, scheduled_date=today)
        .order_by(StudySession.is_completed)
        .all()
    )
    todays_hours_studied = round(
        sum(s.allocated_hours for s in todays_sessions if s.is_completed), 2
    )

    return render_template(
        "dashboard.html",
        user=current_user,
        stats=stats,
        upcoming=upcoming,
        struggling_tasks=struggling_tasks,
        top_recommendations=top_recommendations,
        todays_sessions=todays_sessions,
        todays_hours_studied=todays_hours_studied,
        today=today,
    )
