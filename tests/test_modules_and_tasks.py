"""Module/Task CRUD, and progress-tracking behaviour (hours, status)."""
from datetime import date
from app.models import Module, Task


def test_create_module(client, registered_user, db):
    resp = client.post("/modules/new", data={"name": "Algorithms", "description": "DSA"})
    assert resp.status_code == 302

    m = Module.query.filter_by(user_id=registered_user.id, name="Algorithms").first()
    assert m is not None
    assert m.description == "DSA"


def test_create_module_requires_name(client, registered_user, db):
    resp = client.post("/modules/new", data={"name": "", "description": "x"})
    assert resp.status_code == 302  # redirected back with a flash error
    assert Module.query.count() == 0


def test_edit_module(client, registered_user, module, db):
    resp = client.post(
        f"/modules/{module.id}/edit", data={"name": "Renamed", "description": "updated"}
    )
    assert resp.status_code == 302
    db.session.refresh(module)
    assert module.name == "Renamed"


def test_delete_module_cascades_to_tasks(client, registered_user, module, task, db):
    task_id = task.id
    resp = client.post(f"/modules/{module.id}/delete")
    assert resp.status_code == 302

    assert Module.query.get(module.id) is None
    assert Task.query.get(task_id) is None  # cascade delete


def test_create_task_under_module(client, registered_user, module, db):
    resp = client.post(
        f"/tasks/module/{module.id}/new",
        data={
            "title": "Revise indexes",
            "due_date": "2026-12-01",
            "priority": "medium",
            "difficulty": "2",
            "estimated_hours": "3",
        },
    )
    assert resp.status_code == 302
    t = Task.query.filter_by(module_id=module.id, title="Revise indexes").first()
    assert t is not None
    assert t.status == "not_started"


def test_create_task_rejects_invalid_due_date(client, registered_user, module, db):
    resp = client.post(
        f"/tasks/module/{module.id}/new",
        data={"title": "Bad task", "due_date": "not-a-date", "priority": "medium",
              "difficulty": "2", "estimated_hours": "3"},
    )
    assert resp.status_code == 302
    assert Task.query.filter_by(title="Bad task").count() == 0


def test_mark_complete_sets_full_hours(client, registered_user, task, db):
    resp = client.post(f"/tasks/{task.id}/complete")
    assert resp.status_code == 302
    db.session.refresh(task)
    assert task.status == "completed"
    assert task.hours_completed == task.estimated_hours


def test_log_hours_partial_sets_in_progress(client, registered_user, task, db):
    resp = client.post(f"/tasks/{task.id}/log-hours", data={"hours": "2"})
    assert resp.status_code == 302
    db.session.refresh(task)
    assert task.status == "in_progress"
    assert task.hours_completed == 2


def test_log_hours_caps_at_estimated_hours_and_completes(client, registered_user, task, db):
    resp = client.post(f"/tasks/{task.id}/log-hours", data={"hours": "999"})
    assert resp.status_code == 302
    db.session.refresh(task)
    assert task.hours_completed == task.estimated_hours
    assert task.status == "completed"


def test_module_progress_percent_weighted_by_hours(client, registered_user, module, db):
    due = date(2026, 12, 1)
    t1 = Task(module_id=module.id, title="Big", due_date=due,
              estimated_hours=8, hours_completed=4)
    t2 = Task(module_id=module.id, title="Small", due_date=due,
              estimated_hours=2, hours_completed=2)
    db.session.add_all([t1, t2])
    db.session.commit()

    # (4 + 2) completed out of (8 + 2) estimated = 60%
    assert module.progress_percent == 60
