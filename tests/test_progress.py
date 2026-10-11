"""Progress blueprint: analytics page (overall completion, per-module
progress, weekly study hours)."""
from app.extensions import db as _db


def test_progress_requires_login(client, db):
    resp = client.get("/progress/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


def test_progress_page_shows_module_breakdown(client, db, registered_user, module, task):
    resp = client.get("/progress/")
    assert resp.status_code == 200
    assert module.name.encode() in resp.data


def test_progress_page_reflects_logged_hours(client, db, registered_user, task):
    client.post(f"/tasks/{task.id}/log-hours", data={"hours": "2"}, follow_redirects=False)
    resp = client.get("/progress/")
    assert resp.status_code == 200
    assert b"2.0h" in resp.data or b"2h" in resp.data
