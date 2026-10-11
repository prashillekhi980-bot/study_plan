"""Study timetable generator (proposal Phase 4: "plan all the different
study blocks in the best possible way").

Daily round-robin allocation: for each day (starting today), the top
MAX_TASKS_PER_DAY still-unfinished tasks — ranked by the recommendation
engine's score *as of that day* (so urgency keeps climbing the closer a
day gets to a task's deadline) — split that day's study-hours capacity
between them in equal shares (a task needing less than its share hands
the rest back to the others that day). This mirrors how a student
actually studies: a handful of subjects each day, not one subject
monopolised for days in a row before the next one gets a look-in — which
is what a plain "fill task 1 fully, then task 2" greedy pass used to
produce whenever a single task's hours matched or exceeded the daily cap.

If a task still can't be fully scheduled before its deadline (not enough
total capacity), the generator keeps allocating into the days immediately
after the deadline instead of silently dropping hours, and reports which
tasks are "at risk" so the UI can warn the student rather than hide the
problem.
"""
from datetime import timedelta, date
from app.extensions import db
from app.models import StudySession
from app.recommendations.engine import rank_tasks

OVERFLOW_BUFFER_DAYS = 14  # how far past a deadline we'll still try to schedule
MAX_TASKS_PER_DAY = 3  # how many different subjects can share one day


def _split_day_capacity(day_cap, remaining_by_task_id, task_ids):
    """Split `day_cap` hours evenly across `task_ids`. A task that needs
    less than its equal share (because it's nearly done) only takes what
    it needs; the leftover is redistributed across the other tasks still
    wanting more, repeating until the day's capacity is used up or every
    selected task is fully satisfied for the day."""
    alloc = {tid: 0.0 for tid in task_ids}
    cap = day_cap
    active = set(task_ids)

    while cap > 1e-9 and active:
        share = cap / len(active)
        progressed = False
        for tid in list(active):
            want = remaining_by_task_id[tid] - alloc[tid]
            take = min(share, want)
            if take > 1e-9:
                alloc[tid] += take
                cap -= take
                progressed = True
            if remaining_by_task_id[tid] - alloc[tid] <= 1e-9:
                active.discard(tid)
        if not progressed:
            break

    return alloc


def generate_timetable(user, today=None):
    """Regenerate `user`'s timetable: clears previous study_sessions and
    creates a fresh set based on current tasks/scores. Returns a summary
    dict with the sessions created and any tasks that couldn't be fully
    scheduled before their deadline.
    """
    today = today or date.today()
    daily_cap = user.daily_study_hours if user.daily_study_hours > 0 else 1.0

    # Wipe the old *planned* sessions only — the schedule is fully
    # recomputed each time, rather than trying to diff/patch a stale one.
    # Two kinds of session must survive a regenerate: history the student
    # has actually studied (is_completed=True, added when they log hours,
    # complete a task, or stop a live timer — see tasks/routes.py), and a
    # Start/Stop Session timer that's *currently running*
    # (started_at set, ended_at still null) — regenerating the plan must
    # never delete a session the student is mid-way through recording.
    StudySession.query.filter_by(
        user_id=user.id, is_completed=False, started_at=None
    ).delete()

    incomplete_tasks = [
        t for m in user.modules for t in m.tasks
        if t.status != "completed" and t.remaining_hours > 0
    ]

    if not incomplete_tasks:
        db.session.commit()
        return {"sessions_created": 0, "at_risk_tasks": []}

    tasks_by_id = {t.id: t for t in incomplete_tasks}
    remaining = {t.id: t.remaining_hours for t in incomplete_tasks}
    scheduled_before_due = {t.id: 0.0 for t in incomplete_tasks}

    horizon_end = max(t.due_date for t in incomplete_tasks) + timedelta(days=OVERFLOW_BUFFER_DAYS)
    sessions_created = 0
    day = today

    while day <= horizon_end and any(hrs > 1e-9 for hrs in remaining.values()):
        pending_ids = [tid for tid, hrs in remaining.items() if hrs > 1e-9]

        # Re-rank against *this* day so urgency reflects how close each
        # task now is to its deadline, not just where it stood on day one.
        ranked_today = rank_tasks([tasks_by_id[tid] for tid in pending_ids], today=day)
        top_ids = [r["task"].id for r in ranked_today[:MAX_TASKS_PER_DAY]]

        alloc = _split_day_capacity(daily_cap, remaining, top_ids)
        for tid, hours in alloc.items():
            if hours > 1e-9:
                db.session.add(StudySession(
                    task_id=tid,
                    user_id=user.id,
                    scheduled_date=day,
                    allocated_hours=round(hours, 2),
                ))
                sessions_created += 1
                remaining[tid] -= hours
                if day <= tasks_by_id[tid].due_date:
                    scheduled_before_due[tid] += hours

        day += timedelta(days=1)

    at_risk_tasks = []
    for task in incomplete_tasks:
        if scheduled_before_due[task.id] < task.remaining_hours - 1e-9:
            at_risk_tasks.append({
                "task": task,
                "hours_short": round(task.remaining_hours - scheduled_before_due[task.id], 2),
            })

    db.session.commit()
    return {"sessions_created": sessions_created, "at_risk_tasks": at_risk_tasks}


def get_timetable_by_day(user):
    """Return the user's current *planned* timetable as a list of
    {date, sessions: [StudySession...]} ordered by date, for display.
    Actually-studied sessions and a currently-running Start/Stop Session
    timer are history/live activity, not part of the plan, so they're
    shown on the task detail/dashboard/progress pages instead of
    cluttering this view."""
    sessions = (
        StudySession.query.filter_by(user_id=user.id, is_completed=False, started_at=None)
        .order_by(StudySession.scheduled_date)
        .all()
    )

    grouped = {}
    for s in sessions:
        grouped.setdefault(s.scheduled_date, []).append(s)

    return [{"date": d, "sessions": grouped[d]} for d in sorted(grouped.keys())]
