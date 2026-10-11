"""Timetable generator (app/timetable/generator.py) — greedy allocation
and at-risk detection, against the real DB layer (SQLite test DB)."""
from datetime import date, timedelta
from app.models import Task, StudySession
from app.timetable.generator import generate_timetable, get_timetable_by_day
from app.timetable.routes import _fill_display_window, DISPLAY_WINDOW_DAYS, MAX_DISPLAY_DAYS

TODAY = date(2026, 9, 23)


def test_generate_timetable_allocates_within_daily_cap(client, registered_user, module, db):
    registered_user.daily_study_hours = 2.0
    task = Task(module_id=module.id, title="Big task", due_date=TODAY + timedelta(days=10),
                estimated_hours=6, priority="high")
    db.session.add(task)
    db.session.commit()

    result = generate_timetable(registered_user, today=TODAY)

    sessions = StudySession.query.filter_by(user_id=registered_user.id).order_by(
        StudySession.scheduled_date
    ).all()
    assert result["sessions_created"] == len(sessions)
    assert all(s.allocated_hours <= 2.0 + 1e-9 for s in sessions)
    assert sum(s.allocated_hours for s in sessions) == 6
    assert result["at_risk_tasks"] == []  # 6h at 2h/day fits comfortably in 10 days


def test_generate_timetable_flags_at_risk_task(client, registered_user, module, db):
    registered_user.daily_study_hours = 1.0
    # Due tomorrow but needs 5 hours — cannot fit before the deadline at 1h/day.
    task = Task(module_id=module.id, title="Urgent big task",
                due_date=TODAY + timedelta(days=1), estimated_hours=5, priority="high")
    db.session.add(task)
    db.session.commit()

    result = generate_timetable(registered_user, today=TODAY)

    assert len(result["at_risk_tasks"]) == 1
    assert result["at_risk_tasks"][0]["task"].id == task.id
    assert result["at_risk_tasks"][0]["hours_short"] > 0


def test_generate_timetable_excludes_completed_tasks(client, registered_user, module, db):
    done = Task(module_id=module.id, title="Done", due_date=TODAY + timedelta(days=5),
                estimated_hours=4, hours_completed=4, status="completed")
    db.session.add(done)
    db.session.commit()

    result = generate_timetable(registered_user, today=TODAY)
    assert result["sessions_created"] == 0


def test_generate_timetable_is_idempotent_wipes_previous_plan(client, registered_user, module, db):
    task = Task(module_id=module.id, title="Task", due_date=TODAY + timedelta(days=5),
                estimated_hours=3, priority="medium")
    db.session.add(task)
    db.session.commit()

    generate_timetable(registered_user, today=TODAY)
    first_count = StudySession.query.filter_by(user_id=registered_user.id).count()

    # Regenerating should replace, not duplicate, the plan.
    generate_timetable(registered_user, today=TODAY)
    second_count = StudySession.query.filter_by(user_id=registered_user.id).count()

    assert first_count == second_count


def test_get_timetable_by_day_groups_and_orders_sessions(client, registered_user, module, db):
    task = Task(module_id=module.id, title="Task", due_date=TODAY + timedelta(days=5),
                estimated_hours=4, priority="medium")
    db.session.add(task)
    db.session.commit()
    registered_user.daily_study_hours = 1.0
    generate_timetable(registered_user, today=TODAY)

    by_day = get_timetable_by_day(registered_user)
    dates = [entry["date"] for entry in by_day]
    assert dates == sorted(dates)
    assert all(len(entry["sessions"]) >= 1 for entry in by_day)


def test_fill_display_window_empty_input_stays_empty():
    assert _fill_display_window([], TODAY) == []


def test_fill_display_window_pads_sparse_days_to_a_full_week():
    # Only two scheduled days, both near the start of the window.
    sparse = [
        {"date": TODAY, "sessions": []},
        {"date": TODAY + timedelta(days=1), "sessions": []},
    ]
    filled = _fill_display_window(sparse, TODAY)

    assert len(filled) == DISPLAY_WINDOW_DAYS
    assert filled[0]["date"] == TODAY
    assert filled[0]["is_today"] is True
    assert filled[-1]["is_today"] is False
    # Every day in the window is present and in order, even ones with no sessions.
    assert [d["date"] for d in filled] == [TODAY + timedelta(days=i) for i in range(DISPLAY_WINDOW_DAYS)]


def test_fill_display_window_extends_past_a_week_for_late_sessions():
    late_date = TODAY + timedelta(days=15)
    sparse = [{"date": late_date, "sessions": []}]
    filled = _fill_display_window(sparse, TODAY)

    assert filled[-1]["date"] == late_date
    assert len(filled) == 16  # today .. late_date inclusive


def test_fill_display_window_caps_extremely_long_horizons():
    far_future = TODAY + timedelta(days=100)
    sparse = [{"date": far_future, "sessions": []}]
    filled = _fill_display_window(sparse, TODAY)

    assert len(filled) == MAX_DISPLAY_DAYS
    assert filled[-1]["date"] == TODAY + timedelta(days=MAX_DISPLAY_DAYS - 1)


def test_fill_display_window_computes_total_hours_per_day():
    class FakeSession:
        def __init__(self, hours):
            self.allocated_hours = hours

    sparse = [{"date": TODAY, "sessions": [FakeSession(1.5), FakeSession(2.0)]}]
    filled = _fill_display_window(sparse, TODAY)

    assert filled[0]["total_hours"] == 3.5


def test_regenerating_timetable_preserves_actually_studied_sessions(client, registered_user, module, db):
    """Regression test: generate_timetable used to wipe *every* StudySession
    row for the user, including ones recorded as actually-studied history
    (is_completed=True, created when a student logs hours — see
    tasks/routes.py). Regenerating the plan must only clear the old
    planned blocks, never that history."""
    task = Task(module_id=module.id, title="Task", due_date=TODAY + timedelta(days=10),
                estimated_hours=6, priority="high")
    db.session.add(task)
    db.session.commit()

    studied = StudySession(
        task_id=task.id, user_id=registered_user.id,
        scheduled_date=TODAY, allocated_hours=2.0, is_completed=True,
    )
    db.session.add(studied)
    db.session.commit()

    generate_timetable(registered_user, today=TODAY)

    remaining_studied = StudySession.query.filter_by(id=studied.id).first()
    assert remaining_studied is not None
    assert remaining_studied.is_completed is True

    # The timetable view itself should only ever show the planned blocks,
    # not this actually-studied history.
    days = get_timetable_by_day(registered_user)
    for day in days:
        assert all(not s.is_completed for s in day["sessions"])


def test_generate_timetable_interleaves_multiple_tasks_per_day(client, registered_user, module, db):
    """Regression coverage for the round-robin rewrite: when several tasks
    are pending and the daily cap is generous, a single day should show
    more than one task instead of one task draining the whole day before
    the next one gets a look-in."""
    registered_user.daily_study_hours = 6.0
    t1 = Task(module_id=module.id, title="Task A", due_date=TODAY + timedelta(days=10),
              estimated_hours=6, priority="high")
    t2 = Task(module_id=module.id, title="Task B", due_date=TODAY + timedelta(days=10),
              estimated_hours=6, priority="high")
    t3 = Task(module_id=module.id, title="Task C", due_date=TODAY + timedelta(days=10),
              estimated_hours=6, priority="high")
    db.session.add_all([t1, t2, t3])
    db.session.commit()

    generate_timetable(registered_user, today=TODAY)

    first_day_sessions = StudySession.query.filter_by(
        user_id=registered_user.id, scheduled_date=TODAY
    ).all()
    task_ids_today = {s.task_id for s in first_day_sessions}
    assert len(task_ids_today) == 3  # all three subjects show up on day one
    assert all(abs(s.allocated_hours - 2.0) < 1e-9 for s in first_day_sessions)  # 6h / 3 tasks


def test_generate_timetable_caps_tasks_per_day_and_rotates_in_the_next(client, registered_user, module, db):
    """With more pending tasks than MAX_TASKS_PER_DAY, only the top-ranked
    ones share a given day; once one finishes, the next-ranked pending
    task should rotate into the mix."""
    from app.timetable.generator import MAX_TASKS_PER_DAY

    registered_user.daily_study_hours = 3.0
    tasks = []
    for i in range(5):
        t = Task(module_id=module.id, title=f"Task {i}", due_date=TODAY + timedelta(days=10),
                  estimated_hours=1, priority="high", difficulty=5 - i)
        tasks.append(t)
    db.session.add_all(tasks)
    db.session.commit()

    generate_timetable(registered_user, today=TODAY)

    day_one = StudySession.query.filter_by(user_id=registered_user.id, scheduled_date=TODAY).all()
    assert len(day_one) <= MAX_TASKS_PER_DAY

    day_two = StudySession.query.filter_by(
        user_id=registered_user.id, scheduled_date=TODAY + timedelta(days=1)
    ).all()
    # The remaining two 1h tasks (not scheduled on day one, since only 3
    # of 5 fit) should roll into day two.
    assert len(day_two) >= 1


def test_regenerating_timetable_preserves_a_running_session(client, registered_user, module, db):
    """A live Start/Stop Session timer (started_at set, ended_at still
    null) must survive a timetable regenerate too, just like completed
    study history — the student is mid-way through recording it."""
    from datetime import datetime

    task = Task(module_id=module.id, title="Task", due_date=TODAY + timedelta(days=5),
                estimated_hours=3, priority="medium")
    db.session.add(task)
    db.session.commit()

    running = StudySession(
        task_id=task.id, user_id=registered_user.id,
        scheduled_date=TODAY, allocated_hours=0, is_completed=False,
        started_at=datetime.utcnow(),
    )
    db.session.add(running)
    db.session.commit()

    generate_timetable(registered_user, today=TODAY)

    still_there = StudySession.query.filter_by(id=running.id).first()
    assert still_there is not None
    assert still_there.is_active is True

    # And it must not show up in the planned timetable view either.
    days = get_timetable_by_day(registered_user)
    for day in days:
        assert all(not s.is_active for s in day["sessions"])
