"""Ownership-security tests for app.ownership.

These are the regression tests the refactor in app/ownership.py needed:
one user must never be able to view, edit, or delete another user's
module, task, or note — every such attempt must 404 (not 403, so an
attacker can't even tell the resource exists), and must leave the data
unchanged. Covers all three consolidated helpers
(get_owned_module_or_404, get_owned_task_or_404, get_owned_note_or_404)
through every blueprint that uses them.
"""
from app.models import Module, Task, Note
from tests.conftest import login


def _login_as_other(client):
    login(client, email="other@example.com")


def test_non_owner_cannot_view_module_edit_form(client, registered_user, other_user, module):
    _login_as_other(client)
    resp = client.get(f"/modules/{module.id}/edit")
    assert resp.status_code == 404


def test_non_owner_cannot_edit_module(client, registered_user, other_user, module, db):
    _login_as_other(client)
    resp = client.post(f"/modules/{module.id}/edit", data={"name": "Hijacked"})
    assert resp.status_code == 404
    db.session.refresh(module)
    assert module.name == "Databases"


def test_non_owner_cannot_delete_module(client, registered_user, other_user, module, db):
    _login_as_other(client)
    resp = client.post(f"/modules/{module.id}/delete")
    assert resp.status_code == 404
    assert Module.query.get(module.id) is not None


def test_non_owner_cannot_list_tasks_of_others_module(client, registered_user, other_user, module):
    _login_as_other(client)
    resp = client.get(f"/tasks/module/{module.id}")
    assert resp.status_code == 404


def test_non_owner_cannot_view_task_edit_form(client, registered_user, other_user, task):
    _login_as_other(client)
    resp = client.get(f"/tasks/{task.id}/edit")
    assert resp.status_code == 404


def test_non_owner_cannot_delete_task(client, registered_user, other_user, task, db):
    _login_as_other(client)
    resp = client.post(f"/tasks/{task.id}/delete")
    assert resp.status_code == 404
    assert Task.query.get(task.id) is not None


def test_non_owner_cannot_complete_task(client, registered_user, other_user, task, db):
    _login_as_other(client)
    resp = client.post(f"/tasks/{task.id}/complete")
    assert resp.status_code == 404
    db.session.refresh(task)
    assert task.status == "not_started"


def test_non_owner_cannot_log_hours(client, registered_user, other_user, task, db):
    _login_as_other(client)
    resp = client.post(f"/tasks/{task.id}/log-hours", data={"hours": "5"})
    assert resp.status_code == 404
    db.session.refresh(task)
    assert task.hours_completed == 0


def test_non_owner_cannot_list_notes(client, registered_user, other_user, task):
    _login_as_other(client)
    resp = client.get(f"/notes/task/{task.id}")
    assert resp.status_code == 404


def test_non_owner_cannot_create_note(client, registered_user, other_user, task, db):
    _login_as_other(client)
    resp = client.post(f"/notes/task/{task.id}/new", data={"content": "sneaky note"})
    assert resp.status_code == 404
    assert Note.query.filter_by(task_id=task.id).count() == 0


def test_non_owner_cannot_delete_note(client, registered_user, other_user, task, db):
    note = Note(task_id=task.id, user_id=registered_user.id, content="mine")
    db.session.add(note)
    db.session.commit()

    _login_as_other(client)
    resp = client.post(f"/notes/{note.id}/delete")
    assert resp.status_code == 404
    assert Note.query.get(note.id) is not None


def test_owner_can_still_access_everything(client, registered_user, module, task, db):
    """Sanity check the flip side: the refactor must not have broken
    legitimate access for the actual owner."""
    assert client.get(f"/modules/{module.id}/edit").status_code == 200
    assert client.get(f"/tasks/module/{module.id}").status_code == 200
    assert client.get(f"/tasks/{task.id}/edit").status_code == 200
    assert client.get(f"/notes/task/{task.id}").status_code == 200


def test_nonexistent_resource_ids_404_for_owner_too(client, registered_user):
    assert client.get("/modules/999999/edit").status_code == 404
    assert client.get("/tasks/999999/edit").status_code == 404
    assert client.get("/notes/task/999999").status_code == 404
