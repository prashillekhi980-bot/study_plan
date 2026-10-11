"""Onboarding blueprint: first-time setup wizard."""
from app.models import Module, User
from tests.conftest import register, login


def test_new_user_is_redirected_to_setup_on_login(client, db):
    register(client)
    resp = login(client)
    assert resp.status_code == 302
    assert "/setup" in resp.headers["Location"]


def test_setup_wizard_creates_modules_and_sets_daily_hours(client, db):
    register(client)
    login(client)

    resp = client.post(
        "/setup/",
        data={
            "name": "Student",
            "daily_study_hours": "3.5",
            "module_name": ["Databases", "", "Web Dev"],
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]

    user = User.query.filter_by(email="student@example.com").first()
    assert user.daily_study_hours == 3.5
    names = {m.name for m in Module.query.filter_by(user_id=user.id).all()}
    assert names == {"Databases", "Web Dev"}


def test_setup_wizard_skips_cleanly_to_empty_dashboard(client, db):
    register(client)
    login(client)

    resp = client.post("/setup/skip", follow_redirects=False)
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]

    dash = client.get(resp.headers["Location"], follow_redirects=False)
    assert dash.status_code == 200


def test_user_with_a_module_skips_wizard_entirely(client, db, registered_user, module):
    resp = client.get("/setup/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]
