"""Tasks blueprint: cross-module 'My Tasks' filters/search and the task
detail page."""
from datetime import date, timedelta
from app.extensions import db as _db
from app.models import Task


def _make_task(module, **overrides):
    defaults = dict(
        module_id=module.id,
        title="Some Task",
        due_date=date.today() + timedelta(days=5),
        priority="medium",
        difficulty=3,
        estimated_hours=4,
    )
    defaults.update(overrides)
    t = Task(**defaults)
    _db.session.add(t)
    _db.session.commit()
    return t


def test_list_all_shows_tasks_across_modules(client, db, registered_user, module):
    _make_task(module, title="Task A")
    resp = client.get("/tasks/")
    assert resp.status_code == 200
    assert b"Task A" in resp.data


def test_list_all_filter_overdue(client, db, registered_user, module):
    _make_task(module, title="Overdue Task", due_date=date.today() - timedelta(days=2))
    _make_task(module, title="Future Task", due_date=date.today() + timedelta(days=10))

    resp = client.get("/tasks/?filter=overdue")
    assert b"Overdue Task" in resp.data
    assert b"Future Task" not in resp.data


def test_list_all_filter_completed(client, db, registered_user, module):
    _make_task(module, title="Done Task", status="completed", hours_completed=4)
    _make_task(module, title="Pending Task")

    resp = client.get("/tasks/?filter=completed")
    assert b"Done Task" in resp.data
    assert b"Pending Task" not in resp.data


def test_list_all_search_by_title(client, db, registered_user, module):
    _make_task(module, title="Database Assignment")
    _make_task(module, title="Essay Draft")

    resp = client.get("/tasks/?q=database")
    assert b"Database Assignment" in resp.data
    assert b"Essay Draft" not in resp.data


def test_task_detail_shows_full_info(client, db, registered_user, task):
    resp = client.get(f"/tasks/{task.id}")
    assert resp.status_code == 200
    assert task.title.encode() in resp.data
    assert task.module.name.encode() in resp.data


def test_task_detail_blocked_for_non_owner(client, db, other_user, task):
    from tests.conftest import login as do_login
    client.post("/auth/logout")
    resp = client.post(
        "/auth/login",
        data={"email": other_user.email, "password": "TestPass123!"},
        follow_redirects=False,
    )
    resp = client.get(f"/tasks/{task.id}")
    assert resp.status_code == 404


def test_log_hours_creates_a_study_session_record(client, db, registered_user, task):
    from app.models import StudySession

    client.post(f"/tasks/{task.id}/log-hours", data={"hours": "2"}, follow_redirects=False)

    sessions = StudySession.query.filter_by(task_id=task.id, is_completed=True).all()
    assert len(sessions) == 1
    assert sessions[0].allocated_hours == 2


def test_mark_complete_logs_remaining_hours_as_a_session(client, db, registered_user, task):
    from app.models import StudySession

    client.post(f"/tasks/{task.id}/complete", follow_redirects=False)

    sessions = StudySession.query.filter_by(task_id=task.id, is_completed=True).all()
    assert len(sessions) == 1
    assert sessions[0].allocated_hours == task.estimated_hours
