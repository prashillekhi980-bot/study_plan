"""Tasks blueprint — add/edit/delete tasks, mark complete.

Every route is scoped through the parent module's owner, so a user can
only touch tasks that live inside one of their own modules (enforced via
the shared ownership checks in app.ownership).
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Task, Module, StudySession
from app.ownership import get_owned_module_or_404, get_owned_task_or_404, get_owned_study_session_or_404

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")

TASK_FILTERS = ("all", "today", "upcoming", "completed", "overdue")


def _apply_filter(tasks, filter_name, today):
    """Step 6: All / Today / Upcoming / Completed / Overdue task views."""
    if filter_name == "today":
        return [t for t in tasks if t.due_date == today and t.status != "completed"]
    if filter_name == "upcoming":
        return [t for t in tasks if t.due_date > today and t.status != "completed"]
    if filter_name == "completed":
        return [t for t in tasks if t.status == "completed"]
    if filter_name == "overdue":
        return [t for t in tasks if t.due_date < today and t.status != "completed"]
    return tasks


def _parse_task_form(form):
    """Shared parsing/validation for the create and edit forms. Returns
    (data_dict, error_message) — error_message is None if valid."""
    title = form.get("title", "").strip()
    due_date_raw = form.get("due_date", "").strip()
    priority = form.get("priority", "medium")
    difficulty = form.get("difficulty", "3")
    estimated_hours = form.get("estimated_hours", "").strip()
    is_struggling = form.get("is_struggling") == "on"
    description = form.get("description", "").strip()

    if not title:
        return None, "Task title is required."
    if priority not in Task.PRIORITY_LEVELS:
        return None, "Invalid priority level."

    try:
        due_date = datetime.strptime(due_date_raw, "%Y-%m-%d").date()
    except ValueError:
        return None, "A valid due date is required."

    try:
        difficulty = int(difficulty)
        if not (1 <= difficulty <= 5):
            raise ValueError
    except ValueError:
        return None, "Difficulty must be a number between 1 and 5."

    try:
        estimated_hours = float(estimated_hours)
        if estimated_hours <= 0:
            raise ValueError
    except ValueError:
        return None, "Estimated hours must be a positive number."

    return {
        "title": title,
        "description": description,
        "due_date": due_date,
        "priority": priority,
        "difficulty": difficulty,
        "estimated_hours": estimated_hours,
        "is_struggling": is_struggling,
    }, None


@tasks_bp.route("/module/<int:module_id>")
@login_required
def list_tasks(module_id):
    module = get_owned_module_or_404(module_id)
    tasks = Task.query.filter_by(module_id=module.id).order_by(Task.due_date).all()
    return render_template("tasks/list.html", module=module, tasks=tasks, today=date.today())


@tasks_bp.route("/")
@login_required
def list_all():
    """Step 6: 'My Tasks' — every task across every module, with the
    All/Today/Upcoming/Completed/Overdue filters and a title search."""
    today = date.today()
    filter_name = request.args.get("filter", "all")
    if filter_name not in TASK_FILTERS:
        filter_name = "all"
    query = request.args.get("q", "").strip()

    module_ids = [m.id for m in Module.query.filter_by(user_id=current_user.id).all()]
    tasks = Task.query.filter(Task.module_id.in_(module_ids)).all() if module_ids else []

    if query:
        tasks = [t for t in tasks if query.lower() in t.title.lower()]

    tasks = _apply_filter(tasks, filter_name, today)
    tasks.sort(key=lambda t: t.due_date)

    counts = {}
    all_tasks = Task.query.filter(Task.module_id.in_(module_ids)).all() if module_ids else []
    for name in TASK_FILTERS:
        counts[name] = len(_apply_filter(all_tasks, name, today))

    return render_template(
        "tasks/list_all.html",
        tasks=tasks,
        today=today,
        active_filter=filter_name,
        query=query,
        counts=counts,
    )


@tasks_bp.route("/<int:task_id>")
@login_required
def task_detail(task_id):
    """Step 6: task detail page — full info on one task in one place."""
    task = get_owned_task_or_404(task_id)
    sessions = (
        StudySession.query.filter_by(task_id=task.id)
        .order_by(StudySession.scheduled_date.desc())
        .all()
    )
    return render_template("tasks/detail.html", task=task, sessions=sessions, today=date.today())


@tasks_bp.route("/module/<int:module_id>/new", methods=["GET", "POST"])
@login_required
def new_task(module_id):
    module = get_owned_module_or_404(module_id)

    if request.method == "POST":
        data, error = _parse_task_form(request.form)
        if error:
            flash(error, "error")
            return redirect(url_for("tasks.new_task", module_id=module_id))

        task = Task(module_id=module.id, **data)
        db.session.add(task)
        db.session.commit()
        flash(f'Task "{task.title}" added.', "success")
        return redirect(url_for("tasks.list_tasks", module_id=module_id))

    return render_template("tasks/form.html", module=module, task=None)


@tasks_bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = get_owned_task_or_404(task_id)

    if request.method == "POST":
        data, error = _parse_task_form(request.form)
        if error:
            flash(error, "error")
            return redirect(url_for("tasks.edit_task", task_id=task_id))

        for key, value in data.items():
            setattr(task, key, value)
        db.session.commit()
        flash(f'Task "{task.title}" updated.', "success")
        return redirect(url_for("tasks.list_tasks", module_id=task.module_id))

    return render_template("tasks/form.html", module=task.module, task=task)


@tasks_bp.route("/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    task = get_owned_task_or_404(task_id)
    module_id = task.module_id
    title = task.title
    db.session.delete(task)
    db.session.commit()
    flash(f'Task "{title}" deleted.', "success")
    return redirect(url_for("tasks.list_tasks", module_id=module_id))


MIN_SESSION_HOURS = 1 / 60  # a session shorter than a minute still counts as a minute


def _record_actual_session(task, hours):
    """Step 10: record actual study time and associate it with the task,
    as a real StudySession row (is_completed=True marks it as time that
    was actually studied, vs. the timetable generator's planned blocks)."""
    if hours <= 0:
        return
    db.session.add(
        StudySession(
            task_id=task.id,
            user_id=current_user.id,
            scheduled_date=date.today(),
            allocated_hours=hours,
            is_completed=True,
        )
    )


def _get_active_session():
    """The current user's one live Start/Stop Session timer, if any —
    only one can run at a time (across all tasks) to keep the UI simple."""
    return (
        StudySession.query.filter_by(user_id=current_user.id, ended_at=None)
        .filter(StudySession.started_at.isnot(None))
        .first()
    )


def _stop_session(study_session, ended_at=None):
    """Stop a running session: compute elapsed hours automatically from
    started_at/ended_at, log it as real study time on the task, and
    recalculate the task's progress/status — the same recalculation
    logged/manual hours have always triggered, just from a timer instead
    of a typed-in number. Returns the elapsed hours actually logged."""
    ended_at = ended_at or datetime.utcnow()
    raw_elapsed_hours = max((ended_at - study_session.started_at).total_seconds() / 3600.0, MIN_SESSION_HOURS)
    # Round to the nearest minute (2dp in hours) — a timer's raw elapsed
    # time has far more precision than is useful to show or store, and an
    # unrounded value made hours_completed print as e.g. "0.0166667h".
    elapsed_hours = round(raw_elapsed_hours, 2)

    task = study_session.task
    actual_logged = min(elapsed_hours, task.remaining_hours)

    study_session.ended_at = ended_at
    study_session.allocated_hours = round(actual_logged, 2)
    study_session.is_completed = True

    task.hours_completed = min(task.hours_completed + elapsed_hours, task.estimated_hours)
    if task.hours_completed >= task.estimated_hours:
        task.status = "completed"
    elif task.hours_completed > 0:
        task.status = "in_progress"

    return round(actual_logged, 2)


@tasks_bp.route("/<int:task_id>/start-session", methods=["POST"])
@login_required
def start_session(task_id):
    """Step 10: start a live study session on a task — replaces typing in
    hours after the fact. Only one session can run at a time."""
    task = get_owned_task_or_404(task_id)

    if task.status == "completed":
        flash(f'"{task.title}" is already complete.', "error")
        return redirect(url_for("tasks.task_detail", task_id=task_id))

    active = _get_active_session()
    if active:
        flash(f'You already have a session running on "{active.task.title}" — stop it first.', "error")
        return redirect(url_for("tasks.task_detail", task_id=task_id))

    db.session.add(
        StudySession(
            task_id=task.id,
            user_id=current_user.id,
            scheduled_date=date.today(),
            allocated_hours=0,
            is_completed=False,
            started_at=datetime.utcnow(),
        )
    )
    db.session.commit()
    flash(f'Session started on "{task.title}".', "success")
    return redirect(url_for("tasks.task_detail", task_id=task_id))


@tasks_bp.route("/session/<int:session_id>/stop", methods=["POST"])
@login_required
def stop_session(session_id):
    """Step 10: stop a running session — automatically logs the elapsed
    time and recalculates the task's progress/status. Recommendation
    scores, the dashboard and Progress page all recompute live from the
    database on their next load, so no separate 'recalculate' step is
    needed beyond this."""
    study_session = get_owned_study_session_or_404(session_id)

    if not study_session.is_active:
        flash("That session isn't running.", "error")
        return redirect(url_for("recommendations.dashboard"))

    task = study_session.task
    hours = _stop_session(study_session)
    db.session.commit()
    flash(f'Session stopped — logged {hours}h on "{task.title}".', "success")
    return redirect(url_for("tasks.task_detail", task_id=task.id))


@tasks_bp.route("/<int:task_id>/complete", methods=["POST"])
@login_required
def mark_complete(task_id):
    """Progress tracking: mark a task fully complete in one click. Stops
    a running session on this task first (logging its elapsed time)
    before topping up whatever's left to reach 100%."""
    task = get_owned_task_or_404(task_id)

    active = _get_active_session()
    if active and active.task_id == task.id:
        _stop_session(active)

    remaining = task.remaining_hours
    task.status = "completed"
    task.hours_completed = task.estimated_hours
    _record_actual_session(task, remaining)
    db.session.commit()
    flash(f'"{task.title}" marked complete.', "success")
    return redirect(url_for("tasks.list_tasks", module_id=task.module_id))


@tasks_bp.route("/<int:task_id>/log-hours", methods=["POST"])
@login_required
def log_hours(task_id):
    """Progress tracking: log partial study hours toward a task without
    marking it fully complete."""
    task = get_owned_task_or_404(task_id)
    try:
        hours = float(request.form.get("hours", 0))
    except ValueError:
        hours = 0

    if hours > 0:
        actual_logged = min(hours, task.remaining_hours)
        task.hours_completed = min(task.hours_completed + hours, task.estimated_hours)
        if task.hours_completed >= task.estimated_hours:
            task.status = "completed"
        elif task.hours_completed > 0:
            task.status = "in_progress"
        _record_actual_session(task, actual_logged)
        db.session.commit()
        flash(f"Logged {hours}h on \"{task.title}\".", "success")

    return redirect(url_for("tasks.list_tasks", module_id=task.module_id))
