"""Start/Stop Session timer: app/tasks/routes.py start_session/stop_session,
and the recalculation (task progress/status) that stopping triggers."""
from datetime import datetime, timedelta
from app.extensions import db as _db
from app.models import StudySession, Task


def test_start_session_creates_an_active_session(client, db, registered_user, task):
    resp = client.post(f"/tasks/{task.id}/start-session", follow_redirects=False)
    assert resp.status_code == 302

    sessions = StudySession.query.filter_by(task_id=task.id).all()
    assert len(sessions) == 1
    assert sessions[0].is_active is True
    assert sessions[0].started_at is not None
    assert sessions[0].ended_at is None


def test_cannot_start_a_second_session_while_one_is_running(client, db, registered_user, module):
    t1 = Task(module_id=module.id, title="Task 1", due_date=task_due(), estimated_hours=2)
    t2 = Task(module_id=module.id, title="Task 2", due_date=task_due(), estimated_hours=2)
    _db.session.add_all([t1, t2])
    _db.session.commit()

    client.post(f"/tasks/{t1.id}/start-session", follow_redirects=False)
    resp = client.post(f"/tasks/{t2.id}/start-session", follow_redirects=False)
    assert resp.status_code == 302

    active_sessions = StudySession.query.filter_by(user_id=registered_user.id).filter(
        StudySession.ended_at.is_(None)
    ).all()
    assert len(active_sessions) == 1
    assert active_sessions[0].task_id == t1.id


def test_stop_session_logs_elapsed_time_and_updates_task(client, db, registered_user, task):
    client.post(f"/tasks/{task.id}/start-session", follow_redirects=False)
    running = StudySession.query.filter_by(task_id=task.id).first()

    # Backdate the start so we control the elapsed time precisely.
    running.started_at = datetime.utcnow() - timedelta(hours=1, minutes=30)
    _db.session.commit()

    resp = client.post(f"/tasks/session/{running.id}/stop", follow_redirects=False)
    assert resp.status_code == 302

    stopped = StudySession.query.get(running.id)
    assert stopped.is_active is False
    assert stopped.is_completed is True
    assert abs(stopped.allocated_hours - 1.5) < 0.02

    refreshed_task = Task.query.get(task.id)
    assert abs(refreshed_task.hours_completed - 1.5) < 0.02
    assert refreshed_task.status == "in_progress"


def test_stop_session_marks_task_completed_when_hours_reached(client, db, registered_user, module):
    t = Task(module_id=module.id, title="Short task", due_date=task_due(), estimated_hours=1)
    _db.session.add(t)
    _db.session.commit()

    client.post(f"/tasks/{t.id}/start-session", follow_redirects=False)
    running = StudySession.query.filter_by(task_id=t.id).first()
    running.started_at = datetime.utcnow() - timedelta(hours=2)  # more than enough
    _db.session.commit()

    client.post(f"/tasks/session/{running.id}/stop", follow_redirects=False)

    refreshed = Task.query.get(t.id)
    assert refreshed.status == "completed"
    assert refreshed.hours_completed == refreshed.estimated_hours


def test_very_short_session_still_logs_a_minimum_amount(client, db, registered_user, task):
    client.post(f"/tasks/{task.id}/start-session", follow_redirects=False)
    running = StudySession.query.filter_by(task_id=task.id).first()

    resp = client.post(f"/tasks/session/{running.id}/stop", follow_redirects=False)
    assert resp.status_code == 302

    stopped = StudySession.query.get(running.id)
    assert stopped.allocated_hours > 0  # never logs 0h even if stopped almost instantly


def test_stop_session_blocked_for_non_owner(client, db, registered_user, other_user, task):
    client.post(f"/tasks/{task.id}/start-session", follow_redirects=False)
    running = StudySession.query.filter_by(task_id=task.id).first()

    client.post("/auth/logout")
    client.post(
        "/auth/login",
        data={"email": other_user.email, "password": "TestPass123!"},
        follow_redirects=False,
    )
    resp = client.post(f"/tasks/session/{running.id}/stop", follow_redirects=False)
    assert resp.status_code == 404

    untouched = StudySession.query.get(running.id)
    assert untouched.is_active is True


def test_mark_complete_stops_a_running_session_first(client, db, registered_user, module):
    t = Task(module_id=module.id, title="Task", due_date=task_due(), estimated_hours=3)
    _db.session.add(t)
    _db.session.commit()

    client.post(f"/tasks/{t.id}/start-session", follow_redirects=False)
    running = StudySession.query.filter_by(task_id=t.id).first()
    running.started_at = datetime.utcnow() - timedelta(hours=1)
    _db.session.commit()

    client.post(f"/tasks/{t.id}/complete", follow_redirects=False)

    refreshed = Task.query.get(t.id)
    assert refreshed.status == "completed"
    assert refreshed.hours_completed == refreshed.estimated_hours

    stopped = StudySession.query.get(running.id)
    assert stopped.is_active is False
    assert stopped.is_completed is True

    # A second session should cover the remaining 2h top-up.
    all_sessions = StudySession.query.filter_by(task_id=t.id, is_completed=True).all()
    assert len(all_sessions) == 2
    assert abs(sum(s.allocated_hours for s in all_sessions) - 3.0) < 0.02


def task_due():
    from datetime import date
    return date.today() + timedelta(days=7)
